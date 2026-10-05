# Databricks notebook source
# MAGIC %md
# MAGIC # 02 - Data Understanding
# MAGIC
# MAGIC ## 1. What I am doing
# MAGIC
# MAGIC This notebook investigates the quality and structure of the raw Chicago Crime dataset before any cleaning or transformation is applied.
# MAGIC
# MAGIC The analysis focuses on:
# MAGIC
# MAGIC - Missing values and missing-value percentages
# MAGIC - Duplicate records and duplicate identifiers
# MAGIC - Unique values and cardinality of important categorical variables
# MAGIC - The target variable `primary_type`
# MAGIC - Descriptive statistics for numerical variables
# MAGIC - Potential invalid or unusual records
# MAGIC - Initial data-quality observations
# MAGIC
# MAGIC ## 2. Why I am doing it
# MAGIC
# MAGIC Data understanding is required before making cleaning decisions.
# MAGIC
# MAGIC The purpose is to identify genuine data-quality issues and use evidence to determine which cleaning rules should be applied in the next stage.
# MAGIC
# MAGIC The raw table `default.chicago_crime_raw` is used as the source so that the original data remains unchanged.

# COMMAND ----------

from pyspark.sql import functions as F

# Load the persistent raw table

df = spark.table("default.chicago_crime_raw")

print(f"Rows: {df.count():,}")
print(f"Columns: {len(df.columns)}")

# COMMAND ----------

# Calculate missing-value counts and percentages for every column

total_rows = df.count()

missing_summary = []

for column in df.columns:
    missing_count = df.filter(
        F.col(column).isNull()
    ).count()

    missing_percentage = (missing_count / total_rows) * 100

    missing_summary.append(
        (column, missing_count, missing_percentage)
    )

missing_df = spark.createDataFrame(
    missing_summary,
    ["column", "missing_count", "missing_percentage"]
)

display(
    missing_df.orderBy(
        F.desc("missing_count")
    )
)

# COMMAND ----------

# MAGIC %md
# MAGIC ### Missing-value observations
# MAGIC
# MAGIC The dataset contains 662,472 records.
# MAGIC
# MAGIC Missing values are concentrated in geographic and location-related fields.
# MAGIC
# MAGIC The largest number of missing values occurs in:
# MAGIC
# MAGIC - `x_coordinate`
# MAGIC - `y_coordinate`
# MAGIC - `latitude`
# MAGIC - `longitude`
# MAGIC - `location`
# MAGIC
# MAGIC Each of these fields has 4,435 missing records (0.6695%).
# MAGIC
# MAGIC `location_description` has 3,145 missing records (0.4747%).
# MAGIC
# MAGIC `community_area` has 932 missing records (0.1407%), while `ward` has 916 missing records (0.1383%).
# MAGIC
# MAGIC The target variable `primary_type` has no missing values. The identifier fields `unique_key` and `case_number` and the temporal field `date` also contain no missing values.
# MAGIC
# MAGIC No missing-value replacement is performed at this stage. The appropriate treatment will be determined during the data-cleaning stage based on the role of each variable and its modelling relevance.

# COMMAND ----------

# Check for completely duplicated records

total_records = df.count()
distinct_records = df.dropDuplicates().count()

duplicate_records = total_records - distinct_records

print(f"Total records: {total_records:,}")
print(f"Distinct records: {distinct_records:,}")
print(f"Potential duplicate records: {duplicate_records:,}")

# COMMAND ----------

# Check whether unique_key is actually unique

unique_key_count = df.select("unique_key").distinct().count()
total_records = df.count()

print(f"Total records: {total_records:,}")
print(f"Unique unique_key values: {unique_key_count:,}")
print(f"Duplicate unique_key records: {total_records - unique_key_count:,}")

# COMMAND ----------

# Check case_number uniqueness

case_number_count = df.select("case_number").distinct().count()

print(f"Total records: {total_records:,}")
print(f"Unique case_number values: {case_number_count:,}")
print(f"Repeated case_number records: {total_records - case_number_count:,}")

# COMMAND ----------

# MAGIC %md
# MAGIC ### Duplicate-record observations
# MAGIC
# MAGIC The dataset contains 662,472 records.
# MAGIC
# MAGIC A complete duplicate check found 662,472 distinct records, meaning there are no exact duplicate rows.
# MAGIC
# MAGIC The `unique_key` field contains 662,472 distinct values, matching the total number of records. Therefore, there are no duplicate `unique_key` values.
# MAGIC
# MAGIC The `case_number` field contains 662,399 distinct values, resulting in 73 records associated with repeated case numbers.
# MAGIC
# MAGIC The repeated `case_number` values are not treated as duplicate records at this stage because `unique_key` is unique for every record and no complete duplicate rows were identified. The repeated case numbers will be investigated further before any cleaning decision is made.

# COMMAND ----------

from pyspark.sql import functions as F

repeated_cases = (
    df.groupBy("case_number")
      .count()
      .filter(F.col("count") > 1)
      .orderBy(F.desc("count"))
)

display(repeated_cases)

# COMMAND ----------

repeated_case_numbers = [
    row["case_number"]
    for row in repeated_cases.collect()
]

display(
    df.filter(
        F.col("case_number").isin(repeated_case_numbers)
    ).orderBy("case_number", "date")
)

# COMMAND ----------

# MAGIC %md
# MAGIC ### Duplicate investigation conclusion
# MAGIC
# MAGIC The dataset contains no exact duplicate rows and no duplicate `unique_key` values.
# MAGIC
# MAGIC There are 73 records associated with repeated `case_number` values. Investigation of these records shows that repeated case numbers can correspond to multiple records with different `unique_key` values and, in many cases, different incident times.
# MAGIC
# MAGIC Therefore, `case_number` is not treated as the unique record identifier, and the 73 records are retained. No duplicate records are removed at this stage.
# MAGIC
# MAGIC The `unique_key` field is retained as the record-level identifier because it is unique across all 662,472 records.

# COMMAND ----------

# Cardinality of important categorical columns

categorical_columns = [
    "primary_type",
    "iucr",
    "description",
    "location_description",
    "fbi_code"
]

cardinality_results = []

for column in categorical_columns:
    distinct_count = df.select(column).distinct().count()

    cardinality_results.append(
        (column, distinct_count)
    )

cardinality_df = spark.createDataFrame(
    cardinality_results,
    ["column", "unique_values"]
)

display(cardinality_df.orderBy(F.desc("unique_values")))

# COMMAND ----------

display(
    df.groupBy("primary_type")
      .count()
      .orderBy(F.desc("count"))
)

# COMMAND ----------

# MAGIC %md
# MAGIC ### Categorical Cardinality Observations
# MAGIC
# MAGIC The categorical-variable analysis shows that the target variable `primary_type` contains 31 unique crime categories. Therefore, the project represents a 31-class multiclass classification problem.
# MAGIC
# MAGIC Among the other categorical variables:
# MAGIC
# MAGIC - `iucr` contains 358 unique values.
# MAGIC - `description` contains 336 unique values.
# MAGIC - `location_description` contains 137 unique values.
# MAGIC - `fbi_code` contains 26 unique values.
# MAGIC
# MAGIC The `iucr`, `description`, and `fbi_code` fields are crime classification/code-related variables and may contain information that directly identifies or strongly reveals `primary_type`. Therefore, their use as modelling predictors should be reviewed carefully during the feature-engineering and preprocessing stages.
# MAGIC
# MAGIC `location_description` has moderate cardinality and may provide useful contextual information about where incidents occur.
# MAGIC
# MAGIC No categorical values are removed or transformed during the data-understanding stage.

# COMMAND ----------

# MAGIC %md
# MAGIC ### Categorical Cardinality Observations
# MAGIC
# MAGIC The categorical-variable analysis shows that the target variable `primary_type` contains 31 unique crime categories. Therefore, the project represents a 31-class multiclass classification problem.
# MAGIC
# MAGIC Among the other categorical variables:
# MAGIC
# MAGIC - `iucr` contains 358 unique values.
# MAGIC - `description` contains 336 unique values.
# MAGIC - `location_description` contains 137 unique values.
# MAGIC - `fbi_code` contains 26 unique values.
# MAGIC
# MAGIC The `iucr`, `description`, and `fbi_code` fields are crime classification/code-related variables and may contain information that directly identifies or strongly reveals `primary_type`. Therefore, their use as modelling predictors should be reviewed carefully during the feature-engineering and preprocessing stages.
# MAGIC
# MAGIC `location_description` has moderate cardinality and may provide useful contextual information about where incidents occur.
# MAGIC
# MAGIC No categorical values are removed or transformed during the data-understanding stage.

# COMMAND ----------

numeric_columns = [
    "unique_key",
    "beat",
    "district",
    "ward",
    "community_area",
    "x_coordinate",
    "y_coordinate",
    "year",
    "latitude",
    "longitude"
]

display(
    df.select(numeric_columns).describe()
)

# COMMAND ----------

# MAGIC %md
# MAGIC ### Numerical Variable Observations
# MAGIC
# MAGIC Descriptive statistics were calculated for the main numerical variables.
# MAGIC
# MAGIC The `year` field ranges from 2024 to 2026, which is consistent with the selected extraction period. The 2026 records represent the available year-to-date data rather than a complete calendar year.
# MAGIC
# MAGIC The `district` values range from 1 to 61, while `ward` values range from 1 to 50 and `community_area` values range from 1 to 77.
# MAGIC
# MAGIC The geographic variables also have reasonable bounded ranges in the observed data. Latitude ranges from approximately 41.64 to 42.02 and longitude ranges from approximately -87.93 to -87.52.
# MAGIC
# MAGIC Missing values are present in `ward`, `community_area`, and the geographic variables, consistent with the missing-value analysis performed earlier.
# MAGIC
# MAGIC The descriptive statistics do not by themselves identify invalid records. Therefore, explicit range and validity checks will be performed before making cleaning decisions.

# COMMAND ----------

print("=== Range / validity checks ===")

checks = {
    "year outside 2024-2026": df.filter(
        (F.col("year") < 2024) | (F.col("year") > 2026)
    ).count(),

    "district outside 1-61": df.filter(
        (F.col("district") < 1) | (F.col("district") > 61)
    ).count(),

    "ward outside 1-50": df.filter(
        (F.col("ward") < 1) | (F.col("ward") > 50)
    ).count(),

    "community_area outside 1-77": df.filter(
        (F.col("community_area") < 1) | (F.col("community_area") > 77)
    ).count(),

    "latitude outside observed geographic bounds": df.filter(
        (F.col("latitude") < 41.0) | (F.col("latitude") > 43.0)
    ).count(),

    "longitude outside observed geographic bounds": df.filter(
        (F.col("longitude") < -89.0) | (F.col("longitude") > -87.0)
    ).count()
}

for check, count in checks.items():
    print(f"{check}: {count:,}")

# COMMAND ----------

# MAGIC %md
# MAGIC ### Range and Validity Check Observations
# MAGIC
# MAGIC Explicit validity checks were performed for the main numerical and geographic variables.
# MAGIC
# MAGIC The results showed:
# MAGIC
# MAGIC - No records with `year` outside 2024–2026.
# MAGIC - No records with `district` outside the observed range of 1–61.
# MAGIC - No records with `ward` outside the observed range of 1–50.
# MAGIC - No records with `community_area` outside the observed range of 1–77.
# MAGIC - No records with latitude outside the checked geographic range.
# MAGIC - No records with longitude outside the checked geographic range.
# MAGIC
# MAGIC Therefore, no obvious out-of-range values were identified in these variables during the data-understanding stage.
# MAGIC
# MAGIC Missing values remain present in several geographic and location-related fields and will be considered separately during data cleaning.

# COMMAND ----------

date_summary = df.select(
    F.min("date").alias("minimum_date"),
    F.max("date").alias("maximum_date")
)

display(date_summary)

# COMMAND ----------

print("Null dates:", df.filter(F.col("date").isNull()).count())

display(
    df.groupBy("year")
      .agg(
          F.min("date").alias("minimum_date"),
          F.max("date").alias("maximum_date"),
          F.count("*").alias("record_count")
      )
      .orderBy("year")
)

# COMMAND ----------

# MAGIC %md
# MAGIC ### Temporal Coverage Observations
# MAGIC
# MAGIC The `date` field contains no missing values.
# MAGIC
# MAGIC The overall dataset covers the period from 2024-01-01 to 2026-09-16.
# MAGIC
# MAGIC The yearly coverage is:
# MAGIC
# MAGIC - 2024: 259,631 records, covering the complete year from January 1 to December 31.
# MAGIC - 2025: 238,083 records, covering the complete year from January 1 to December 31.
# MAGIC - 2026: 164,758 records, covering January 1 to September 16 only.
# MAGIC
# MAGIC Therefore, 2026 represents year-to-date data rather than a complete calendar year. Comparisons between yearly record counts should take this difference in coverage into account.
# MAGIC
# MAGIC No invalid or missing dates were identified during the data-understanding stage.

# COMMAND ----------

# MAGIC %md
# MAGIC # Data Quality Summary
# MAGIC
# MAGIC The Chicago Crime dataset contains 662,472 records and 22 columns covering crime incidents from January 1, 2024 to September 16, 2026.
# MAGIC
# MAGIC ## Key observations
# MAGIC
# MAGIC ### Completeness
# MAGIC
# MAGIC Missing values are concentrated in geographic and location-related fields.
# MAGIC
# MAGIC - `x_coordinate`, `y_coordinate`, `latitude`, `longitude`, and `location` each have 4,435 missing values (0.6695%).
# MAGIC - `location_description` has 3,145 missing values (0.4747%).
# MAGIC - `community_area` has 932 missing values (0.1407%).
# MAGIC - `ward` has 916 missing values (0.1383%).
# MAGIC - `primary_type`, `date`, `unique_key`, and `case_number` contain no missing values.
# MAGIC
# MAGIC ### Duplicates
# MAGIC
# MAGIC No exact duplicate rows were identified.
# MAGIC
# MAGIC The `unique_key` field contains 662,472 unique values, matching the total number of records.
# MAGIC
# MAGIC There are 73 records associated with repeated `case_number` values. These records were retained because `case_number` is not unique at the row level and the records have distinct `unique_key` values. No duplicate records are removed based only on repeated case numbers.
# MAGIC
# MAGIC ### Categorical variables
# MAGIC
# MAGIC The target variable `primary_type` contains 31 unique crime categories.
# MAGIC
# MAGIC The other important categorical variables contain:
# MAGIC
# MAGIC - `iucr`: 358 unique values
# MAGIC - `description`: 336 unique values
# MAGIC - `location_description`: 137 unique values
# MAGIC - `fbi_code`: 26 unique values
# MAGIC
# MAGIC The crime-code and description fields require careful consideration during feature engineering because they may directly encode or reveal the target classification.
# MAGIC
# MAGIC ### Target distribution
# MAGIC
# MAGIC The target variable is strongly imbalanced.
# MAGIC
# MAGIC `THEFT` is the most frequent crime category with 151,279 records, while several categories contain fewer than 100 records.
# MAGIC
# MAGIC This imbalance should be considered during preprocessing, model training, and evaluation.
# MAGIC
# MAGIC ### Numerical and geographic variables
# MAGIC
# MAGIC The observed ranges of the main numerical variables did not reveal obvious out-of-range values.
# MAGIC
# MAGIC Explicit validity checks identified zero records outside the checked ranges for:
# MAGIC
# MAGIC - `year`
# MAGIC - `district`
# MAGIC - `ward`
# MAGIC - `community_area`
# MAGIC - latitude
# MAGIC - longitude
# MAGIC
# MAGIC ### Temporal coverage
# MAGIC
# MAGIC The dataset contains complete records for 2024 and 2025 and year-to-date records for 2026 through September 16.
# MAGIC
# MAGIC Therefore, 2026 should not be interpreted as a complete-year dataset.
# MAGIC
# MAGIC ## Overall conclusion
# MAGIC
# MAGIC The dataset is suitable for proceeding to the cleaning stage. The main data-quality considerations are missing geographic/location information, repeated case numbers that are not necessarily duplicate records, strong class imbalance in the target variable, and the partial-year coverage of 2026.
# MAGIC
# MAGIC No cleaning actions are performed in this notebook. The identified issues will be addressed or documented during the data-cleaning stage.

# COMMAND ----------

# MAGIC %md
# MAGIC # Conclusion
# MAGIC
# MAGIC The data-understanding stage identified the main structural, completeness, duplication, categorical, numerical, temporal, and target-distribution characteristics of the Chicago Crime dataset.
# MAGIC
# MAGIC The dataset contains 662,472 records across 22 columns. No exact duplicate records or duplicate `unique_key` values were identified. Missing values are primarily concentrated in geographic and location-related variables.
# MAGIC
# MAGIC The target `primary_type` contains 31 crime categories and is substantially imbalanced. The dataset covers complete years for 2024 and 2025 and year-to-date data for 2026 through September 16.
# MAGIC
# MAGIC These findings will guide the cleaning decisions in the next notebook, `03_Data_Cleaning`.