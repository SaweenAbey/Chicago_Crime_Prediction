# Chart interpretations

## Class imbalance

What it shows: 31 classes; THEFT has 151,279 records (22.84%). NON-CRIMINAL has 9; largest/smallest ratio = 16808.8. 5 classes have fewer than 100 records.

Why it matters: Members 3/4: preserve rare-class support information; compare macro F1, macro precision/recall, weighted F1 and per-class recall. Fit any balancing on training data only.

Pattern / limitation: Class imbalance; accuracy can hide poor minority-class performance. Do not merge target classes merely to improve scores.

## Yearly coverage

What it shows: Observed dates: 2024-01-01 05:30:00 to 2026-09-16 05:30:00. Year totals: 2024: 259,631; 2025: 238,083; 2026: 164,758

Why it matters: Compare equal date windows before interpreting year-to-year change; retain a time-aware validation strategy.

Pattern / limitation: Unequal exposure; endpoint coverage does not establish that every report was captured.

## Comparable yearly window

What it shows: Counts use 01-01 ≤ month/day < 09-16 in every year; the upper boundary day is excluded.

Why it matters: Use these totals instead of full-year versus year-to-date totals. Leap years may add one exposure day.

Pattern / limitation: Temporal comparison; reporting delay and later revisions still affect comparability.

## Monthly trend

What it shows: The highest observed monthly total is 2024-07: 24,149 records.

Why it matters: Member 3: assess month as a candidate feature using training/validation data; inspect boundary months separately.

Pattern / limitation: Possible seasonality or reporting changes; a short series does not establish a recurring seasonal effect.

## Hour of day

What it shows: The highest recorded-hour count occurs at 00:00.

Why it matters: Evaluate hour (possibly cyclic encoding) on training/validation data and confirm timestamp semantics with Member 1.

Pattern / limitation: Temporal pattern; rounded/default incident times can create artificial peaks.

## Day of week

What it shows: The largest weekday total is Friday. CSV also includes records per calendar day of exposure.

Why it matters: Member 3: evaluate weekday/weekend features; compare exposure-normalized counts when windows are short.

Pattern / limitation: Weekly pattern; first/last days may have incomplete hourly coverage.

## District

What it shows: Largest observed group: 8 (42,717 records). All groups are in the CSV; chart shows at most 20.

Why it matters: Member 3: treat codes categorically, allow missing/unseen values, and inspect sparse categories before encoding.

Pattern / limitation: Geographic count pattern; without population/exposure denominators these are not crime rates or measures of individual risk.

## Community Area

What it shows: Largest observed group: 25 (33,124 records). All groups are in the CSV; chart shows at most 20.

Why it matters: Member 3: treat codes categorically, allow missing/unseen values, and inspect sparse categories before encoding.

Pattern / limitation: Geographic count pattern; without population/exposure denominators these are not crime rates or measures of individual risk.

## Ward

What it shows: Largest observed group: 27 (31,090 records). All groups are in the CSV; chart shows at most 20.

Why it matters: Member 3: treat codes categorically, allow missing/unseen values, and inspect sparse categories before encoding.

Pattern / limitation: Geographic count pattern; without population/exposure denominators these are not crime rates or measures of individual risk.

## Beat

What it shows: Largest observed group: 1834 (8,050 records). All groups are in the CSV; chart shows at most 20.

Why it matters: Member 3: treat codes categorically, allow missing/unseen values, and inspect sparse categories before encoding.

Pattern / limitation: Geographic count pattern; without population/exposure denominators these are not crime rates or measures of individual risk.

## Missing values

What it shows: The highest null share is longitude: 0.669%.

Why it matters: Retain missingness indicators where justified; learn any model imputation from training data only. Never invent coordinates.

Pattern / limitation: Missingness; this chart counts SQL nulls, with NaN/invalid coordinates checked separately below.

## Coordinate coverage and spatial density

What it shows: 658,037/662,472 records (99.33%) enter the grid; 4,435 are excluded only from that plot. See coverage by class for differential missingness.

Why it matters: Members 3/4: assess whether coordinate missingness differs by class; keep these records for other analyses and modelling where feasible.

Pattern / limitation: Spatial/missingness pattern. Broad bounds are a screening rule, not a city polygon; density is not population-adjusted risk.

## Location context

What it shows: 137 location groups including missing, led by STREET (178,168 records).

Why it matters: Evaluate location description with explicit missing/unseen handling; learn rare-category grouping on training data.

Pattern / limitation: Context pattern; location description differs from the leakage-prone crime description field.

## Crime category by eda_hour

What it shows: eda_hour: THEFT reaches 29.9% in displayed group 14. Full count and percentage table is exported.

Why it matters: Use differences as feature hypotheses, then verify incremental value on validation data. Check each group's support before interpreting percentages.

Pattern / limitation: Association does not establish causation or predictive value. Domestic must be available at the intended prediction time; no post-event fields should leak the answer.

## Crime category by eda_weekday

What it shows: eda_weekday: THEFT reaches 23.7% in displayed group 03. Full count and percentage table is exported.

Why it matters: Use differences as feature hypotheses, then verify incremental value on validation data. Check each group's support before interpreting percentages.

Pattern / limitation: Association does not establish causation or predictive value. Domestic must be available at the intended prediction time; no post-event fields should leak the answer.

## Crime category by eda_month

What it shows: eda_month: THEFT reaches 23.8% in displayed group 12. Full count and percentage table is exported.

Why it matters: Use differences as feature hypotheses, then verify incremental value on validation data. Check each group's support before interpreting percentages.

Pattern / limitation: Association does not establish causation or predictive value. Domestic must be available at the intended prediction time; no post-event fields should leak the answer.

## Crime category by district

What it shows: district: THEFT reaches 40.4% in displayed group 18. Full count and percentage table is exported.

Why it matters: Use differences as feature hypotheses, then verify incremental value on validation data. Check each group's support before interpreting percentages.

Pattern / limitation: Association does not establish causation or predictive value. Domestic must be available at the intended prediction time; no post-event fields should leak the answer.

## Crime category by community_area

What it shows: community_area: THEFT reaches 40.4% in displayed group 8. Full count and percentage table is exported.

Why it matters: Use differences as feature hypotheses, then verify incremental value on validation data. Check each group's support before interpreting percentages.

Pattern / limitation: Association does not establish causation or predictive value. Domestic must be available at the intended prediction time; no post-event fields should leak the answer.

## Crime category by location_description

What it shows: location_description: THEFT reaches 83.0% in displayed group DEPARTMENT STORE. Full count and percentage table is exported.

Why it matters: Use differences as feature hypotheses, then verify incremental value on validation data. Check each group's support before interpreting percentages.

Pattern / limitation: Association does not establish causation or predictive value. Domestic must be available at the intended prediction time; no post-event fields should leak the answer.

## Crime category by domestic

What it shows: domestic: BATTERY reaches 50.8% in displayed group true. Full count and percentage table is exported.

Why it matters: Use differences as feature hypotheses, then verify incremental value on validation data. Check each group's support before interpreting percentages.

Pattern / limitation: Association does not establish causation or predictive value. Domestic must be available at the intended prediction time; no post-event fields should leak the answer.

## Unusual observations

What it shows: 19 dates are flagged by the IQR rule; 0 calendar days have zero records. IQR = 96.0.

Why it matters: Investigate extract gaps, revisions, holidays or rounded timestamps; do not remove records solely because a count is unusual.

Pattern / limitation: Potential outliers; this pooled rule does not adjust for weekday, seasonality or long-term trend.