# 🏙️ Chicago Crime Prediction & AI Intelligence System

[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-blue?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110.0-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=black)](https://react.dev/)
[![Vite](https://img.shields.io/badge/Vite-5.0-646CFF?logo=vite&logoColor=white)](https://vitejs.dev/)
[![Apache Spark](https://img.shields.io/badge/Apache%20Spark-3.5%2F4.2-E25A1C?logo=apachespark&logoColor=white)](https://spark.apache.org/)
[![Databricks](https://img.shields.io/badge/Databricks-Pipeline%2001--13-FF3621?logo=databricks&logoColor=white)](https://www.databricks.com/)

An end-to-end Big Data & Machine Learning analytics platform powered by the **City of Chicago Open Data Portal (662,472 records)**. The platform features an automated **13-stage Databricks ML pipeline**, a high-performance **FastAPI** inference backend, and a modern **React + Vite** frontend web dashboard.

---

## 👥 Project Team & Contributors

| Member Name | Role & Core Responsibilities |
| :--- | :--- |
| **Savin Udana** | Pipeline Orchestration, Frontend Light Theme Architecture & Backend Integration |
| **Sanuja Salitha** | Data Ingestion, Data Understanding & EDA Pipelines |
| **Amasha Weerasuriya** | Data Cleaning & Spark Feature Engineering |
| **Akila Jathunga** | Multiclass ML Preprocessing, Model Training, Comparison & Tuning |

---

## 🚀 Key Features

- **Multi-Class Crime Category Prediction (`primary_type`)**: Forecasts the expected crime type (e.g., `THEFT`, `BATTERY`, `CRIMINAL DAMAGE`, `MOTOR VEHICLE THEFT`, `ROBBERY`, `BURGLARY`, `ASSAULT`) using spatial, administrative, temporal, and situational features.
- **Probability Distributions**: Visualizes Softmax probability distributions across all crime categories for every incident scenario.
- **Dynamic Risk & Arrest Likelihood**: Estimates risk severity, emergency dispatch response time, and arrest probability based on historical patterns.
- **Geospatial Hotspot Mapping**: Real-time hotspot visualization across Chicago's 77 official Community Areas and 22+ Police Districts.
- **Citywide Intelligence Dashboard**: Clean light-themed metrics, seasonal trend comparisons, and live incident streams.
- **Automated 13-Stage Databricks Pipeline**: End-to-end reproducible PySpark workflow from raw ingestion to model export.

---

## 📂 Project Folder Structure

```
Chicago_Crime_Prediction/
├── backend/                             # FastAPI Backend & Inference Engine
│   ├── app/
│   │   ├── __init__.py
│   │   ├── config.py                   # Server & Model artifact path configurations
│   │   ├── main.py                     # FastAPI routes & dataset analytics endpoints
│   │   ├── prediction.py               # ML Predictor engine & Chicago area mapping
│   │   └── schemas.py                  # Pydantic request/response schemas
│   ├── models/                         # Serialized ML model artifacts (< 40MB)
│   │   ├── chicago_crime_model.joblib  # Trained Random Forest classifier
│   │   └── label_encoder.joblib        # Scikit-learn Target LabelEncoder
│   ├── requirements.txt                # Backend Python dependencies
│   └── train_model.py                  # Standalone model training & compression script
│
├── databricks/                          # 13-Stage Databricks ML Pipeline Notebooks
│   ├── 00_Master_Pipeline_Runner.ipynb # Master orchestration notebook
│   ├── 01_Data_Ingestion/             # Stage 01: Raw data ingestion & validation
│   ├── 02_Data_Understanding/         # Stage 02: Schema validation & profiling
│   ├── 03_Data_Cleaning/              # Stage 03: Data deduplication & cleaning
│   ├── 04_EDA/                        # Stage 04: Exploratory Data Analysis & visual reports
│   ├── 05_Feature_Engineering/        # Stage 05: Cyclical temporal & area grouping
│   ├── 06_Preprocessing/              # Stage 06: Imputation, encoding & split validation
│   ├── 07_Logistic_Regression/        # Stage 07: Linear multiclass baseline
│   ├── 08_Decision_Tree/              # Stage 08: Decision Tree baseline
│   ├── 09_Random_Forest/              # Stage 09: Random Forest ensemble baseline
│   ├── 10_XGBoost/                    # Stage 10: Gradient boosted baseline
│   ├── 11_Model_Comparison/           # Stage 11: Cross-model benchmark & metric matrix
│   ├── 12_Hyperparameter_Tuning/      # Stage 12: Grid search & hyperparameter tuning
│   ├── 13_Final_Model/                # Stage 13: Champion model freezing & evaluation
│   └── run_all_pipeline.py            # Headless runner for all 13 stages
│
├── frontend/                            # React + Vite Modern Light Web Application
│   ├── src/
│   │   ├── components/
│   │   │   ├── cards/                 # MetricCard & analytics KPI cards
│   │   │   ├── forms/                 # PredictionForm with all dataset input features
│   │   │   └── layout/                # Navbar & Sidebar layout navigation
│   │   ├── context/                   # Global React AppContext
│   │   ├── pages/
│   │   │   ├── Dashboard.jsx          # Citywide Intelligence Overview
│   │   │   ├── CrimePredictor.jsx     # AI Risk & Crime Type Predictor
│   │   │   ├── TrendsView.jsx         # Historical Monthly Trends & Breakdown
│   │   │   └── MapView.jsx            # Chicago Community Area Hotspot Map
│   │   ├── services/                  # Axios API services & fallback data
│   │   ├── utils/constants.js         # 77 Chicago areas, districts, and locations
│   │   ├── App.jsx                    # Root App component
│   │   └── index.css                  # Tailwind CSS & custom light theme styling
│   ├── package.json
│   ├── tailwind.config.js
│   └── vite.config.js
│
├── data/                                # Cleaned and raw data directories (Git Ignored)
│   ├── clean/                         # chicago_crime_clean.csv (662,472 rows)
│   └── raw/                           # chicago_crime_raw.csv
│
├── .gitignore                           # Excludes > 100MB data files & caches
└── README.md                            # Project documentation
```

---

## 🛠️ Technology Stack

- **Machine Learning & Analytics**: Scikit-Learn, PySpark, Pandas, NumPy, Scipy, Joblib
- **Big Data Platform**: Databricks Lakehouse / Apache Spark (Delta Tables & Views)
- **Backend API**: FastAPI, Uvicorn, Pydantic
- **Frontend Framework**: React 18, Vite, Tailwind CSS, Lucide React
- **Visualization**: Chart.js / CSS Data Visualizations

---

## ⚡ Step-by-Step Setup & Execution Guide

### Prerequisites
- **Python 3.10, 3.11, or 3.12** installed
- **Node.js 18+ & npm** installed
- **Git** installed

---

### Step 1: Clone the Repository

```bash
git clone https://github.com/SaweenAbey/Chicago_Crime_Prediction.git
cd Chicago_Crime_Prediction
```

---

### Step 2: Python Virtual Environment & Backend Setup

1. Create and activate a Python virtual environment:

```powershell
# Windows PowerShell
python -m venv .venv
.venv\Scripts\activate

# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
```

2. Install backend dependencies:

```bash
pip install -r backend/requirements.txt
```

3. (Optional) Retrain or verify the ML model locally:

```bash
python backend/train_model.py
```

4. Start the **FastAPI Backend Server**:

```bash
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

> 🌐 **Backend API**: [http://localhost:8000](http://localhost:8000)  
> 📖 **Interactive Swagger Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)

---

### Step 3: Frontend Setup & Execution

Open a **new terminal window**:

1. Navigate to the `frontend/` directory:

```bash
cd frontend
```

2. Install Node.js dependencies:

```bash
npm install
```

3. Start the **Vite Development Server**:

```bash
npm run dev
```

> 🖥️ **Frontend Application**: [http://localhost:5173](http://localhost:5173)

---

### Step 4: Running the Databricks ML Pipeline (Optional)

To execute all **13 Databricks stages sequentially** from ingestion to model comparison:

```powershell
python databricks/run_all_pipeline.py
```

---

## 📊 Pipeline Stages Overview

| Stage | Name | Description |
| :---: | :--- | :--- |
| **01** | `01_Data_Ingestion` | Ingests Chicago Open Data CSV and registers raw Delta table |
| **02** | `02_Data_Understanding` | Statistical profiling, null assessments, and distribution checks |
| **03** | `03_Data_Cleaning` | Deduplication, coordinate bounds filtering & type casting |
| **04** | `04_EDA` | Exploratory data analysis, temporal patterns & correlation reports |
| **05** | `05_Feature_Engineering` | Hourly cyclical features, weekend flags & spatial quadrant tags |
| **06** | `06_Preprocessing` | Leakage-free split validation, standard imputation & One-Hot encoding |
| **07** | `07_Logistic_Regression` | Multinomial Logistic Regression baseline |
| **08** | `08_Decision_Tree` | Multi-class Decision Tree classifier |
| **09** | `09_Random_Forest` | Random Forest ensemble classifier |
| **10** | `10_XGBoost` | Gradient boosted tree classifier |
| **11** | `11_Model_Comparison` | Comprehensive benchmark matrix (Macro F1, Accuracy, Latency) |
| **12** | `12_Hyperparameter_Tuning` | Systematic grid search tuning on validation sets |
| **13** | `13_Final_Model` | Frozen final model evaluation on test hold-out set |

---

## 🔌 API Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/` | API status and metadata |
| `GET` | `/health` | Healthcheck and model load status |
| `POST` | `/api/predict` | Multiclass crime prediction for input incident features |
| `GET` | `/api/stats/overview` | High-level citywide metrics and totals |
| `GET` | `/api/stats/trends` | Monthly crime trends breakdown |
| `GET` | `/api/stats/hotspots` | Community Area risk hotspots and coordinates |
| `GET` | `/api/incidents/recent` | Live incident stream feed |
| `POST` | `/api/pipeline/run` | Triggers full Databricks pipeline execution (01-13) |

---

## 🛡️ License

This project is developed for educational and research purposes under the MIT License using public data provided by the **City of Chicago**.