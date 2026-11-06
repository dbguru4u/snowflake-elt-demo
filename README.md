# Snowflake ELT Demo

A tiny CSV-to-Snowflake ELT example:

1. Extracts orders from `data/orders.csv`.
2. Loads them into `RAW_ORDERS`.
3. Transforms them with SQL into `DAILY_SALES`.

## Requirements

- Python 3.11+
- A Snowflake account with a warehouse, database, and schema
- A Snowflake user and role with access to those objects and permission to create tables

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

On Windows PowerShell, activate the environment with:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## Configure Snowflake

Copy the example environment file, then replace its placeholders with values
from your Snowflake account:

```powershell
Copy-Item .env.example .env
python snowflake_elt.py
```

The `.env` file is loaded automatically and is excluded from Git. The
connector uses `SNOWFLAKE_PAT` with
`authenticator="PROGRAMMATIC_ACCESS_TOKEN"`. Replace the PAT placeholder in
`.env` with a Snowflake programmatic access token; do not commit that file. For
GitHub Actions, add the token as the repository secret `SNOWFLAKE_PAT`. PAT
authentication must be enabled for your Snowflake account and user. The account
identifier should be the account name or locator expected by the Snowflake
Python connector, not the full browser URL.

The role needs permission to use the selected warehouse, database, and schema,
and to create and replace tables in the schema. Once connected, the script reads
`data/orders.csv`, loads `RAW_ORDERS`, and builds `DAILY_SALES`.
