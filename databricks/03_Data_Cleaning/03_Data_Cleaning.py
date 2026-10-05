# Databricks notebook source
# MAGIC %md
# MAGIC # 03_Data_Cleaning
# MAGIC
# MAGIC ## What I am doing
# MAGIC
# MAGIC In this notebook, I will clean the Chicago Crime dataset based on the data-quality issues identified during the data-understanding stage.
# MAGIC
# MAGIC The cleaning process will address:
# MAGIC - Missing values
# MAGIC - Duplicate records
# MAGIC - Data types
# MAGIC - Irrelevant identifier fields
# MAGIC - Other issues identified during data understanding
# MAGIC
# MAGIC The cleaned dataset will be saved as a separate table for use by the remaining project members.
# MAGIC
# MAGIC ## Why I am doing it
# MAGIC
# MAGIC Data cleaning is required to produce a consistent and reliable dataset for exploratory analysis, feature engineering, and machine-learning model development.
# MAGIC
# MAGIC All cleaning decisions will be documented before they are applied so that the remaining team members understand how the final dataset was produced.

# COMMAND ----------

from pyspark.sql import functions as F

df_raw = spark.table("default.chicago_crime_raw")

print(f"Raw rows: {df_raw.count():,}")
print(f"Raw columns: {len(df_raw.columns)}")

# COMMAND ----------

# MAGIC %md
# MAGIC # Cleaning Decisions
# MAGIC
# MAGIC The following cleaning rules are based on the data-quality findings from `02_Data_Understanding`.
# MAGIC
# MAGIC | Issue | Decision | Reason |
# MAGIC |---|---|---|
# MAGIC | Exact duplicate rows | Remove if identified | Exact duplicate records provide no additional information |
# MAGIC | Duplicate `unique_key` | Investigate; remove only if duplicates exist | `unique_key` is intended to identify individual records |
# MAGIC | Repeated `case_number` | Retain | Investigation showed that repeated case numbers can correspond to different records and `unique_key` values |
# MAGIC | Missing `primary_type` | No action required | No missing values were identified |
# MAGIC | Missing `date` | No action required | No missing dates were identified |
# MAGIC | Missing geographic coordinates | Retain as missing | Missing values represent unavailable location information; they should not be replaced with arbitrary coordinates |
# MAGIC | Missing `location_description` | Retain as missing | The field is not required to have a fabricated category when the original value is unavailable |
# MAGIC | Missing `ward` / `community_area` | Retain as missing | These are geographic attributes and missing values should not be replaced with unsupported values |
# MAGIC | Date field | Keep as timestamp | The existing timestamp representation is appropriate for temporal analysis |
# MAGIC | `unique_key` | Retain as identifier | It is unique across all records and useful for record identification |
# MAGIC | `case_number` | Retain | It may contain useful reference information even though it is not unique |
# MAGIC | Target `primary_type` | Retain | This is the target variable for the classification task |
# MAGIC | Crime-code fields | Retain in cleaned dataset but flag for modelling review | `iucr`, `description`, and `fbi_code` may directly encode the target and require careful treatment during feature engineering |

# COMMAND ----------

duplicate_unique_keys = (
    df_raw.groupBy("unique_key")
    .count()
    .filter(F.col("count") > 1)
)

print(
    f"Duplicate unique_key values: "
    f"{duplicate_unique_keys.count():,}"
)

# COMMAND ----------

distinct_count = df_raw.distinct().count()
total_count = df_raw.count()

print(f"Total records: {total_count:,}")
print(f"Distinct records: {distinct_count:,}")
print(f"Exact duplicate records: {total_count - distinct_count:,}")

# COMMAND ----------

df_clean = df_raw.dropDuplicates()

print(f"Rows after duplicate handling: {df_clean.count():,}")

# COMMAND ----------

df_clean = df_raw.dropDuplicates()

print(f"Rows after duplicate handling: {df_clean.count():,}")
print(f"Columns: {len(df_clean.columns)}")

# COMMAND ----------

df_clean.printSchema()

# COMMAND ----------

# MAGIC %md
# MAGIC ### Data-Type Cleaning Decision
# MAGIC
# MAGIC The existing schema was reviewed before applying any type conversions.
# MAGIC
# MAGIC The `date` and `updated_on` fields are already stored as timestamp values, which is appropriate for temporal analysis.
# MAGIC
# MAGIC The `arrest` and `domestic` fields are stored as boolean values, which is appropriate for binary attributes.
# MAGIC
# MAGIC Numeric administrative and geographic fields are stored using numeric data types.
# MAGIC
# MAGIC Therefore, no unnecessary data-type conversions are required at this stage.

# COMMAND ----------

missing_summary = []

for column in df_clean.columns:
    missing_count = df_clean.filter(F.col(column).isNull()).count()
    
    if missing_count > 0:
        missing_percentage = (missing_count / df_clean.count()) * 100
        missing_summary.append(
            (column, missing_count, missing_percentage)
        )

missing_df = spark.createDataFrame(
    missing_summary,
    ["column", "missing_count", "missing_percentage"]
)

display(
    missing_df.orderBy(F.desc("missing_count"))
)

# COMMAND ----------

# MAGIC %md
# MAGIC ### Missing-Value Cleaning Decision
# MAGIC
# MAGIC The missing-value analysis shows that missing values are concentrated in geographic and location-related attributes.
# MAGIC
# MAGIC The following fields contain missing values:
# MAGIC
# MAGIC - `x_coordinate`: 4,435 records
# MAGIC - `y_coordinate`: 4,435 records
# MAGIC - `latitude`: 4,435 records
# MAGIC - `longitude`: 4,435 records
# MAGIC - `location`: 4,435 records
# MAGIC - `location_description`: 3,145 records
# MAGIC - `community_area`: 932 records
# MAGIC - `ward`: 916 records
# MAGIC
# MAGIC These missing values are retained rather than replaced with arbitrary values.
# MAGIC
# MAGIC Geographic coordinates will not be replaced with mean, median, or fixed coordinates because doing so would introduce artificial spatial information into the dataset.
# MAGIC
# MAGIC Similarly, categorical location attributes such as `location_description` will not be assigned an artificial category at this stage.
# MAGIC
# MAGIC The target variable `primary_type` has no missing values, so no target records need to be removed because of missing target values.
# MAGIC
# MAGIC Therefore, no rows are removed due to missing geographic or location information.

# COMMAND ----------

target_missing = df_clean.filter(
    F.col("primary_type").isNull()
).count()

print(f"Missing target values: {target_missing:,}")

# COMMAND ----------

important_columns = [
    "unique_key",
    "case_number",
    "date",
    "primary_type"
]

for column in important_columns:
    null_count = df_clean.filter(
        F.col(column).isNull()
    ).count()

    print(f"{column}: {null_count:,} null values")

# COMMAND ----------

# MAGIC %md
# MAGIC ### Missing-Value Cleaning Conclusion
# MAGIC
# MAGIC The target variable `primary_type` and the main record-identification and temporal fields (`unique_key`, `case_number`, and `date`) contain no missing values.
# MAGIC
# MAGIC Missing values are limited to geographic and location-related fields.
# MAGIC
# MAGIC Because these missing values represent unavailable information rather than demonstrably invalid records, the corresponding rows are retained. No artificial values are introduced.
# MAGIC
# MAGIC This preserves the original information without creating potentially misleading geographic or categorical values.
# MAGIC
# MAGIC Any model-specific handling of missing predictor values can be performed during the preprocessing stage by Member 3, depending on the final feature set.

# COMMAND ----------

raw_count = df_raw.count()
clean_count = df_clean.count()

print("=== Cleaning Validation ===")
print(f"Raw record count:     {raw_count:,}")
print(f"Cleaned record count: {clean_count:,}")
print(f"Records removed:      {raw_count - clean_count:,}")
print(f"Raw columns:          {len(df_raw.columns)}")
print(f"Cleaned columns:      {len(df_clean.columns)}")

# COMMAND ----------

clean_table_name = "default.chicago_crime_clean"

df_clean.write.mode("overwrite").saveAsTable(clean_table_name)

print(f"Cleaned table saved successfully as: {clean_table_name}")

# COMMAND ----------

df_verify = spark.table("default.chicago_crime_clean")

print(f"Verified cleaned rows: {df_verify.count():,}")
print(f"Verified cleaned columns: {len(df_verify.columns)}")

# COMMAND ----------

# MAGIC %md
# MAGIC # Final Cleaning Summary
# MAGIC
# MAGIC The cleaned Chicago Crime dataset has been created from the raw dataset.
# MAGIC
# MAGIC ## Cleaning actions performed
# MAGIC
# MAGIC 1. Exact duplicate records were checked and none were found.
# MAGIC 2. Duplicate `unique_key` values were checked and none were found.
# MAGIC 3. Repeated `case_number` values were retained because investigation showed that a case number can be associated with multiple distinct records.
# MAGIC 4. Missing values in geographic and location-related fields were retained because they represent unavailable information and replacing them with arbitrary values could introduce false information.
# MAGIC 5. The target variable `primary_type` was checked and contains no missing values.
# MAGIC 6. The `date`, `updated_on`, boolean, numerical, and geographic fields were reviewed and their existing data types were found to be appropriate.
# MAGIC 7. No records were removed because of invalid ranges or missing target values.
# MAGIC
# MAGIC ## Final dataset
# MAGIC
# MAGIC - Records: 662,472
# MAGIC - Columns: 22
# MAGIC - Records removed: 0
# MAGIC - Target: `primary_type`
# MAGIC - Target classes: 31
# MAGIC - Coverage: January 1, 2024 to September 16, 2026
# MAGIC
# MAGIC The cleaned dataset is saved as:
# MAGIC
# MAGIC `default.chicago_crime_clean`
# MAGIC
# MAGIC The cleaned table is ready to be handed over to Members 2 and 3 for exploratory analysis and feature engineering/preprocessing.

# COMMAND ----------

df_final = spark.table("default.chicago_crime_clean")

print("=== FINAL MEMBER 1 DATASET ===")
print(f"Table: default.chicago_crime_clean")
print(f"Rows: {df_final.count():,}")
print(f"Columns: {len(df_final.columns)}")
print(f"Target column: primary_type")
print(f"Target classes: {df_final.select('primary_type').distinct().count()}")

# COMMAND ----------

# MAGIC %md
# MAGIC # Member 1 Handover Note
# MAGIC
# MAGIC ## Dataset to use
# MAGIC
# MAGIC Members 2 and 3 should use the cleaned table:
# MAGIC
# MAGIC `default.chicago_crime_clean`
# MAGIC
# MAGIC The cleaned dataset contains:
# MAGIC
# MAGIC - 662,472 records
# MAGIC - 22 columns
# MAGIC - Target variable: `primary_type`
# MAGIC - 31 target classes
# MAGIC
# MAGIC ## Dataset coverage
# MAGIC
# MAGIC The dataset covers:
# MAGIC
# MAGIC - 2024: complete year
# MAGIC - 2025: complete year
# MAGIC - 2026: January 1 to September 16 only
# MAGIC
# MAGIC Therefore, 2026 is year-to-date and should not be interpreted as a complete calendar year.
# MAGIC
# MAGIC ## Data-quality findings
# MAGIC
# MAGIC - No exact duplicate records were found.
# MAGIC - No duplicate `unique_key` values were found.
# MAGIC - 73 records are associated with repeated `case_number` values, but these were retained because `case_number` is not a unique row identifier.
# MAGIC - `primary_type`, `date`, `unique_key`, and `case_number` contain no missing values.
# MAGIC - Missing values are concentrated in geographic and location-related fields.
# MAGIC - No obvious out-of-range values were identified in the checked numerical and geographic fields.
# MAGIC
# MAGIC ## Missing geographic information
# MAGIC
# MAGIC The following fields contain missing values:
# MAGIC
# MAGIC - `x_coordinate`: 4,435
# MAGIC - `y_coordinate`: 4,435
# MAGIC - `latitude`: 4,435
# MAGIC - `longitude`: 4,435
# MAGIC - `location`: 4,435
# MAGIC - `location_description`: 3,145
# MAGIC - `community_area`: 932
# MAGIC - `ward`: 916
# MAGIC
# MAGIC These missing values were retained rather than replaced with artificial values.
# MAGIC
# MAGIC ## Target distribution
# MAGIC
# MAGIC The target variable `primary_type` is highly imbalanced across its 31 classes.
# MAGIC
# MAGIC The most frequent classes include:
# MAGIC
# MAGIC - `THEFT`
# MAGIC - `BATTERY`
# MAGIC - `CRIMINAL DAMAGE`
# MAGIC - `ASSAULT`
# MAGIC - `MOTOR VEHICLE THEFT`
# MAGIC
# MAGIC Several classes contain very few records.
# MAGIC
# MAGIC This imbalance should be considered during feature engineering, model development, and evaluation.
# MAGIC
# MAGIC ## Potential target leakage
# MAGIC
# MAGIC The following fields require particular attention before being used as ordinary machine-learning predictors:
# MAGIC
# MAGIC - `iucr`
# MAGIC - `description`
# MAGIC - `fbi_code`
# MAGIC
# MAGIC These fields are crime classification/code-related variables and may directly encode or reveal the target `primary_type`.
# MAGIC
# MAGIC Members 2 and 3 should review these variables before including them in the final modelling feature set.
# MAGIC
# MAGIC ## Cleaning status
# MAGIC
# MAGIC No records were removed during cleaning because no exact duplicates, duplicate unique keys, missing target values, or obvious invalid records were identified.
# MAGIC
# MAGIC The cleaned dataset is ready for exploratory analysis and feature engineering.