from pathlib import Path

import duckdb

con = duckdb.connect(str(Path(__file__).resolve().parents[1] / "olist.duckdb"), read_only=True)

tabelas = ["orders", "customers", "order_items", "order_payments", "order_reviews", "products", "sellers"]
print("Contagem de linhas por tabela:")
for t in tabelas:
    n = con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
    print(f"  {t}: {n:,} linhas")

print("\nAmostra da tabela orders:")
print(con.execute("SELECT * FROM orders LIMIT 5").fetchdf())

con.close()
