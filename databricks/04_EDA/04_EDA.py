# Databricks notebook source
# /// script
# [tool.databricks.environment]
# environment_version = "6"
# ///
# MAGIC %md
# MAGIC # 04 — Exploratory Data Analysis | Member 2
# MAGIC ## 1. What I am doing
# MAGIC Analyse reported crime categories, class imbalance, time, geography, location context,
# MAGIC missingness and unusual observations. Produce figures, tables and a written handover.
# MAGIC ## 2. Why I am doing it
# MAGIC Identify evidence that helps Members 3 and 4 choose preprocessing and evaluation strategies.
# MAGIC The target is `primary_type`, a multiclass incident category, not whether crime will occur.
# MAGIC ## Run instructions
# MAGIC Attach Databricks Python compute with access to Member 1's cleaned table and **Run all**.
# MAGIC Change the widgets if your catalog/schema differs. No source table is modified.
# MAGIC `output_dir` may be a writable `/Volumes/<catalog>/<schema>/<volume>/member2` path.
# MAGIC The default evidence Volume persists after compute stops. If you change it to `/tmp`,
# MAGIC download the ZIP before stopping compute because that location is temporary.
# MAGIC Keep `features_table` empty until Member 3 supplies a table with `unique_key` and
# MAGIC `city_zone` or `area_group`. The optional table must match the same incident population.
# MAGIC Set `session_timezone` to the timezone that reproduces Member 1's source wall-clock dates.
# MAGIC UTC is the default for naive source timestamps ingested without conversion; do not shift
# MAGIC to America/Chicago unless Member 1 confirms the stored timestamps represent actual UTC instants.
# MAGIC EDA uses the full cleaned extract descriptively. Agree a split before using findings to tune
# MAGIC models; do not repeatedly inspect held-out test labels during feature selection.

# COMMAND ----------

from pathlib import Path
from datetime import datetime, timezone
import html
import json
import re
import shutil
import tempfile
import uuid
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pyspark.sql import functions as F

for name, default in {
    "clean_table": "workspace.default.chicago_crime_clean",
    "features_table": "",
    "output_dir": "/Volumes/workspace/default/member2_eda_evidence",
    "session_timezone": "UTC",
}.items():
    dbutils.widgets.text(name, default)

CLEAN_TABLE = dbutils.widgets.get("clean_table").strip()
FEATURES_TABLE = dbutils.widgets.get("features_table").strip()
spark.conf.set("spark.sql.session.timeZone", dbutils.widgets.get("session_timezone"))
RUN_ID = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid.uuid4().hex[:8]
OUT = Path(dbutils.widgets.get("output_dir")) / RUN_ID
OUT.mkdir(parents=True, exist_ok=True)
plt.rcParams.update({"figure.dpi": 110, "savefig.dpi": 220, "font.size": 10})
NOTES, TABLES, FIGURES = [], {}, []

def note(title, observation, implication, signal):
    """Show and preserve the three required explanations beneath each important chart."""
    item = {"title": title, "observation": observation, "implication": implication, "signal": signal}
    NOTES.append(item)
    displayHTML("<h3>" + html.escape(title) + "</h3>" + "".join(
        "<p><b>" + label + ":</b> " + html.escape(str(value)) + "</p>"
        for label, value in [("What it shows", observation), ("Why it matters", implication), ("Pattern / limitation", signal)]
    ))

def table(name, frame):
    TABLES[name] = frame.copy()
    frame.to_csv(OUT / (name + ".csv"), index=False)
    display(frame)
    return frame

def savefig(name, fig):
    fig.tight_layout()
    for suffix in ("png", "svg"):
        fig.savefig(OUT / (name + "." + suffix), bbox_inches="tight")
    FIGURES.append(name)
    display(fig)
    plt.close(fig)

def bars(name, frame, label, value="count", title=None, top=None):
    view = frame.head(top) if top else frame
    fig, ax = plt.subplots(figsize=(10, max(4, len(view) * .25)))
    ax.barh(view[label].astype(str)[::-1], view[value][::-1], color="#236b8e")
    ax.set(title=title or name.replace("_", " "), xlabel=value.replace("_", " "))
    ax.grid(axis="x", alpha=.2)
    savefig(name, fig)

def heatmap(name, frame, row, column, value, title):
    pivot = frame.pivot(index=row, columns=column, values=value).fillna(0)
    fig, ax = plt.subplots(figsize=(12, max(4, len(pivot) * .4)))
    im = ax.imshow(pivot.to_numpy(dtype=float), aspect="auto", cmap="YlGnBu")
    ax.set_xticks(range(len(pivot.columns)), pivot.columns.astype(str), rotation=90)
    ax.set_yticks(range(len(pivot.index)), pivot.index.astype(str))
    ax.set_title(title)
    fig.colorbar(im, ax=ax, label=value.replace("_", " "))
    savefig(name, fig)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Code / analysis — input contract and coverage
# MAGIC Read only the cleaned table. Derive temporary time fields for EDA; Member 3 owns the
# MAGIC reusable modelling transformations. Missing coordinates stay missing, and their records
# MAGIC remain in all non-coordinate analyses. Counts below refer to reported records, not population risk.

# COMMAND ----------

if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*(\.[A-Za-z_][A-Za-z0-9_]*){1,2}", CLEAN_TABLE):
    raise ValueError("Use a plain schema.table or catalog.schema.table identifier.")
SOURCE_VERSION = int(spark.sql(f"DESCRIBE HISTORY {CLEAN_TABLE}").select("version").first()["version"])
df = spark.read.option("versionAsOf", SOURCE_VERSION).table(CLEAN_TABLE)
required = {"unique_key", "date", "primary_type", "district", "community_area", "ward",
            "beat", "latitude", "longitude", "location_description", "domestic"}
missing = sorted(required - set(df.columns))
if missing:
    raise ValueError(f"Clean table is missing required columns: {missing}")
if dict(df.dtypes)["date"] not in ("timestamp", "timestamp_ntz", "date"):
    raise TypeError("Member 1 must provide date as a date/timestamp, not a string.")
meta = df.agg(F.count("*").alias("rows"), F.min("date").alias("start"),
              F.max("date").alias("end"),
              F.sum(F.col("date").isNull().cast("long")).alias("null_dates"),
              F.sum((F.col("primary_type").isNull() | (F.trim("primary_type") == "")).cast("long")).alias("null_targets")).first().asDict()
N = meta["rows"]
if N == 0 or meta["null_dates"] or meta["null_targets"]:
    raise ValueError(f"Input needs Member 1 review before EDA: {meta}")
display(pd.DataFrame([meta]))
eda = (df.withColumn("eda_year", F.year("date"))
       .withColumn("eda_month", F.month("date"))
       .withColumn("eda_hour", F.hour("date"))
       .withColumn("eda_day", F.to_date("date"))
       .withColumn("eda_weekday", F.pmod(F.dayofweek("date") + F.lit(5), F.lit(7))))
START, END = pd.Timestamp(meta["start"]), pd.Timestamp(meta["end"])
calendar = pd.DataFrame({"day": pd.date_range(START.normalize(), END.normalize(), freq="D")})
calendar["eda_weekday"] = calendar.day.dt.dayofweek

# COMMAND ----------

# MAGIC %md
# MAGIC ### Target distribution and class imbalance
# MAGIC Use every class, including rare classes. The majority-class share is a descriptive constant-
# MAGIC predictor accuracy reference on this extract; it is not an independently evaluated model score.

# COMMAND ----------

classes = eda.groupBy("primary_type").count().toPandas().sort_values(["count", "primary_type"], ascending=[False, True]).reset_index(drop=True)
classes["share_pct"] = classes["count"] / N * 100
classes["cumulative_pct"] = classes.share_pct.cumsum()
table("class_distribution", classes)
bars("01_primary_type", classes, "primary_type", title="Reported incidents by Primary Type — all classes")
major, minor = classes.iloc[0], classes.iloc[-1]
imbalance = {"classes": len(classes), "largest_class": major.primary_type,
             "smallest_class": minor.primary_type, "largest_smallest_ratio": float(major["count"] / minor["count"]),
             "majority_share_pct": float(major.share_pct), "classes_below_100": int((classes["count"] < 100).sum()),
             "top_5_share_pct": float(classes.head(5).share_pct.sum())}
table("class_imbalance_summary", pd.DataFrame([imbalance]))
note("Class imbalance", f"{len(classes)} classes; {major.primary_type} has {major['count']:,} records ({major.share_pct:.2f}%). "
     f"{minor.primary_type} has {minor['count']:,}; largest/smallest ratio = {imbalance['largest_smallest_ratio']:.1f}. "
     f"{imbalance['classes_below_100']} classes have fewer than 100 records.",
     "Members 3/4: preserve rare-class support information; compare macro F1, macro precision/recall, weighted F1 and per-class recall. Fit any balancing on training data only.",
     "Class imbalance; accuracy can hide poor minority-class performance. Do not merge target classes merely to improve scores.")
TOP_TYPES = classes.head(5).primary_type.tolist()

# COMMAND ----------

# MAGIC %md
# MAGIC ### Temporal trends and incomplete-year comparisons
# MAGIC Yearly totals have different exposure when the extract starts/ends mid-year. The additional
# MAGIC matched-window chart uses the same month/day interval in every represented year and excludes
# MAGIC the last observed day conservatively. Month totals flag boundary months. Daily spike checks
# MAGIC include zero-record calendar days; a zero can also indicate a gap in ingestion.

# COMMAND ----------

yearly = eda.groupBy("eda_year").agg(F.count("*").alias("count"), F.min("date").alias("first_record"), F.max("date").alias("last_record")).toPandas().sort_values("eda_year")
yearly["calendar_boundary_coverage"] = [
    "Jan 1–Dec 31 endpoints" if pd.Timestamp(a).strftime("%m-%d") == "01-01" and pd.Timestamp(b).strftime("%m-%d") == "12-31" else "Partial calendar year"
    for a, b in zip(yearly.first_record, yearly.last_record)]
table("yearly_counts", yearly)
bars("02_yearly_counts", yearly, "eda_year", title="Year totals — inspect coverage before comparing")
note("Yearly coverage", f"Observed dates: {START} to {END}. Year totals: " + "; ".join(f"{r.eda_year}: {r.count:,}" for r in yearly.itertuples()),
     "Compare equal date windows before interpreting year-to-year change; retain a time-aware validation strategy.",
     "Unequal exposure; endpoint coverage does not establish that every report was captured.")

lower_md = max(pd.Timestamp(v).strftime("%m-%d") for v in yearly.first_record)
upper_md = min(pd.Timestamp(v).strftime("%m-%d") for v in yearly.last_record)
matched = (eda.filter((F.date_format("date", "MM-dd") >= lower_md) & (F.date_format("date", "MM-dd") < upper_md))
           .groupBy("eda_year").count().toPandas().sort_values("eda_year"))
if not matched.empty:
    table("matched_calendar_window", matched)
    bars("03_matched_years", matched, "eda_year", title=f"Matched year window: {lower_md} inclusive to {upper_md} exclusive")
    note("Comparable yearly window", f"Counts use {lower_md} ≤ month/day < {upper_md} in every year; the upper boundary day is excluded.",
         "Use these totals instead of full-year versus year-to-date totals. Leap years may add one exposure day.",
         "Temporal comparison; reporting delay and later revisions still affect comparability.")
else:
    note("Comparable yearly window", "No shared non-empty calendar window is available.", "Do not infer annual change from unequal windows.", "Insufficient comparable coverage.")

monthly = eda.groupBy(F.date_format("date", "yyyy-MM").alias("month")).count().toPandas()
month_axis = pd.DataFrame({"month": pd.period_range(START, END, freq="M").astype(str)})
monthly = month_axis.merge(monthly, on="month", how="left").fillna({"count": 0})
monthly["boundary_month"] = monthly.month.isin([START.strftime("%Y-%m"), END.strftime("%Y-%m")])
table("monthly_counts", monthly)
fig, ax = plt.subplots(figsize=(12, 5))
ax.plot(monthly.month, monthly["count"], marker="o", color="#236b8e")
ax.tick_params(axis="x", rotation=90)
ax.set(title="Monthly reported incidents — boundary months may be incomplete", ylabel="Records")
savefig("04_monthly_trend", fig)
peak_month = monthly.loc[monthly["count"].idxmax()]
note("Monthly trend", f"The highest observed monthly total is {peak_month.month}: {int(peak_month['count']):,} records.",
     "Member 3: assess month as a candidate feature using training/validation data; inspect boundary months separately.",
     "Possible seasonality or reporting changes; a short series does not establish a recurring seasonal effect.")

hourly = pd.DataFrame({"eda_hour": range(24)}).merge(eda.groupBy("eda_hour").count().toPandas(), how="left", on="eda_hour").fillna(0)
table("hourly_counts", hourly)
fig, ax = plt.subplots(figsize=(10, 4))
ax.bar(hourly.eda_hour, hourly["count"], color="#236b8e")
ax.set(xticks=range(24), xlabel="Recorded hour", ylabel="Records", title="Time of day")
savefig("05_hourly_counts", fig)
peak_hour = int(hourly.loc[hourly["count"].idxmax(), "eda_hour"])
note("Hour of day", f"The highest recorded-hour count occurs at {peak_hour:02d}:00.",
     "Evaluate hour (possibly cyclic encoding) on training/validation data and confirm timestamp semantics with Member 1.",
     "Temporal pattern; rounded/default incident times can create artificial peaks.")

week = pd.DataFrame({"eda_weekday": range(7)}).merge(eda.groupBy("eda_weekday").count().toPandas(), on="eda_weekday", how="left").fillna(0)
week = week.merge(calendar.groupby("eda_weekday").size().rename("observed_calendar_days"), on="eda_weekday", how="left")
week["records_per_calendar_day"] = week["count"] / week.observed_calendar_days
week["weekday"] = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
table("weekday_counts", week)
bars("06_weekday_counts", week, "weekday", title="Reported incidents by weekday")
note("Day of week", f"The largest weekday total is {week.loc[week['count'].idxmax(), 'weekday']}. CSV also includes records per calendar day of exposure.",
     "Member 3: evaluate weekday/weekend features; compare exposure-normalized counts when windows are short.",
     "Weekly pattern; first/last days may have incomplete hourly coverage.")

# COMMAND ----------

# MAGIC %md
# MAGIC ### Geographic counts and coordinate coverage
# MAGIC Administrative codes are categories, not continuous distances. Null codes remain an explicit
# MAGIC missing group. Coordinate bins are a visualization grid, not official City Zones. No incident
# MAGIC coordinates are collected to the driver; only aggregated bins are plotted.

# COMMAND ----------

geography = {}
for field in ("district", "community_area", "ward", "beat"):
    counts = (eda.groupBy(F.coalesce(F.col(field).cast("string"), F.lit("[MISSING]")).alias(field))
              .count().toPandas().sort_values(["count", field], ascending=[False, True]))
    geography[field] = table(field + "_counts", counts)
    bars("07_" + field, counts, field, title=f"Top {field.replace('_', ' ')} groups — recorded counts", top=20)
    lead = counts.iloc[0]
    note(field.replace("_", " ").title(), f"Largest observed group: {lead[field]} ({lead['count']:,} records). All groups are in the CSV; chart shows at most 20.",
         "Member 3: treat codes categorically, allow missing/unseen values, and inspect sparse categories before encoding.",
         "Geographic count pattern; without population/exposure denominators these are not crime rates or measures of individual risk.")

null_row = df.agg(*[F.sum(F.col(c).isNull().cast("long")).alias(c) for c in df.columns]).first().asDict()
nulls = pd.DataFrame([{"column": c, "missing_count": n, "missing_pct": n / N * 100} for c, n in null_row.items()]).sort_values("missing_count", ascending=False)
table("missing_values", nulls)
bars("08_missing_values", nulls, "column", "missing_pct", "Null values in the cleaned table (%)")
note("Missing values", f"The highest null share is {nulls.iloc[0]['column']}: {nulls.iloc[0].missing_pct:.3f}%.",
     "Retain missingness indicators where justified; learn any model imputation from training data only. Never invent coordinates.",
     "Missingness; this chart counts SQL nulls, with NaN/invalid coordinates checked separately below.")

lat, lon = F.col("latitude"), F.col("longitude")
coord_missing = lat.isNull() | lon.isNull() | F.isnan(lat) | F.isnan(lon)
coord_valid = (~coord_missing) & lat.between(-90, 90) & lon.between(-180, 180)
# Broad screening window used by Member 1; not an official Chicago boundary.
coord_screen = coord_valid & lat.between(41, 43) & lon.between(-89, -87)
eda = eda.withColumn("coordinate_status", F.when(coord_missing, "missing_or_nan")
                     .when(~coord_valid, "invalid_global_range")
                     .when(~coord_screen, "outside_broad_screen").otherwise("within_broad_screen"))
coord_summary = table("coordinate_coverage", eda.groupBy("coordinate_status").count().toPandas())
coord_by_class = eda.groupBy("primary_type", "coordinate_status").count().toPandas()
coord_by_class["within_class_pct"] = coord_by_class["count"] / coord_by_class.groupby("primary_type")["count"].transform("sum") * 100
table("coordinate_coverage_by_class", coord_by_class)
grid = (eda.filter(F.col("coordinate_status") == "within_broad_screen")
        .groupBy(F.floor(lat / .01).alias("lat_bin"), F.floor(lon / .01).alias("lon_bin"))
        .count().toPandas())
table("coordinate_grid", grid)
if not grid.empty:
    fig, ax = plt.subplots(figsize=(9, 8))
    points = ax.scatter((grid.lon_bin + .5) * .01, (grid.lat_bin + .5) * .01,
                        c=np.log1p(grid["count"]), s=22, marker="s", cmap="viridis")
    ax.set(xlabel="Longitude (bin centre)", ylabel="Latitude (bin centre)", title="Aggregated coordinate density — 0.01 degree grid")
    ax.set_aspect(1 / np.cos(np.deg2rad(41.88)))
    fig.colorbar(points, ax=ax, label="log(1 + reported records)")
    savefig("09_coordinate_density", fig)
mapped = int(grid["count"].sum()) if not grid.empty else 0
note("Coordinate coverage and spatial density", f"{mapped:,}/{N:,} records ({mapped/N*100:.2f}%) enter the grid; {N-mapped:,} are excluded only from that plot. See coverage by class for differential missingness.",
     "Members 3/4: assess whether coordinate missingness differs by class; keep these records for other analyses and modelling where feasible.",
     "Spatial/missingness pattern. Broad bounds are a screening rule, not a city polygon; density is not population-adjusted risk.")

# COMMAND ----------

# MAGIC %md
# MAGIC ### Location context and comparisons of major categories
# MAGIC Heatmaps show percentages within each feature group. The denominator includes all crime
# MAGIC categories, even though only the five most frequent are displayed, so rows may sum to less than 100%.

# COMMAND ----------

locations = (eda.groupBy(F.coalesce("location_description", F.lit("[MISSING]")).alias("location_description"))
             .count().toPandas().sort_values("count", ascending=False))
table("location_description_counts", locations)
bars("10_location_description", locations, "location_description", title="Top location descriptions", top=20)
note("Location context", f"{len(locations)} location groups including missing, led by {locations.iloc[0].location_description} ({locations.iloc[0]['count']:,} records).",
     "Evaluate location description with explicit missing/unseen handling; learn rare-category grouping on training data.",
     "Context pattern; location description differs from the leakage-prone crime description field.")

cross_summaries = []
for field in ("eda_hour", "eda_weekday", "eda_month", "district", "community_area", "location_description", "domestic"):
    group = F.coalesce(F.col(field).cast("string"), F.lit("[MISSING]"))
    cross = eda.groupBy(group.alias("group"), "primary_type").count().toPandas()
    totals = cross.groupby("group")["count"].sum().sort_values(ascending=False)
    cross["within_group_pct"] = cross["count"] / cross["group"].map(totals) * 100
    table("crime_type_by_" + field, cross)
    keep = totals.head(15).index if field in ("district", "community_area", "location_description") else totals.index
    view = cross[cross.primary_type.isin(TOP_TYPES) & cross["group"].isin(keep)].copy()
    if field.startswith("eda_"):
        view["group"] = view["group"].str.zfill(2)
    heatmap("11_type_by_" + field, view, "group", "primary_type", "within_group_pct", f"Major crime categories by {field} — within-group %")
    maximum = view.loc[view.within_group_pct.idxmax()]
    cross_summaries.append(f"{field}: {maximum.primary_type} reaches {maximum.within_group_pct:.1f}% in displayed group {maximum['group']}")
    note("Crime category by " + field, cross_summaries[-1] + ". Full count and percentage table is exported.",
         "Use differences as feature hypotheses, then verify incremental value on validation data. Check each group's support before interpreting percentages.",
         "Association does not establish causation or predictive value. Domestic must be available at the intended prediction time; no post-event fields should leak the answer.")

# COMMAND ----------

# MAGIC %md
# MAGIC ### Unusual daily totals and sparse groups
# MAGIC The 1.5×IQR rule is an exploratory flag, not a deletion rule. Include calendar zeroes and
# MAGIC distinguish boundary days. Investigate flagged dates with Member 1 before changing data.

# COMMAND ----------

daily = eda.groupBy("eda_day").count().toPandas()
daily["day"] = pd.to_datetime(daily.eda_day)
daily = calendar[["day"]].merge(daily[["day", "count"]], on="day", how="left").fillna({"count": 0})
q1, q3 = daily["count"].quantile([.25, .75])
iqr = q3 - q1
daily["flag_iqr"] = (daily["count"] < q1 - 1.5 * iqr) | (daily["count"] > q3 + 1.5 * iqr)
daily["boundary_day"] = daily.day.isin([START.normalize(), END.normalize()])
table("daily_counts_and_flags", daily)
table("unusual_daily_totals", daily[daily.flag_iqr | (daily["count"] == 0)])
fig, ax = plt.subplots(figsize=(12, 4))
ax.plot(daily.day, daily["count"], linewidth=.8)
flagged = daily[daily.flag_iqr]
ax.scatter(flagged.day, flagged["count"], color="#c84536", s=14, label="IQR flag")
ax.set(title="Daily reported totals and review flags", ylabel="Records")
ax.legend()
savefig("12_daily_review", fig)
sparse = pd.DataFrame([{"feature": f, "groups_below_100": int((t["count"] < 100).sum()), "total_groups": len(t)} for f, t in geography.items()])
table("sparse_geographic_groups", sparse)
note("Unusual observations", f"{len(flagged)} dates are flagged by the IQR rule; {int((daily['count']==0).sum())} calendar days have zero records. IQR = {iqr:.1f}.",
     "Investigate extract gaps, revisions, holidays or rounded timestamps; do not remove records solely because a count is unusual.",
     "Potential outliers; this pooled rule does not adjust for weekday, seasonality or long-term trend.")

# COMMAND ----------

# MAGIC %md
# MAGIC ### Optional Member 3 City Zone / Area Group validation
# MAGIC Supply `features_table` to enable this step. Join by the record identifier, never row order.
# MAGIC Require a one-to-one, complete match. Obtain Member 3's documented mapping and construction
# MAGIC rule before interpreting the group. This notebook does not invent geographic boundaries.

# COMMAND ----------

zone_status = "Pending Member 3: no features_table supplied."
if FEATURES_TABLE:
    features = spark.table(FEATURES_TABLE)
    zone_candidates = [c for c in features.columns if c.lower() in ("city_zone", "area_group")]
    if "unique_key" not in features.columns or not zone_candidates:
        raise ValueError("Feature table needs unique_key plus City_Zone or Area_Group (case-insensitive).")
    zone_col = zone_candidates[0]
    for label, source in [("clean", eda), ("features", features)]:
        if source.filter(F.col("unique_key").isNull()).limit(1).count() or source.groupBy("unique_key").count().filter("count > 1").limit(1).count():
            raise ValueError(f"{label} unique_key must be non-null and unique for the zone join.")
    if eda.join(features, "unique_key", "left_anti").limit(1).count() or features.join(eda, "unique_key", "left_anti").limit(1).count():
        raise ValueError("Feature table and cleaned table must contain the same incident IDs.")
    zone = eda.select("unique_key", "primary_type").join(features.select("unique_key", F.col(zone_col).alias("member3_zone")), "unique_key")
    z = zone.groupBy(F.coalesce(F.col("member3_zone").cast("string"), F.lit("[MISSING]")).alias("zone"), "primary_type").count().toPandas()
    z["within_zone_pct"] = z["count"] / z.groupby("zone")["count"].transform("sum") * 100
    table("crime_type_by_city_zone", z)
    ztotals = z.groupby("zone", as_index=False)["count"].sum().sort_values("count", ascending=False)
    table("city_zone_counts", ztotals)
    bars("13_city_zone", ztotals, "zone", title="Member 3 geographic group counts", top=25)
    note("City Zone counts", f"{len(ztotals)} groups including missing; chart displays at most 25.",
         "Check Member 3's mapping, missingness, and group support before accepting the feature.", "Engineered geography; count differences do not validate boundaries.")
    heatmap("14_type_by_city_zone", z[z.primary_type.isin(TOP_TYPES) & z.zone.isin(ztotals.head(25).zone)], "zone", "primary_type", "within_zone_pct", "Crime category mix by Member 3 geographic group")
    zone_status = f"Analysed {FEATURES_TABLE}.{zone_col}; {len(ztotals)} groups. Mapping rationale and model ablation remain for Member 3/4."
    note("City Zone category mix", zone_status, "Compare validation performance with and without the engineered feature; fit any clustering on training data only.", "EDA association alone does not prove added predictive value.")
else:
    displayHTML("<p>" + html.escape(zone_status) + " Rerun with the feature table when available.</p>")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. Findings / conclusion and report evidence
# MAGIC The following ten findings are generated from this run. The bundle includes every chart in
# MAGIC PNG and SVG, aggregate CSVs, chart interpretations, provenance, and a Member 3/4 handover.
# MAGIC Download the ZIP from the final link. Large row-level incident data are never exported.

# COMMAND ----------

findings = [
    f"Coverage: {N:,} cleaned incident records, {len(df.columns)} source columns, {START} through {END}. Partial periods need explicit exposure controls.",
    f"Class imbalance: {major.primary_type} represents {major.share_pct:.2f}% of records; {minor.primary_type} has {minor['count']:,}. Use macro/per-class metrics alongside accuracy.",
    f"Sparse targets: {imbalance['classes_below_100']} classes have fewer than 100 records; top five classes account for {imbalance['top_5_share_pct']:.2f}%. Preserve class support in evaluation.",
    f"Temporal coverage: matched comparisons use {lower_md} inclusive to {upper_md} exclusive. Avoid interpreting a partial year's lower total as a decline.",
    f"Monthly/hourly structure: peak observed month {peak_month.month}; peak recorded hour {peak_hour:02d}:00. Check partial months and default times before modelling.",
    f"Weekday structure: largest total on {week.loc[week['count'].idxmax(), 'weekday']}; weekday_counts.csv includes calendar-day-normalized exposure.",
    "Geographic structure: " + "; ".join(f"largest {f} group {t.iloc[0][f]} ({t.iloc[0]['count']:,})" for f, t in geography.items()) + ". Counts are not population-adjusted rates.",
    f"Coordinate coverage: {mapped:,} records ({mapped/N*100:.2f}%) plotted; {N-mapped:,} omitted from the coordinate plot only. Review class-specific missingness before imputation.",
    f"Context: leading location group {locations.iloc[0].location_description}. Category-mix tables cover time, geography, location and domestic status; verify associations on validation data.",
    f"Review flags: {len(flagged)} unusual daily totals, {int((daily['count']==0).sum())} zero-record days. Investigate rather than automatically delete. City Zone status: {zone_status}",
]
report = "# Member 2 — generated EDA findings\n\n" + "\n\n".join(f"{i}. {text}" for i, text in enumerate(findings, 1))
report += "\n\n## Handover to Member 3\n\nEvaluate temporary time features, categorical geographic codes, location context and missingness. Review sparse groups. Exclude IUCR, crime description and FBI code from ordinary predictors; review arrest, updated_on and any post-event information. Confirm Domestic is known at prediction time. Fit encoders, imputers and any geographic clustering on training data only. Document the City Zone mapping.\n"
report += "\n## Handover to Member 4\n\nAgree a time-aware train/validation/test protocol, retain support counts, and compare a training-majority baseline with models on the same evaluation population. Report accuracy, macro precision/recall/F1, weighted F1 and per-class results. Do not tune on the final test set. Use validation ablations to assess feature value.\n"
report += "\n## Limitations\n\nThese are associations in reported incidents, subject to reporting/enforcement patterns and extract coverage. They do not establish causality, future incident risk, or characteristics of individuals. No population denominators are available. City Zone EDA cannot establish model improvement.\n"
(OUT / "member2_findings_and_handover.md").write_text(report, encoding="utf-8")
interpretations = "# Chart interpretations\n\n" + "\n\n".join(f"## {n['title']}\n\nWhat it shows: {n['observation']}\n\nWhy it matters: {n['implication']}\n\nPattern / limitation: {n['signal']}" for n in NOTES)
(OUT / "chart_interpretations.md").write_text(interpretations, encoding="utf-8")
manifest = {"run_id": RUN_ID, "clean_table": CLEAN_TABLE, "source_delta_version": SOURCE_VERSION, "features_table": FEATURES_TABLE,
            "spark_version": spark.version, "session_timezone": spark.conf.get("spark.sql.session.timeZone"),
            "observed_metadata": meta, "class_imbalance": imbalance, "zone_status": zone_status,
            "figures": FIGURES, "tables": list(TABLES), "coordinate_grid_degrees": .01,
            "coordinate_screen": {"latitude": [41, 43], "longitude": [-89, -87]},
            "notes": "Source table is read only and pinned to the recorded Delta version."}
(OUT / "run_manifest.json").write_text(json.dumps(manifest, indent=2, default=str), encoding="utf-8")
displayHTML("<h2>Ten EDA findings</h2><ol>" + "".join("<li>" + html.escape(f) + "</li>" for f in findings) + "</ol>")
with tempfile.TemporaryDirectory() as archive_tmp:
    local_archive = shutil.make_archive(str(Path(archive_tmp) / RUN_ID), "zip", root_dir=OUT)
    archive = str(OUT) + ".zip"
    shutil.copyfile(local_archive, archive)
print(f"Evidence folder: {OUT}\nEvidence ZIP: {archive}")
from IPython.display import FileLink
display(FileLink(archive, result_html_prefix="Download evidence ZIP: "))
print("If the compute UI cannot serve this local link, set output_dir to a writable Unity Catalog Volume and download the ZIP using the Catalog file browser.")
dbutils.notebook.exit(json.dumps({"status": "SUCCESS", "evidence_directory": str(OUT),
                                 "archive": archive, "manifest": manifest, "findings": findings}, default=str))