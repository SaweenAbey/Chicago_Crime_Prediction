# Databricks notebook source
# MAGIC %md
# MAGIC # 01 - Data Ingestion
# MAGIC
# MAGIC ## 1. What I am doing
# MAGIC
# MAGIC This notebook performs the data ingestion stage of the Chicago Crime Type Prediction project.
# MAGIC
# MAGIC The Chicago Crime dataset was extracted from the Chicago Crime public dataset available through Google BigQuery and covers the years 2024, 2025, and 2026 year-to-date.
# MAGIC
# MAGIC The dataset is loaded into Databricks and stored as the persistent raw table:
# MAGIC
# MAGIC `default.chicago_crime_raw`
# MAGIC
# MAGIC The ingestion process includes:
# MAGIC - Loading the raw dataset
# MAGIC - Displaying sample records
# MAGIC - Inspecting the schema
# MAGIC - Recording the total number of rows and columns
# MAGIC - Verifying the raw table

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Why I am doing it
# MAGIC
# MAGIC A reproducible raw-data layer is required before data understanding and cleaning.
# MAGIC
# MAGIC Keeping the original dataset as a raw table allows the team to:
# MAGIC - preserve the original extracted data,
# MAGIC - perform data-quality investigation without modifying the source,
# MAGIC - reproduce the cleaning process,
# MAGIC - provide a consistent dataset for the later EDA, feature engineering, preprocessing, and modelling stages.
# MAGIC
# MAGIC The target variable for the project is `Primary Type`, which represents the crime classification to be predicted.

# COMMAND ----------

# Load the raw Chicago Crime dataset into a Spark DataFrame
import os

raw_csv_candidates = [
    "/FileStore/tables/chicago_crime_raw.csv",
    "dbfs:/FileStore/tables/chicago_crime_raw.csv",
    "data/raw/chicago_crime_raw.csv",
    "../data/raw/chicago_crime_raw.csv",
    "../../data/raw/chicago_crime_raw.csv",
    "/Workspace/Repos/Chicago_Crime_Prediction/data/raw/chicago_crime_raw.csv",
    "d:/Projects/Chicago_Crime_Prediction/data/raw/chicago_crime_raw.csv"
]

df_raw = None
loaded_from = None

# Check if table already exists in catalog
try:
    if spark.catalog.tableExists("default.chicago_crime_raw"):
        df_raw = spark.table("default.chicago_crime_raw")
        loaded_from = "default.chicago_crime_raw (Table)"
except Exception as e:
    pass

# If not found or empty, load from raw CSV file
if df_raw is None:
    for path in raw_csv_candidates:
        try:
            df_raw = spark.read.option("header", "true").option("inferSchema", "true").csv(path)
            # Verify non-empty
            if len(df_raw.columns) > 1:
                loaded_from = f"Raw CSV ({path})"
                # Persist to table for downstream notebooks
                try:
                    df_raw.write.mode("overwrite").format("delta").saveAsTable("default.chicago_crime_raw")
                    print(f"Persisted table 'default.chicago_crime_raw' from {path}")
                except Exception as save_err:
                    df_raw.createOrReplaceTempView("chicago_crime_raw")
                    print(f"Created temp view 'chicago_crime_raw': {save_err}")
                break
        except Exception:
            continue

if df_raw is None:
    raise FileNotFoundError(
        "Could not locate raw Chicago crime dataset. Please ensure 'data/raw/chicago_crime_raw.csv' or 'default.chicago_crime_raw' is accessible."
    )

print(f"Raw dataset loaded successfully from: {loaded_from}")


# COMMAND ----------

# Display the first 10 records

display(df_raw.limit(10))

# COMMAND ----------

# Display the Spark DataFrame schema

df_raw.printSchema()

# COMMAND ----------

# Count total number of records

row_count = df_raw.count()

print(f"Total rows: {row_count:,}")

# COMMAND ----------

# Count total number of columns

column_count = len(df_raw.columns)

print(f"Total columns: {column_count}")

# COMMAND ----------

# Display all column names

for i, column in enumerate(df_raw.columns, start=1):
    print(f"{i}. {column}")

# COMMAND ----------

# Verify that the target variable exists

target_column = "primary_type"

if target_column in df_raw.columns:
    print(f"Target column '{target_column}' found.")
else:
    print(f"WARNING: Target column '{target_column}' was not found.")

# COMMAND ----------

from pyspark.sql import functions as F

display(
    df_raw.groupBy("year")
          .count()
          .orderBy("year")
)

# COMMAND ----------

# Verify that the persistent raw table exists

spark.sql("""
    SHOW TABLES IN default
""").show(truncate=False)

# COMMAND ----------

print("=" * 60)
print("CHICAGO CRIME DATA - INGESTION SUMMARY")
print("=" * 60)

print(f"Source table       : default.chicago_crime_raw")
print(f"Total rows         : {row_count:,}")
print(f"Total columns      : {column_count}")
print(f"Target variable    : {target_column}")
print(f"Dataset period     : 2024, 2025, and 2026 year-to-date")
print("=" * 60)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. Findings / Conclusion
# MAGIC
# MAGIC The Chicago Crime dataset was successfully ingested into Databricks and is available as the persistent raw table `default.chicago_crime_raw`.
# MAGIC
# MAGIC The ingestion validation confirmed:
# MAGIC
# MAGIC - The dataset contains 22 columns.
# MAGIC - The target variable is `primary_type`.
# MAGIC - The `date` and `updated_on` fields are stored as timestamps.
# MAGIC - `latitude` and `longitude` are stored as numeric values.
# MAGIC - `arrest` and `domestic` are stored as Boolean values.
# MAGIC - The raw table is accessible through Spark.
# MAGIC - The extracted dataset covers 2024, 2025, and 2026 year-to-date.
# MAGIC
# MAGIC ### Dataset coverage
# MAGIC
# MAGIC The extracted dataset contains 662,472 records across the selected period:
# MAGIC
# MAGIC - 2024: 259,631 records
# MAGIC - 2025: 238,083 records
# MAGIC - 2026 year-to-date: 164,758 records
# MAGIC
# MAGIC The 2026 records represent year-to-date data rather than a complete calendar year. Therefore, comparisons involving 2026 should account for the incomplete observation period.
# MAGIC
# MAGIC No data-cleaning transformations were applied during ingestion. The raw table is preserved as the starting point for the data-understanding and cleaning stages.