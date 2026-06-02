"""SQLite database connection and helpers."""
import sqlite3
import os
from typing import Any

DB_PATH = os.environ.get("DATABASE_PATH", "./database/prices.db")


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def query(sql: str, params: tuple = ()) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(sql, params).fetchall()
        return [dict(r) for r in rows]


def execute(sql: str, params: tuple = ()) -> int:
    with get_conn() as conn:
        cur = conn.execute(sql, params)
        conn.commit()
        return cur.lastrowid


def get_all_materials() -> list[dict]:
    return query("SELECT * FROM materials ORDER BY category, name")


def get_material_by_name(name: str) -> dict | None:
    rows = query(
        "SELECT * FROM materials WHERE lower(name) LIKE ? LIMIT 1",
        (f"%{name.lower()}%",),
    )
    return rows[0] if rows else None


def get_materials_by_category(category: str) -> list[dict]:
    return query(
        "SELECT * FROM materials WHERE lower(category) = ? ORDER BY name",
        (category.lower(),),
    )


def get_all_labor() -> list[dict]:
    return query("SELECT * FROM labor ORDER BY trade")


def get_labor_by_trade(trade: str) -> dict | None:
    rows = query(
        "SELECT * FROM labor WHERE lower(trade) LIKE ? LIMIT 1",
        (f"%{trade.lower()}%",),
    )
    return rows[0] if rows else None


def update_material_price(material_id: int, price_gel: float) -> None:
    execute(
        "UPDATE materials SET price_gel=?, updated_at=datetime('now') WHERE id=?",
        (price_gel, material_id),
    )


def update_labor_price(labor_id: int, price_gel: float) -> None:
    execute(
        "UPDATE labor SET price_gel=?, updated_at=datetime('now') WHERE id=?",
        (price_gel, labor_id),
    )
