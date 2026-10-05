# Databricks notebook source
# MAGIC %md
# MAGIC # 06 — Data Preprocessing | Member 3
# MAGIC
# MAGIC ## 1. What I am doing
# MAGIC Prepare the feature-engineered Chicago Crime dataset for machine-learning model development.
# MAGIC
# MAGIC ## 2. Why I am doing it
# MAGIC Handle missing values, define categorical and numerical variables, prevent data leakage,
# MAGIC prepare train/validation/test datasets, and build a reproducible preprocessing strategy.
# MAGIC
# MAGIC ## Important
# MAGIC Any transformation that learns information from the data will be fitted using training data only.

# COMMAND ----------

df = spark.table("workspace.default.chicago_crime_features")

print("Rows:", df.count())
print("Columns:", len(df.columns))

display(df.limit(10))

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Data Coverage Before Train / Validation / Test Split
# MAGIC
# MAGIC Because the dataset contains incidents across multiple years,
# MAGIC the temporal coverage is reviewed before choosing the final split strategy.
# MAGIC
# MAGIC A time-aware split can better represent prediction on later incidents
# MAGIC than randomly mixing older and newer incidents.

# COMMAND ----------

from pyspark.sql import functions as F

date_coverage = df.select(
    F.min("date").alias("start_date"),
    F.max("date").alias("end_date"),
    F.count("*").alias("total_rows")
)

display(date_coverage)

# COMMAND ----------

display(
    df.groupBy("year")
      .count()
      .orderBy("year")
)

# COMMAND ----------

date_coverage = df.select(
    F.min("date").alias("start_date"),
    F.max("date").alias("end_date"),
    F.count("*").alias("total_rows")
)

display(date_coverage)

# COMMAND ----------

display(
    df.groupBy("year")
      .count()
      .orderBy("year")
) 

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. Time-Aware Train / Validation / Test Split
# MAGIC
# MAGIC The dataset is split chronologically to simulate prediction on future incidents.
# MAGIC
# MAGIC - Training: 2024-01-01 to 2025-06-30
# MAGIC - Validation: 2025-07-01 to 2025-12-31
# MAGIC - Test: 2026-01-01 to 2026-09-16
# MAGIC
# MAGIC This prevents future records from influencing earlier model training and provides a more realistic evaluation than randomly mixing incidents from different time periods.

# COMMAND ----------

from pyspark.sql import functions as F

train_df = df.filter(
    F.col("date") < F.to_timestamp(F.lit("2025-07-01 00:00:00"))
)

validation_df = df.filter(
    (F.col("date") >= F.to_timestamp(F.lit("2025-07-01 00:00:00"))) &
    (F.col("date") < F.to_timestamp(F.lit("2026-01-01 00:00:00")))
)

test_df = df.filter(
    F.col("date") >= F.to_timestamp(F.lit("2026-01-01 00:00:00"))
)

print("Training rows:", train_df.count())
print("Validation rows:", validation_df.count())
print("Test rows:", test_df.count())
print("Total:", train_df.count() + validation_df.count() + test_df.count())

# COMMAND ----------

for name, dataset in [
    ("Train", train_df),
    ("Validation", validation_df),
    ("Test", test_df)
]:
    summary = dataset.select(
        F.min("date").alias("start"),
        F.max("date").alias("end"),
        F.count("*").alias("rows")
    )

    print(name)
    display(summary)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5. Rebuild Area Group Using Training Data Only
# MAGIC
# MAGIC The exploratory `area_group` created during feature engineering used medians
# MAGIC calculated from the complete dataset.
# MAGIC
# MAGIC For machine-learning evaluation, the latitude and longitude thresholds are
# MAGIC recalculated using the training dataset only.
# MAGIC
# MAGIC The same training-derived thresholds are then applied unchanged to the
# MAGIC validation and test datasets to prevent information leakage.

# COMMAND ----------

from pyspark.sql import functions as F

train_coordinate_medians = train_df.select(
    F.expr("percentile_approx(latitude, 0.5)").alias("median_latitude"),
    F.expr("percentile_approx(longitude, 0.5)").alias("median_longitude")
).first()

train_median_latitude = train_coordinate_medians["median_latitude"]
train_median_longitude = train_coordinate_medians["median_longitude"]

print("Training median latitude:", train_median_latitude)
print("Training median longitude:", train_median_longitude)

# COMMAND ----------

def create_area_group(dataset, median_latitude, median_longitude):

    # Remove the exploratory full-dataset version first
    if "area_group" in dataset.columns:
        dataset = dataset.drop("area_group")

    return (
        dataset
        .withColumn(
            "area_group",
            F.when(
                F.col("latitude").isNull() |
                F.col("longitude").isNull(),
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

# COMMAND ----------

train_df = create_area_group(
    train_df,
    train_median_latitude,
    train_median_longitude
)

validation_df = create_area_group(
    validation_df,
    train_median_latitude,
    train_median_longitude
)

test_df = create_area_group(
    test_df,
    train_median_latitude,
    train_median_longitude
)

print("Area groups rebuilt successfully using training-only thresholds.")

# COMMAND ----------

print("TRAIN")
display(
    train_df.groupBy("area_group")
    .count()
    .orderBy(F.desc("count"))
)

print("VALIDATION")
display(
    validation_df.groupBy("area_group")
    .count()
    .orderBy(F.desc("count"))
)

print("TEST")
display(
    test_df.groupBy("area_group")
    .count()
    .orderBy(F.desc("count"))
)

# COMMAND ----------

def create_area_group(dataset, median_latitude, median_longitude):

    # Remove the exploratory area_group if it already exists
    if "area_group" in dataset.columns:
        dataset = dataset.drop("area_group")

    return (
        dataset
        .withColumn(
            "area_group",
            F.when(
                F.col("latitude").isNull() |
                F.col("longitude").isNull(),
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

# COMMAND ----------

train_df = create_area_group(
    train_df,
    train_median_latitude,
    train_median_longitude
)

validation_df = create_area_group(
    validation_df,
    train_median_latitude,
    train_median_longitude
)

test_df = create_area_group(
    test_df,
    train_median_latitude,
    train_median_longitude
)

print("Area groups rebuilt successfully.")

# COMMAND ----------

display(
    train_df
    .groupBy("area_group")
    .count()
    .orderBy(F.desc("count"))
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 6. Missing-Value Review
# MAGIC
# MAGIC Missing values are reviewed using the training dataset first.
# MAGIC
# MAGIC Any imputation strategy will be decided from training data only and then
# MAGIC applied consistently to validation and test data.

# COMMAND ----------

from pyspark.sql import functions as F

columns_to_check = [
    "location_description",
    "domestic",
    "beat",
    "district",
    "ward",
    "community_area",
    "latitude",
    "longitude",
    "hour",
    "month",
    "day_of_week",
    "is_weekend",
    "area_group",
    "primary_type"
]

missing_summary = []

for c in columns_to_check:
    result = train_df.select(
        F.sum(F.col(c).isNull().cast("long")).alias("missing_count"),
        F.count("*").alias("total_rows")
    ).first()

    missing_count = result["missing_count"]
    total_rows = result["total_rows"]

    missing_summary.append(
        (
            c,
            missing_count,
            round((missing_count / total_rows) * 100, 4)
        )
    )

missing_df = spark.createDataFrame(
    missing_summary,
    ["column", "missing_count", "missing_pct"]
)

display(
    missing_df.orderBy(F.desc("missing_count"))
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 7. Missing-Value Handling
# MAGIC
# MAGIC Missing values are handled using rules derived from the training dataset.
# MAGIC
# MAGIC - Missing location descriptions are assigned `Unknown`.
# MAGIC - Missing ward and community-area codes are assigned an explicit unknown category.
# MAGIC - Missing latitude and longitude values are imputed using training-set medians.
# MAGIC - A `coordinates_missing` indicator preserves information about whether the original coordinates were unavailable.
# MAGIC - The same training-derived rules are applied to validation and test datasets.

# COMMAND ----------

coordinate_medians = train_df.select(
    F.expr("percentile_approx(latitude, 0.5)").alias("latitude_median"),
    F.expr("percentile_approx(longitude, 0.5)").alias("longitude_median")
).first()

latitude_median = coordinate_medians["latitude_median"]
longitude_median = coordinate_medians["longitude_median"]

print("Training latitude median:", latitude_median)
print("Training longitude median:", longitude_median)

# COMMAND ----------

def handle_missing_values(dataset, latitude_median, longitude_median):

    return (
        dataset

        # Preserve whether coordinates were originally missing
        .withColumn(
            "coordinates_missing",
            F.when(
                F.col("latitude").isNull() |
                F.col("longitude").isNull(),
                1
            ).otherwise(0)
        )

        # Contextual category
        .fillna({
            "location_description": "Unknown"
        })

        # Geographic categorical codes
        .fillna({
            "ward": -1,
            "community_area": -1
        })

        # Numerical coordinates
        .fillna({
            "latitude": latitude_median,
            "longitude": longitude_median
        })
    )

# COMMAND ----------

train_df = handle_missing_values(
    train_df,
    latitude_median,
    longitude_median
)

validation_df = handle_missing_values(
    validation_df,
    latitude_median,
    longitude_median
)

test_df = handle_missing_values(
    test_df,
    latitude_median,
    longitude_median
)

print("Missing-value handling completed.")

# COMMAND ----------

columns_to_verify = [
    "location_description",
    "ward",
    "community_area",
    "latitude",
    "longitude"
]

verification = train_df.select([
    F.sum(F.col(c).isNull().cast("long")).alias(c)
    for c in columns_to_verify
])

display(verification)

# COMMAND ----------

display(
    train_df.groupBy("coordinates_missing")
    .count()
    .orderBy("coordinates_missing")
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 8. Define Categorical and Numerical Features
# MAGIC
# MAGIC Features are grouped according to their meaning rather than only their stored data type.
# MAGIC
# MAGIC Administrative geographic codes such as beat, district, ward, and community area
# MAGIC are treated as categorical variables.
# MAGIC
# MAGIC Continuous coordinates and temporal quantities are treated as numerical features.
# MAGIC Identifiers and the raw timestamp are retained only for tracking and split validation,
# MAGIC not as machine-learning predictors.

# COMMAND ----------

categorical_features = [
    "location_description",
    "beat",
    "district",
    "ward",
    "community_area",
    "area_group"
]

numerical_features = [
    "latitude",
    "longitude",
    "year",
    "month",
    "day_of_week",
    "hour",
    "is_weekend",
    "coordinates_missing"
]

target_column = "primary_type"

non_model_columns = [
    "unique_key",
    "date"
]

print("Categorical features:")
for c in categorical_features:
    print(" -", c)

print("\nNumerical features:")
for c in numerical_features:
    print(" -", c)

print("\nTarget:", target_column)

print("\nNot used as predictors:")
for c in non_model_columns:
    print(" -", c)

# COMMAND ----------

for c in categorical_features:
    distinct_count = train_df.select(c).distinct().count()
    print(f"{c}: {distinct_count} distinct values")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 9. Boolean and Cyclic Temporal Feature Transformation
# MAGIC
# MAGIC The `domestic` Boolean variable is converted to a numeric binary feature.
# MAGIC
# MAGIC Hour, weekday, and month are cyclic variables. Sine and cosine transformations
# MAGIC are created so that values at the beginning and end of each cycle remain close
# MAGIC in the feature space.
# MAGIC
# MAGIC The original temporal variables are retained for interpretability and tree-based models.

# COMMAND ----------

import math
from pyspark.sql import functions as F

def add_model_features(dataset):

    return (
        dataset

        # Boolean -> numeric
        .withColumn(
            "domestic_int",
            F.when(F.col("domestic") == True, 1).otherwise(0)
        )

        # Hour: 24-hour cycle
        .withColumn(
            "hour_sin",
            F.sin(2 * math.pi * F.col("hour") / 24)
        )
        .withColumn(
            "hour_cos",
            F.cos(2 * math.pi * F.col("hour") / 24)
        )

        # Day of week: 7-day cycle
        .withColumn(
            "day_of_week_sin",
            F.sin(2 * math.pi * F.col("day_of_week") / 7)
        )
        .withColumn(
            "day_of_week_cos",
            F.cos(2 * math.pi * F.col("day_of_week") / 7)
        )

        # Month: 12-month cycle
        .withColumn(
            "month_sin",
            F.sin(2 * math.pi * (F.col("month") - 1) / 12)
        )
        .withColumn(
            "month_cos",
            F.cos(2 * math.pi * (F.col("month") - 1) / 12)
        )
    )

# COMMAND ----------

train_df = add_model_features(train_df)
validation_df = add_model_features(validation_df)
test_df = add_model_features(test_df)

print("Boolean and cyclic features created successfully.")

# COMMAND ----------

display(
    train_df.select(
        "domestic",
        "domestic_int",
        "hour",
        "hour_sin",
        "hour_cos",
        "day_of_week",
        "day_of_week_sin",
        "day_of_week_cos",
        "month",
        "month_sin",
        "month_cos"
    ).limit(20)
)

# COMMAND ----------


## 10. Categorical Feature Encoding

Categorical predictors are encoded using transformations fitted on the training data only.

Administrative codes such as beat, district, ward, and community area are treated
as categories rather than continuous numerical quantities.

StringIndexer converts each category to an index, and OneHotEncoder creates
machine-learning-ready vectors.

Unseen categories in validation or test data are handled explicitly rather than
causing pipeline failures.

# COMMAND ----------

categorical_features = [
    "location_description",
    "beat",
    "district",
    "ward",
    "community_area",
    "area_group"
]

def cast_categorical_columns(dataset):
    result = dataset

    for c in categorical_features:
        result = result.withColumn(
            c,
            F.col(c).cast("string")
        )

    return result


train_df = cast_categorical_columns(train_df)
validation_df = cast_categorical_columns(validation_df)
test_df = cast_categorical_columns(test_df)

print("Categorical columns converted to string type.")

# COMMAND ----------

from pyspark.ml.feature import StringIndexer

indexers = [
    StringIndexer(
        inputCol=c,
        outputCol=f"{c}_index",
        handleInvalid="keep"
    )
    for c in categorical_features
]

# COMMAND ----------

from pyspark.ml.feature import OneHotEncoder

encoder = OneHotEncoder(
    inputCols=[
        f"{c}_index"
        for c in categorical_features
    ],
    outputCols=[
        f"{c}_ohe"
        for c in categorical_features
    ],
    handleInvalid="keep"
)

# COMMAND ----------

from pyspark.ml import Pipeline

categorical_pipeline = Pipeline(
    stages=indexers + [encoder]
)

# COMMAND ----------

categorical_model = categorical_pipeline.fit(train_df)

print("Categorical encoding pipeline fitted using training data only.")

# COMMAND ----------

train_encoded = categorical_model.transform(train_df)

validation_encoded = categorical_model.transform(validation_df)

test_encoded = categorical_model.transform(test_df)

print("Categorical encoding applied successfully.")

# COMMAND ----------

encoded_columns = []

for c in categorical_features:
    encoded_columns.extend([
        c,
        f"{c}_index",
        f"{c}_ohe"
    ])

display(
    train_encoded.select(
        *encoded_columns
    ).limit(10)
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 11. Target-Class Validation
# MAGIC
# MAGIC Before encoding the target variable `primary_type`, crime categories are compared
# MAGIC across training, validation, and test datasets.
# MAGIC
# MAGIC The objective is to verify whether validation or test data contain any target class
# MAGIC that was not observed during training.
# MAGIC
# MAGIC This check is important because a classifier cannot learn a crime category that
# MAGIC does not exist in its training data.

# COMMAND ----------

train_classes = (
    train_encoded
    .select("primary_type")
    .distinct()
)

validation_classes = (
    validation_encoded
    .select("primary_type")
    .distinct()
)

test_classes = (
    test_encoded
    .select("primary_type")
    .distinct()
)

print("Training classes:", train_classes.count())
print("Validation classes:", validation_classes.count())
print("Test classes:", test_classes.count())

# COMMAND ----------

validation_unseen_classes = (
    validation_classes
    .join(
        train_classes,
        on="primary_type",
        how="left_anti"
    )
)

print("Validation classes not present in training:")
display(validation_unseen_classes)

# COMMAND ----------

test_unseen_classes = (
    test_classes
    .join(
        train_classes,
        on="primary_type",
        how="left_anti"
    )
)

print("Test classes not present in training:")
display(test_unseen_classes)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 12. Target Variable Encoding
# MAGIC
# MAGIC The target variable `primary_type` is encoded into a numerical `label`
# MAGIC required by Spark machine-learning classifiers.
# MAGIC
# MAGIC The target encoder is fitted using the training dataset only and the same
# MAGIC mapping is applied to validation and test data.
# MAGIC
# MAGIC Validation and test data were checked beforehand and contain no crime categories
# MAGIC that are absent from the training dataset.

# COMMAND ----------

from pyspark.ml.feature import StringIndexer

target_indexer = StringIndexer(
    inputCol="primary_type",
    outputCol="label",
    handleInvalid="error"
)

target_model = target_indexer.fit(train_encoded)

print("Target encoder fitted using training data only.")

# COMMAND ----------

train_encoded = target_model.transform(train_encoded)
validation_encoded = target_model.transform(validation_encoded)
test_encoded = target_model.transform(test_encoded)

print("Target encoding applied successfully.")

# COMMAND ----------

label_mapping = [
    (index, crime_type)
    for index, crime_type in enumerate(target_model.labels)
]

label_mapping_df = spark.createDataFrame(
    label_mapping,
    ["label", "primary_type"]
)

display(label_mapping_df.orderBy("label"))

# COMMAND ----------

display(
    train_encoded.select(
        "primary_type",
        "label"
    ).distinct().orderBy("label")
)

# COMMAND ----------

print("Number of target classes:", len(target_model.labels))

# COMMAND ----------

# MAGIC %md
# MAGIC ## 13. Assemble Final Machine-Learning Features
# MAGIC
# MAGIC All processed predictors are combined into a single Spark `features` vector
# MAGIC required by the machine-learning algorithms.
# MAGIC
# MAGIC Categorical variables use one-hot encoded vectors.
# MAGIC Continuous/binary variables use their processed numeric values.
# MAGIC The target is stored in the `label` column.

# COMMAND ----------

categorical_ohe_features = [
    "location_description_ohe",
    "beat_ohe",
    "district_ohe",
    "ward_ohe",
    "community_area_ohe",
    "area_group_ohe"
]

numeric_model_features = [
    "latitude",
    "longitude",
    "year",

    "hour_sin",
    "hour_cos",

    "day_of_week_sin",
    "day_of_week_cos",

    "month_sin",
    "month_cos",

    "is_weekend",
    "domestic_int",
    "coordinates_missing"
]

final_feature_columns = (
    categorical_ohe_features
    + numeric_model_features
)

print("Final feature inputs:")
for c in final_feature_columns:
    print(" -", c)

# COMMAND ----------

from pyspark.ml.feature import VectorAssembler

assembler = VectorAssembler(
    inputCols=final_feature_columns,
    outputCol="features",
    handleInvalid="keep"
)

# COMMAND ----------

train_final = assembler.transform(train_encoded)
validation_final = assembler.transform(validation_encoded)
test_final = assembler.transform(test_encoded)

print("Final ML feature vectors created successfully.")

# COMMAND ----------

display(
    train_final.select(
        "unique_key",
        "primary_type",
        "label",
        "features"
    ).limit(10)
)

# COMMAND ----------

from pyspark.ml.functions import vector_to_array

feature_size = (
    train_final
    .select(
        F.size(vector_to_array("features")).alias("feature_size")
    )
    .first()["feature_size"]
)

print("Final feature vector size:", feature_size)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 14. Final Preprocessing Validation
# MAGIC
# MAGIC Before saving the machine-learning datasets, the final outputs are validated.
# MAGIC
# MAGIC The checks confirm:
# MAGIC - Original split row counts are preserved
# MAGIC - Every dataset contains an encoded target label
# MAGIC - Train, validation, and test use the same feature-vector size
# MAGIC - No records are lost during preprocessing

# COMMAND ----------

from pyspark.ml.functions import vector_to_array
from pyspark.sql import functions as F

def validate_final_dataset(name, dataset):

    summary = dataset.select(
        F.count("*").alias("rows"),
        F.sum(F.col("label").isNull().cast("long")).alias("missing_labels"),
        F.min(
            F.size(vector_to_array("features"))
        ).alias("min_feature_size"),
        F.max(
            F.size(vector_to_array("features"))
        ).alias("max_feature_size")
    ).first()

    print(f"{name}")
    print("Rows:", summary["rows"])
    print("Missing labels:", summary["missing_labels"])
    print("Minimum feature size:", summary["min_feature_size"])
    print("Maximum feature size:", summary["max_feature_size"])
    print("---------------------------")


validate_final_dataset("TRAIN", train_final)
validate_final_dataset("VALIDATION", validation_final)
validate_final_dataset("TEST", test_final)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 15. Save Final Machine-Learning Datasets
# MAGIC
# MAGIC The validated training, validation, and test datasets are saved as separate Delta tables.
# MAGIC
# MAGIC Each table preserves:
# MAGIC - Incident identifier for traceability
# MAGIC - Incident date for temporal evaluation
# MAGIC - Original target category
# MAGIC - Encoded target label
# MAGIC - Final 585-dimensional feature vector
# MAGIC
# MAGIC These tables will be handed over to Member 4 for model development and evaluation.

# COMMAND ----------

final_columns = [
    "unique_key",
    "date",
    "primary_type",
    "label",
    "features"
]

train_output = train_final.select(*final_columns)
validation_output = validation_final.select(*final_columns)
test_output = test_final.select(*final_columns)

print("Final modelling columns prepared.")

# COMMAND ----------

train_table = "workspace.default.chicago_crime_train_ml"
validation_table = "workspace.default.chicago_crime_validation_ml"
test_table = "workspace.default.chicago_crime_test_ml"

(
    train_output.write
    .mode("overwrite")
    .option("overwriteSchema", "true")
    .saveAsTable(train_table)
)

(
    validation_output.write
    .mode("overwrite")
    .option("overwriteSchema", "true")
    .saveAsTable(validation_table)
)

(
    test_output.write
    .mode("overwrite")
    .option("overwriteSchema", "true")
    .saveAsTable(test_table)
)

print("Train table saved:", train_table)
print("Validation table saved:", validation_table)
print("Test table saved:", test_table)

# COMMAND ----------

label_mapping_output = label_mapping_df.select(
    F.col("label").cast("double").alias("label"),
    "primary_type"
)

label_mapping_table = "workspace.default.chicago_crime_label_mapping"

(
    label_mapping_output.write
    .mode("overwrite")
    .option("overwriteSchema", "true")
    .saveAsTable(label_mapping_table)
)

print("Label mapping saved:", label_mapping_table)

# COMMAND ----------

preprocessing_metadata = [
    (
        float(train_median_latitude),
        float(train_median_longitude),
        585,
        31,
        376081,
        121633,
        164758
    )
]

metadata_df = spark.createDataFrame(
    preprocessing_metadata,
    [
        "training_median_latitude",
        "training_median_longitude",
        "feature_vector_size",
        "number_of_target_classes",
        "training_rows",
        "validation_rows",
        "test_rows"
    ]
)

metadata_table = "workspace.default.chicago_crime_preprocessing_metadata"

metadata_df.write.mode("overwrite").saveAsTable(metadata_table)

display(metadata_df)

# COMMAND ----------

print(
    "Saved training rows:",
    spark.table("workspace.default.chicago_crime_train_ml").count()
)

print(
    "Saved validation rows:",
    spark.table("workspace.default.chicago_crime_validation_ml").count()
)

print(
    "Saved test rows:",
    spark.table("workspace.default.chicago_crime_test_ml").count()
)

print(
    "Saved target classes:",
    spark.table("workspace.default.chicago_crime_label_mapping").count()
)

# COMMAND ----------

# MAGIC %md
# MAGIC # 16. Findings, Conclusion and Handover
# MAGIC
# MAGIC ## Key Findings
# MAGIC
# MAGIC 1. The cleaned dataset contained 662,472 reported crime incidents.
# MAGIC
# MAGIC 2. A chronological split was used to preserve the temporal nature of the data:
# MAGIC    - Training: 376,081 records
# MAGIC    - Validation: 121,633 records
# MAGIC    - Test: 164,758 records
# MAGIC
# MAGIC 3. Target leakage and non-predictive fields were excluded from the modelling feature set.
# MAGIC
# MAGIC 4. Temporal features were engineered from the incident timestamp, including:
# MAGIC    - Hour
# MAGIC    - Month
# MAGIC    - Day of week
# MAGIC    - Weekend indicator
# MAGIC    - Cyclic sine/cosine representations
# MAGIC
# MAGIC 5. A geographic `area_group` feature was engineered using latitude and longitude.
# MAGIC    For final modelling, the geographic thresholds were calculated using training
# MAGIC    data only:
# MAGIC    - Median latitude: 41.865358972
# MAGIC    - Median longitude: -87.661363753
# MAGIC
# MAGIC 6. Missing values were handled using training-derived rules:
# MAGIC    - Missing location descriptions -> Unknown
# MAGIC    - Missing ward/community-area codes -> explicit unknown category
# MAGIC    - Missing coordinates -> training medians
# MAGIC    - `coordinates_missing` preserves whether coordinates were originally absent
# MAGIC
# MAGIC 7. Geographic administrative codes such as beat, district, ward and community area
# MAGIC    were treated as categorical variables rather than continuous measurements.
# MAGIC
# MAGIC 8. Categorical encoders were fitted using training data only and then applied
# MAGIC    unchanged to validation and test datasets.
# MAGIC
# MAGIC 9. The target `primary_type` contains 31 crime categories.
# MAGIC    Validation and test data contained no target classes absent from training.
# MAGIC
# MAGIC 10. The final machine-learning feature vector contains 585 features for every
# MAGIC     training, validation and test record.
# MAGIC
# MAGIC ## Final Outputs
# MAGIC
# MAGIC The following Databricks tables were created for model development:
# MAGIC
# MAGIC - `workspace.default.chicago_crime_train_ml`
# MAGIC - `workspace.default.chicago_crime_validation_ml`
# MAGIC - `workspace.default.chicago_crime_test_ml`
# MAGIC - `workspace.default.chicago_crime_label_mapping`
# MAGIC - `workspace.default.chicago_crime_preprocessing_metadata`
# MAGIC
# MAGIC ## Handover to Member 4
# MAGIC
# MAGIC Member 4 should use:
# MAGIC
# MAGIC - `features` as the machine-learning input column
# MAGIC - `label` as the encoded target column
# MAGIC - Training data for model fitting
# MAGIC - Validation data for model comparison and hyperparameter tuning
# MAGIC - Test data only for final evaluation
# MAGIC
# MAGIC The final test dataset should not be used repeatedly during model selection or
# MAGIC hyperparameter tuning.
# MAGIC
# MAGIC Because the target classes are imbalanced, model comparison should not rely only
# MAGIC on accuracy. Macro precision, macro recall, macro F1, weighted F1, confusion
# MAGIC matrices and per-class results should also be considered.
# MAGIC
# MAGIC ## Conclusion
# MAGIC
# MAGIC The feature-engineering and preprocessing stages produced consistent,
# MAGIC leakage-aware and reproducible modelling datasets. All three data splits have
# MAGIC the same 585-dimensional feature structure and contain no missing target labels.
# MAGIC The processed datasets are now ready for machine-learning model development.

# COMMAND ----------

