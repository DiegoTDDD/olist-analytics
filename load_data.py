import duckdb
import os

con = duckdb.connect("olist.duckdb")

raw_dir = "data/raw"

for filename in os.listdir(raw_dir):
    if filename.endswith(".csv"):
        table_name = filename.replace(".csv", "").replace("olist_", "").replace("_dataset", "")
        path = os.path.join(raw_dir, filename)
        con.execute(f"CREATE OR REPLACE TABLE {table_name} AS SELECT * FROM read_csv_auto('{path}')")
        print(f"Tabela criada: {table_name}")

print("\nTabelas no banco:")
print(con.execute("SHOW TABLES").fetchall())

con.close()