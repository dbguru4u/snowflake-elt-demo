import csv
import os
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any

import snowflake.connector
from dotenv import load_dotenv


Order = tuple[date, int, str, int, Decimal]


def read_orders(csv_path: Path) -> list[Order]:
    """Read and validate source orders from CSV."""
    orders: list[Order] = []

    with csv_path.open(newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        required = {"order_date", "order_id", "customer", "quantity", "unit_price"}

        if not reader.fieldnames or not required.issubset(reader.fieldnames):
            raise ValueError(f"CSV must contain these columns: {sorted(required)}")

        for line_number, row in enumerate(reader, start=2):
            try:
                orders.append(
                    (
                        date.fromisoformat(row["order_date"]),
                        int(row["order_id"]),
                        row["customer"].strip(),
                        int(row["quantity"]),
                        Decimal(row["unit_price"]),
                    )
                )
            except (TypeError, ValueError, ArithmeticError) as exc:
                raise ValueError(f"Invalid order on CSV line {line_number}") from exc

    return orders


def _execute(conn: Any, sql: str, params: Any = None) -> None:
    cursor = conn.cursor()
    try:
        cursor.execute(sql, params) if params is not None else cursor.execute(sql)
    finally:
        cursor.close()


def run_elt(conn: Any, csv_path: Path) -> int:
    """Load CSV rows into a raw table and build the daily sales table."""
    orders = read_orders(csv_path)

    _execute(
        conn,
        """
        CREATE TABLE IF NOT EXISTS RAW_ORDERS (
            ORDER_DATE DATE,
            ORDER_ID INTEGER,
            CUSTOMER VARCHAR,
            QUANTITY INTEGER,
            UNIT_PRICE NUMBER(12, 2)
        )
        """,
    )
    _execute(conn, "TRUNCATE TABLE RAW_ORDERS")

    if orders:
        cursor = conn.cursor()
        try:
            cursor.executemany(
                """
                INSERT INTO RAW_ORDERS
                    (ORDER_DATE, ORDER_ID, CUSTOMER, QUANTITY, UNIT_PRICE)
                VALUES (%s, %s, %s, %s, %s)
                """,
                orders,
            )
        finally:
            cursor.close()

    _execute(
        conn,
        """
        CREATE OR REPLACE TABLE DAILY_SALES AS
        SELECT
            ORDER_DATE,
            COUNT(DISTINCT ORDER_ID) AS ORDER_COUNT,
            SUM(QUANTITY) AS UNITS_SOLD,
            SUM(QUANTITY * UNIT_PRICE) AS REVENUE
        FROM RAW_ORDERS
        GROUP BY ORDER_DATE
        """,
    )

    return len(orders)


def main() -> None:
    load_dotenv()

    required = [
        "SNOWFLAKE_ACCOUNT",
        "SNOWFLAKE_USER",
        "SNOWFLAKE_PAT",
        "SNOWFLAKE_ROLE",
        "SNOWFLAKE_WAREHOUSE",
        "SNOWFLAKE_DATABASE",
        "SNOWFLAKE_SCHEMA",
    ]
    missing = [name for name in required if not os.getenv(name)]
    if missing:
        raise SystemExit(f"Missing environment variables: {', '.join(missing)}")

    conn = snowflake.connector.connect(
        account=os.environ["SNOWFLAKE_ACCOUNT"],
        user=os.environ["SNOWFLAKE_USER"],
        authenticator="PROGRAMMATIC_ACCESS_TOKEN",
        token=os.environ["SNOWFLAKE_PAT"],
        role=os.environ["SNOWFLAKE_ROLE"],
        warehouse=os.environ["SNOWFLAKE_WAREHOUSE"],
        database=os.environ["SNOWFLAKE_DATABASE"],
        schema=os.environ["SNOWFLAKE_SCHEMA"],
    )
    try:
        count = run_elt(conn, Path("data/orders.csv"))
        print(f"Loaded {count} orders; built DAILY_SALES.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
