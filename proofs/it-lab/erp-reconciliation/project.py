"""Reconcile a synthetic stock ledger and invoices; no Sage connector."""
from common import unique, integer, text

def analyze(data):
    stock = {text(k, "sku"): integer(v, "opening_stock") for k, v in data["opening_stock"].items()}
    unique(data["movements"], "id")
    for movement in data["movements"]:
        sku = text(movement["sku"], "sku")
        if sku not in stock or movement["kind"] not in ("receipt", "issue"):
            raise ValueError("unknown product or movement")
        qty = integer(movement["quantity"], "quantity", 1)
        stock[sku] += qty if movement["kind"] == "receipt" else -qty
        if stock[sku] < 0:
            raise ValueError("negative stock: movement rejected")
    unique(data["invoices"], "id")
    discrepancies = []
    for invoice in data["invoices"]:
        quantity = integer(invoice["quantity"], "quantity", 1)
        price = integer(invoice["unit_price_cents"], "unit_price_cents")
        actual = integer(invoice["total_cents"], "total_cents")
        expected = quantity * price
        if actual != expected:
            discrepancies.append({"id": invoice["id"], "expected_cents": expected,
                                  "actual_cents": actual, "difference_cents": actual-expected})
    return {"closing_stock": stock, "invoice_discrepancies": discrepancies,
            "scope": "Net amounts only; no VAT, currency conversion or accounting posting"}

