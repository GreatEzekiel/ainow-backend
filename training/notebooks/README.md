# Experimental Notebooks

This folder is dedicated to exploratory data analysis (EDA) and hyperparameter experimentation prior to converting code into the modular scripts above.

### Suggested Notebook Order:
1. `01_eda.ipynb`: Data distribution inspection, missing value analysis, and correlation plots.
2. `02_feature_selection.ipynb`: Experimentation with RSI, MACD, Bollinger Bands, and SMA window periods.
3. `03_model_experiments.ipynb`: Benchmark XGBoost vs. RandomForest vs. LogisticRegression models.

*Note: Clean production code from notebooks should be refactored back into `preprocess.py`, `feature_engineering.py`, and `train_model.py`.*