from pathlib import Path

# Resolve root directory relative to this config file
BASE_DIR = Path(__file__).resolve().parent.parent

# Data directory paths
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
EXTERNAL_DATA_DIR = DATA_DIR / "external"

# Specific file paths
RAW_EXCEL_PATH = RAW_DATA_DIR / "Data.xlsx"
EXTERNAL_INDEX_PATH = EXTERNAL_DATA_DIR / "ngx_asi_index.csv"

CLEANED_CSV_PATH = PROCESSED_DATA_DIR / "cleaned_prices.csv"
FEATURE_PARQUET_PATH = PROCESSED_DATA_DIR / "feature_dataset.parquet"
FEATURE_CSV_PATH = PROCESSED_DATA_DIR / "feature_dataset.csv"


def init_data_directories() -> None:
    """Ensures all data subdirectories exist."""
    for folder in [RAW_DATA_DIR, PROCESSED_DATA_DIR, EXTERNAL_DATA_DIR]:
        folder.mkdir(parents=True, exist_ok=True)