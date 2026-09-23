"""Retail indicators using integer cents, parameterized SQL and explicit grain."""
import sqlite3
from contextlib import closing
from common import unique, integer, text

def analyze(data):
    unique(data["products"], "sku")
    products = []
    for p in data["products"]:
        products.append((text(p["sku"], "sku"), text(p["category"], "category"),
                         integer(p["stock"], "stock"), integer(p["price_cents"], "price_cents")))
    with closing(sqlite3.connect(":memory:")) as db:
        db.execute("PRAGMA foreign_keys=ON")
        db.executescript("CREATE TABLE product(sku TEXT PRIMARY KEY, category TEXT, stock INT, price INT);"
                         "CREATE TABLE sale(sku TEXT REFERENCES product(sku), quantity INT);")
        db.executemany("INSERT INTO product VALUES(?,?,?,?)", products)
        for sale in data["sales"]:
            try:
                db.execute("INSERT INTO sale VALUES(?,?)",
                           (text(sale["sku"], "sku"), integer(sale["quantity"], "quantity", 1)))
            except sqlite3.IntegrityError as exc:
                raise ValueError("unknown product") from exc
        # Aggregate sales before joining, so stock is not multiplied by sales rows.
        rows = db.execute("""
          WITH sold AS (SELECT sku, SUM(quantity) qty FROM sale GROUP BY sku)
          SELECT p.category, SUM(COALESCE(s.qty,0)*p.price),
                 SUM(p.stock), SUM(CASE WHEN p.stock=0 THEN 1 ELSE 0 END)
          FROM product p LEFT JOIN sold s ON p.sku=s.sku
          GROUP BY p.category ORDER BY p.category
        """).fetchall()
    return {"categories": [dict(zip(("category", "revenue_cents", "stock_units", "out_of_stock_skus"), r))
                            for r in rows],
            "price_assumption": "fixed catalog price during this synthetic period"}
