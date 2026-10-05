# Databricks notebook source
# MAGIC %md
# MAGIC # 05 — Feature Engineering | Member 3
# MAGIC
# MAGIC ## 1. What I am doing
# MAGIC Create temporal, geographic and contextual features from the cleaned Chicago Crime dataset.
# MAGIC
# MAGIC ## 2. Why I am doing it
# MAGIC Prepare meaningful predictive features for machine learning while preventing information leakage.

# COMMAND ----------

df_clean = spark.table("workspace.default.chicago_crime_clean")

print("Rows:", df_clean.count())
print("Columns:", len(df_clean.columns))

display(df_clean.limit(10))

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Feature Review and Leakage Prevention
# MAGIC
# MAGIC Before creating new features, we remove identifiers, target-leaking fields,
# MAGIC and post-event information that should not be used as model predictors.
# MAGIC
# MAGIC The `unique_key` column is temporarily retained only as a record identifier
# MAGIC for validation and joining between project stages. It will not be used as
# MAGIC a machine-learning feature.

# COMMAND ----------

columns_to_remove = [
    "case_number",      # Record identifier
    "iucr",             # Directly related to crime classification
    "description",      # Reveals detailed crime type
    "fbi_code",         # Crime classification code
    "arrest",           # Post-event outcome
    "updated_on"        # Administrative update after incident
]

df_features = df_clean.drop(*columns_to_remove)

print("Original columns:", len(df_clean.columns))
print("Remaining columns:", len(df_features.columns))

print("\nRemaining columns:")
for column_name in df_features.columns:
    print(column_name)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. Review of Remaining Features
# MAGIC
# MAGIC The remaining variables are reviewed for missing values, number of distinct values,
# MAGIC possible redundancy, and suitability for machine learning.
# MAGIC
# MAGIC This step helps identify high-cardinality features and overlapping geographic variables
# MAGIC before feature engineering.

# COMMAND ----------

from pyspark.sql import functions as F
from functools import reduce
from pyspark.sql import DataFrame

review_columns = [
    "block",
    "location_description",
    "beat",
    "district",
    "ward",
    "community_area",
    "x_coordinate",
    "y_coordinate",
    "year",
    "latitude",
    "longitude",
    "location"
]

review_tables = []

for c in review_columns:
    temp = df_features.select(
        F.lit(c).alias("column"),
        F.approx_count_distinct(F.col(c)).alias("approx_distinct_values"),
        F.sum(F.col(c).isNull().cast("long")).alias("null_count")
    )
    review_tables.append(temp)

feature_review = reduce(DataFrame.unionByName, review_tables)

display(
    feature_review.orderBy(
        F.desc("approx_distinct_values")
    )
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5. Removal of Redundant and High-Cardinality Geographic Features
# MAGIC
# MAGIC Geographic variables were reviewed for cardinality and redundancy.
# MAGIC
# MAGIC - `block` is excluded because it contains a very large number of unique street/block values.
# MAGIC - `x_coordinate` and `y_coordinate` are excluded because latitude and longitude already represent spatial location.
# MAGIC - `location` is excluded because it largely duplicates coordinate information.
# MAGIC
# MAGIC Administrative geographic codes such as `beat`, `district`, `ward`, and
# MAGIC `community_area` are retained and will later be treated as categorical features.

# COMMAND ----------

# MAGIC %md
# MAGIC ## 6. Temporal Feature Engineering
# MAGIC
# MAGIC The incident timestamp is transformed into meaningful temporal features
# MAGIC that can capture patterns by hour, month, weekday, and weekend status.
# MAGIC
# MAGIC The existing `year` field is retained after verifying that it is consistent
# MAGIC with the year derived from the `date` column.

# COMMAND ----------

# Load cleaned table again
df_clean = spark.table("workspace.default.chicago_crime_clean")

# Step 1 removals
columns_to_remove = [
    "case_number",
    "iucr",
    "description",
    "fbi_code",
    "arrest",
    "updated_on"
]

df_features = df_clean.drop(*columns_to_remove)

# Step 3 geographic/redundant removals
geo_columns_to_remove = [
    "block",
    "x_coordinate",
    "y_coordinate",
    "location"
]

df_features = df_features.drop(*geo_columns_to_remove)

print("df_features recreated successfully")
print("Rows:", df_features.count())
print("Columns:", len(df_features.columns))

print("\nColumns:")
for c in df_features.columns:
    print(c)

# COMMAND ----------

from pyspark.sql import functions as F

year_mismatch_count = (
    df_features
    .filter(F.year("date") != F.col("year"))
    .count()
)

print("Year mismatches:", year_mismatch_count)

# COMMAND ----------

from pyspark.sql import functions as F

df_features = (
    df_features
    .withColumn("hour", F.hour("date"))
    .withColumn("month", F.month("date"))
    .withColumn(
        "day_of_week",
        F.pmod(F.dayofweek("date") + F.lit(5), F.lit(7))
    )
    .withColumn(
        "is_weekend",
        F.when(
            F.pmod(F.dayofweek("date") + F.lit(5), F.lit(7)).isin([5, 6]),
            1
        ).otherwise(0)
    )
)

print("Temporal features created successfully.")

# COMMAND ----------

display(
    df_features.select(
        "date",
        "year",
        "month",
        "day_of_week",
        "hour",
        "is_weekend"
    ).limit(20)
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 7. Geographic Feature Engineering
# MAGIC
# MAGIC Latitude and longitude are reviewed before creating a higher-level geographic feature.
# MAGIC
# MAGIC The engineered geographic zones will be analytical groupings for modelling
# MAGIC and will not be presented as official Chicago neighbourhood boundaries.

# COMMAND ----------

from pyspark.sql import functions as F

coordinate_summary = df_features.select(
    F.count("*").alias("total_rows"),

    F.sum(
        (F.col("latitude").isNull() | F.col("longitude").isNull()).cast("long")
    ).alias("missing_coordinates"),

    F.min("latitude").alias("min_latitude"),
    F.expr("percentile_approx(latitude, 0.25)").alias("q1_latitude"),
    F.expr("percentile_approx(latitude, 0.50)").alias("median_latitude"),
    F.expr("percentile_approx(latitude, 0.75)").alias("q3_latitude"),
    F.max("latitude").alias("max_latitude"),

    F.min("longitude").alias("min_longitude"),
    F.expr("percentile_approx(longitude, 0.25)").alias("q1_longitude"),
    F.expr("percentile_approx(longitude, 0.50)").alias("median_longitude"),
    F.expr("percentile_approx(longitude, 0.75)").alias("q3_longitude"),
    F.max("longitude").alias("max_longitude")
)

display(coordinate_summary)

# COMMAND ----------

# MAGIC %md
# MAGIC ### 7.1 Create Relative Geographic Area Groups
# MAGIC
# MAGIC A new `area_group` feature is created using the median latitude and longitude
# MAGIC of the observed incident coordinates.
# MAGIC
# MAGIC The groups represent relative geographic quadrants within this dataset:
# MAGIC
# MAGIC - North-West
# MAGIC - North-East
# MAGIC - South-West
# MAGIC - South-East
# MAGIC - Unknown
# MAGIC
# MAGIC These are analytical groupings created for feature engineering and are not
# MAGIC official Chicago neighbourhood or administrative boundaries.

# COMMAND ----------

from pyspark.sql import functions as F

median_latitude = 41.864611293
median_longitude = -87.66068353

df_features = (
    df_features
    .withColumn(
        "area_group",
        F.when(
            F.col("latitude").isNull() | F.col("longitude").isNull(),
            "Unknown"
        )
        .when(
            (F.col("latitude") >= median_latitude) &
            (F.col("longitude") < median_longitude),
            "North-West"
        )
        .when(
            (F.col("latitude") >= median_latitude) &
            (F.col("longitude") >= median_longitude),
            "North-East"
        )
        .when(
            (F.col("latitude") < median_latitude) &
            (F.col("longitude") < median_longitude),
            "South-West"
        )
        .otherwise("South-East")
    )
)

print("area_group created successfully.")

# COMMAND ----------

display(
    df_features
    .groupBy("area_group")
    .count()
    .orderBy(F.desc("count"))
)

# COMMAND ----------

display(
    df_features.select(
        "unique_key",
        "latitude",
        "longitude",
        "area_group"
    ).limit(20)
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 8. Feature Engineering Validation
# MAGIC
# MAGIC The engineered dataset is validated before it is saved for preprocessing.
# MAGIC
# MAGIC Checks include:
# MAGIC - Row-count preservation
# MAGIC - Unique incident identifiers
# MAGIC - Missing target values
# MAGIC - Temporal feature completeness
# MAGIC - Geographic area-group completeness

# COMMAND ----------

from pyspark.sql import functions as F

validation_summary = df_features.select(
    F.count("*").alias("total_rows"),

    F.countDistinct("unique_key").alias("unique_incidents"),

    F.sum(
        F.col("primary_type").isNull().cast("long")
    ).alias("missing_target"),

    F.sum(
        F.col("hour").isNull().cast("long")
    ).alias("missing_hour"),

    F.sum(
        F.col("month").isNull().cast("long")
    ).alias("missing_month"),

    F.sum(
        F.col("day_of_week").isNull().cast("long")
    ).alias("missing_day_of_week"),

    F.sum(
        F.col("is_weekend").isNull().cast("long")
    ).alias("missing_is_weekend"),

    F.sum(
        F.col("area_group").isNull().cast("long")
    ).alias("missing_area_group")
)

display(validation_summary)

# COMMAND ----------

print("Total feature-engineered columns:", len(df_features.columns))

for c in df_features.columns:
    print(c)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 9. Save Feature-Engineered Dataset
# MAGIC
# MAGIC The validated feature-engineered dataset is saved as a new Delta table.
# MAGIC
# MAGIC The cleaned source table remains unchanged.
# MAGIC
# MAGIC Note: `area_group` is currently an exploratory engineered feature. Its latitude
# MAGIC and longitude thresholds will be recalculated from training data during final
# MAGIC preprocessing to avoid using held-out data when deriving model features.

# COMMAND ----------

feature_table_name = "workspace.default.chicago_crime_features"

(
    df_features.write
    .mode("overwrite")
    .option("overwriteSchema", "true")
    .saveAsTable(feature_table_name)
)

print(f"Feature table saved successfully: {feature_table_name}")

# COMMAND ----------

df_saved = spark.table("workspace.default.chicago_crime_features")

print("Saved rows:", df_saved.count())
print("Saved columns:", len(df_saved.columns))

display(df_saved.limit(10))

# COMMAND ----------

