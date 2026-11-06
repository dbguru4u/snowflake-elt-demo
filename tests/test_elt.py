import pytest

import snowflake_elt
from snowflake_elt import read_orders


def test_read_orders_parses_csv(tmp_path):
    csv_file = tmp_path / "orders.csv"
    csv_file.write_text(
        "order_date,order_id,customer,quantity,unit_price\n"
        "2026-01-02,1001,Ada,2,12.50\n",
        encoding="utf-8",
    )

    orders = read_orders(csv_file)

    assert len(orders) == 1
    assert str(orders[0][0]) == "2026-01-02"
    assert orders[0][1:] == (1001, "Ada", 2, pytest.approx(12.50))


def test_read_orders_rejects_invalid_row(tmp_path):
    csv_file = tmp_path / "orders.csv"
    csv_file.write_text(
        "order_date,order_id,customer,quantity,unit_price\n"
        "not-a-date,1001,Ada,2,12.50\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="line 2"):
        read_orders(csv_file)


def test_read_orders_requires_expected_columns(tmp_path):
    csv_file = tmp_path / "orders.csv"
    csv_file.write_text("date,total\n2026-01-02,12.50\n", encoding="utf-8")

    with pytest.raises(ValueError, match="columns"):
        read_orders(csv_file)


def test_main_uses_programmatic_access_token(monkeypatch):
    environment = {
        "SNOWFLAKE_ACCOUNT": "example-account",
        "SNOWFLAKE_USER": "example-user",
        "SNOWFLAKE_PAT": "test-pat",
        "SNOWFLAKE_ROLE": "ANALYST",
        "SNOWFLAKE_WAREHOUSE": "COMPUTE_WH",
        "SNOWFLAKE_DATABASE": "ANALYTICS",
        "SNOWFLAKE_SCHEMA": "PUBLIC",
    }
    for name, value in environment.items():
        monkeypatch.setenv(name, value)
    monkeypatch.setattr(snowflake_elt, "load_dotenv", lambda: None)

    class Connection:
        def close(self):
            pass

    connection_options = {}
    monkeypatch.setattr(
        snowflake_elt.snowflake.connector,
        "connect",
        lambda **kwargs: connection_options.update(kwargs) or Connection(),
    )
    monkeypatch.setattr(snowflake_elt, "run_elt", lambda conn, path: 0)

    snowflake_elt.main()

    assert connection_options["authenticator"] == "PROGRAMMATIC_ACCESS_TOKEN"
    assert connection_options["token"] == "test-pat"
