# DLT Hyperliquid Pipeline

A [dlt (data load tool)](https://dlthub.com/) pipeline that extracts funding history data from the [Hyperliquid](https://hyperliquid.xyz/) API and loads it into databases (this repo shows examples for DuckDB or PostgreSQL, but any [destination](https://dlthub.com/docs/dlt-ecosystem/destinations/) suported by dlt should work).

## What This Pipeline Does

This pipeline:
- Uses incremental loading to efficiently sync new data
- Supports both DuckDB (local) and PostgreSQL (remote) destinations
- Handles rate limiting and error recovery
- Transforms timestamps to datetime format and adds paired coin information

## Features

- **Incremental Loading**: Only fetches new data since the last run
- **Multiple Assets**: Simultaneously loads data for a configurable set of crypto assets
- **Data Transformation**: Converts timestamps and adds metadata
- **Flexible Destinations**: Supports both DuckDB and PostgreSQL

## Prerequisites

- Python 3.13+
- UV package manager (recommended) or pip

## Installation

1. Clone this repository:
```bash
git clone https://github.com/swang2016/dlt-hyperliquid.git
cd dlt-hyperliquid
```

2. Install dependencies using UV:
```bash
uv sync
```

Or using pip:
```bash
pip install -e .
```

3. Install additional dependencies for PostgreSQL (only if switching to PostgreSQL):
```bash
uv add psycopg2-binary python-dotenv
# or with pip:
# pip install psycopg2-binary python-dotenv
```

## Configuration

### DuckDB Configuration (Default)

The pipeline is configured by default to use DuckDB for local development and testing:

1. **No secrets configuration needed** - DuckDB stores data locally in a file
2. Simply run: `uv run python hyperliquid_pipeline.py`

This will create a `funding_rates.duckdb` file in your project directory.


### PostgreSQL Configuration

To switch from DuckDB to PostgreSQL, you have two options:

#### Option 1: Using secrets.toml (Recommended)

1. Configure your PostgreSQL credentials in `.dlt/secrets.toml`:

```toml
[destination.postgres.credentials]
database = "your_database_name"
username = "your_username"
password = "your_password"
host = "your_host"
port = 5432
```

2. Modify `hyperliquid_pipeline.py` to use dlt's built-in PostgreSQL destination by commenting out the DuckDB section and uncommenting the PostgreSQL section:

```python
# Comment out the DuckDB pipeline
# pipeline = dlt.pipeline(
#     pipeline_name="funding_rates",
#     destination='duckdb',
#     dataset_name="hyperliquid",
# )

# Uncomment the PostgreSQL pipeline  
pipeline = dlt.pipeline(
    pipeline_name="funding_rates",
    destination='postgres',
    dataset_name="hyperliquid",
)
```

#### Option 2: Using Environment Variables

1. Create a `.env` file in the project root:

```env
POSTGRES_USER=your_username
POSTGRES_PASSWORD=your_password
POSTGRES_HOST=your_host
POSTGRES_PORT=5432
POSTGRES_DATABASE=your_database_name
```

2. In `hyperliquid_pipeline.py`, uncomment the PostgreSQL section and comment out the DuckDB section:

```python
# Comment out the DuckDB pipeline
# pipeline = dlt.pipeline(
#     pipeline_name="funding_rates",
#     destination='duckdb',
#     dataset_name="hyperliquid",
# )

# Uncomment the PostgreSQL pipeline with environment variables
db = postgres(
    credentials=(
        f"postgresql://"
        f"{os.getenv('POSTGRES_USER')}:"
        f"{os.getenv('POSTGRES_PASSWORD')}@"
        f"{os.getenv('POSTGRES_HOST')}:"
        f"{os.getenv('POSTGRES_PORT')}/"
        f"{os.getenv('POSTGRES_DATABASE')}"
    )
)
pipeline = dlt.pipeline(
    pipeline_name="funding_rates",
    destination=db,
    dataset_name="hyperliquid",
)
```

## Running Examples

### Example 1: Load Data into DuckDB (Default)

The simplest way to run the pipeline with the default DuckDB configuration:

```bash
# Run the pipeline (uses DuckDB by default)
uv run python hyperliquid_pipeline.py
```

This will create a `funding_rates.duckdb` file in your project directory with all the loaded data.

You can also run it programmatically:

```bash
uv run python -c "
from hyperliquid_pipeline import load_hyperliquid
load_hyperliquid()
"
```

### Example 2: Load Data into PostgreSQL

First, ensure your PostgreSQL credentials are configured and the code is switched to use PostgreSQL (see Configuration section above).

```bash
# Run the pipeline (after switching to PostgreSQL configuration)
uv run python hyperliquid_pipeline.py
```

### Example 3: Query Loaded Data

#### Querying DuckDB:
```python
import duckdb

# Connect to the database
conn = duckdb.connect('funding_rates.duckdb')

# Query the data
result = conn.execute("""
    SELECT * FROM hyperliquid.btc_usd 
    ORDER BY time DESC 
    LIMIT 10
""").fetchall()

print(result)
```

#### Querying PostgreSQL:
```python
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

# Connect to PostgreSQL
conn = psycopg2.connect(
    host=os.getenv('POSTGRES_HOST'),
    database=os.getenv('POSTGRES_DATABASE'),
    user=os.getenv('POSTGRES_USER'),
    password=os.getenv('POSTGRES_PASSWORD'),
    port=os.getenv('POSTGRES_PORT')
)

cur = conn.cursor()
cur.execute("SELECT * FROM hyperliquid.btc_usd ORDER BY time DESC LIMIT 10;")
results = cur.fetchall()
print(results)
```

## Data Schema

Each asset table contains the following columns:

- `time`: Timestamp (primary key)
- `timestamp`: Converted datetime
- `funding_rate`: The funding rate value
- `premium`: Premium value
- `paired_coin`: Always "USD"
- `_dlt_load_id`: DLT metadata
- `_dlt_id`: DLT metadata

## Assets Tracked

The pipeline currently tracks funding history for:
- BTC/USD (`btc_usd` table)
- ETH/USD (`eth_usd` table)  
- HYPE/USD (`hype_usd` table)
- SOL/USD (`sol_usd` table)
- DOGE/USD (`doge_usd` table)
- FARTCOIN/USD (`fartcoin_usd` table)

## Incremental Loading

The pipeline uses incremental loading starting from timestamp `1683849600047` (May 12, 2023). On subsequent runs, it will only fetch new data since the last successful load.

## Development

To modify which assets are tracked, edit the `ASSETS` list in `hyperliquid/__init__.py`:

```python
ASSETS = ["BTC", "ETH", "HYPE", "SOL", "DOGE", "FARTCOIN"]
```

To change the start time for historical data, modify `START_TIME` in the same file.
