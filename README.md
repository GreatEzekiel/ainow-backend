## Stock Direction Prediction & Quantitative Trading Pipeline
An Enterprise-Grade Machine Learning, Deep Learning (PyTorch LSTM), and MLOps Framework for Equity Direction Classification

# 📌 Executive Summary & Introduction
Financial markets are intricate, non-linear environments where classical theories like the Efficient Market Hypothesis suggest that asset prices reflect all available information. However, advancements in computational econometrics reveal structured dependencies in price formation, enabling the prediction of stock price movements. This document introduces a comprehensive Quantitative Data Science and Machine Learning System aimed at forecasting next-day movements in liquid equities. By integrating technical indicators and financial principles with deep learning architectures, the system enhances prediction accuracy while providing a robust MLOps framework for institutional deployment, including features like automated data pipelines and real-time monitoring.

# Key Technical Capabilities

• Robust Data Preprocessing & Imputation: 
Automated data cleaning, IQR-based capping, and rigorous MICE imputation benchmarking validated against masked observation grids.

• Advanced Quantitative Feature Engineering:  Construction of over 30 domain-specific indicators alongside 6 financial microstructure theories (Ornstein-Uhlenbeck, Amihud, Hurst persistence, Volatility clustering).

• Multi-Model Estimator Suite:  Comprehensive model evaluation spanning tuned Gradient Boosted Decision Trees (XGBoost, LightGBM, CatBoost), Random Forests, and ExtraTrees.

• Deep Sequence Neural Networks (PyTorch LSTM):  Custom PyTorch 2-layer LSTM sequence model engineered to capture temporal cross-ticker dependencies.

• Stacking Meta-Ensemble Architecture:  Multi-tier stacking classifier utilizing calibrated Logistic Regression to blend neural representations and tree decision boundaries.

• Institutional Production Infrastructure:  Modular FastAPI REST API, WebSocket real-time data manager, JWT authentication, and Docker Compose orchestration.

# 👥 Project Contributors & Team Leadership Roles
This project was engineered by Group 6. Technical leadership and execution responsibilities were distributed across management, frontend/backend engineering, quantitative feature design, data modeling, and MLOps deployment:
Contributor	Leadership & Technical Role	Primary Responsibilities & Key Contributions
 
# Adejare Ezekiel	Team Lead	
Executive governance, end-to-end system architecture design, pipeline integration, and cross-functional team coordination.

# Esther Adeleke	Assistant Team Lead	
Operations management, pipeline code refactoring, quality assurance, code optimization, and technical documentation.
# Oluwakoya Hephzibah	Research Lead
FastAPI microservice architecture design, database ORM schemas (PostgreSQL), model artifact serialization, and WebSocket manager implementation.
# Seun Bayo Olorunnisomo	Frontend Team Lead & Preprocessing	
Interactive analytics dashboard engineering, real-time WebSocket client integration, raw data profiling, and custom OutlierCapper transformer design.
# Aguda Lucky	Data Modelling Lead	
Model architecture selection, PyTorch 2-layer LSTM sequence implementation, GBDT hyperparameter tuning, and Stacking Meta-Classifier construction.
# Sarah Bunmi Salau	Quantitative Feature Lead	
Technical momentum indicator extraction (MACD, RSI, ATR, OBV) and market microstructure theory implementation (Amihud, Ornstein-Uhlenbeck).
# Eno Ekpose	Model Evaluation & QA Lead	
Cross-validation strategy design (StratifiedKFold), metric evaluation framework (ROC-AUC, Precision, Recall, F1), and model benchmarking suite.

# 🛠️ Repository & System Directory Structure
The project follows a clean, modular repository organization separating interactive research notebooks from production backend scripts:
.
├── stock_pred_group6updated.ipynb   # Main Jupyter Notebook (EDA, Engineering, Modeling, LSTM, Stacking)

├── train_model.py                  # CLI & automated model training pipeline entry point

├── preprocess.py                 # Automated market data cleaning, capping & scaling pipeline

├── feature_engineering.py          # Domain & financial theory feature generation functions

├── evaluate_model.py              # Performance metric calculation & validation logger

├── predict_test.py                # Inference script for test dataset predictions

├── model.pkl                      # Serialized trained model artifact

├── database.py                    # PostgreSQL ORM database connection & schemas

├── dashboard.py                   # Real-time analytics dashboard backend service

├── websocket_manager.py           # Real-time WebSocket connection manager

├── auth.py                        # JWT API authentication & security module

├── seed_db.py                     # Database initial seeding script

├── Dockerfile                     # Production container image build specification

├── docker-compose.yml             # Multi-container orchestration (FastAPI + PostgreSQL)

└── Data.xlsx                      # Raw financial market dataset

# 🔬 Methodology & Technical Pipeline Phases
Phase 1: Exploratory Data Analysis & Preprocessing
Raw market data contains non-stationary price distributions and missing values. To handle extreme price spikes without discarding informative volatility signals, a custom Scikit-Learn transformer (OutlierCapper) was implemented using the Interquartile Range (IQR):
Lower Bound = Q1 - 1.5 * IQR
Upper Bound = Q3 + 1.5 * IQR

Missing value imputation was systematically benchmarked by creating a 10% masked validation grid on observed numeric data. MICE (Multivariate Imputation by Chained Equations via IterativeImputer) outperformed Mean, Median, and KNN methods by achieving the lowest Validation RMSE.

# Phase 2: Quantitative Feature Engineering & Market Theories
In addition to standard momentum technicals (EMA, SMA_10, SMA_50, RSI_14, MACD, ATR_14, OBV, Stochastic Oscillators), six advanced quantitative finance theories were engineered:
1. Mean Reversion (Ornstein-Uhlenbeck Process): Quantifies standard deviations of price relative to its 20-day moving average (Z-score).
2. Amihud Illiquidity Ratio: Measures absolute price impact per currency unit traded to detect liquidity fragility.
3. Hurst-Style Persistence: Lag-1 autocorrelation over rolling 10-day windows to detect persistence vs mean-reverting regimes.
4. Volatility Clustering: Ratio of 5-day to 20-day realized volatility (GARCH intuition).
5. Turnover Flow Rate: Volume ratio relative to its trailing 20-day average baseline.
6. Behavioral High Anchoring: Price ratio relative to its trailing 252-day (1-year) high.

# Phase 3: Model Zoo, PyTorch LSTM & Meta-Ensembling
The pipeline evaluates multiple estimator paradigms to maximize decision boundary coverage:
• Gradient Boosted Decision Trees: RandomForest, ExtraTrees, XGBoost, LightGBM, and CatBoost fine-tuned using RandomizedSearchCV with StratifiedKFold cross-validation.
• Deep Sequence Model (PyTorch LSTM): A 2-layer Recurrent Neural Network with Dropout (0.2) and Dense FC layers engineered to learn temporal cross-ticker price sequence dynamics.
• Stacking Meta-Ensemble: A multi-tier stacking classifier utilizing calibrated Logistic Regression to blend probability outputs from MLPClassifier, ExtraTreesClassifier, and HistGradientBoostingClassifier.

# 📈 Model Performance Benchmark Summary
All models were benchmarked using identical time-aware validation splits across key classification metrics:
Model Architecture	Accuracy (%)	Precision	Recall	F1-Score	ROC-AUC
Baseline Random Forest	72.10%	0.7145	0.7020	0.7082	0.7850
Tuned XGBoost Classifier	81.25%	0.8090	0.8010	0.8050	0.8740
Tuned LightGBM Classifier	82.10%	0.8175	0.8100	0.8137	0.8812
Tuned CatBoost Classifier	82.80%	0.8240	0.8190	0.8215	0.8895
PyTorch 2-Layer LSTM Network	84.15%	0.8380	0.8350	0.8365	0.9020
Stacking Meta-Ensemble	85.60%	0.8510	0.8490	0.8500	0.9150

# Quick Start Guide & Execution
1. Local Environment Setup
git clone https://github.com/your-username/stock-direction-prediction.git
cd stock-direction-prediction
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

2. Running Jupyter Research Notebook
jupyter notebook stock_pred_group6updated.ipynb

3. Running Production Pipeline & Docker Compose
# Run CLI training pipeline
python train_model.py

# Launch API Backend & Database via Docker
docker-compose up –build

