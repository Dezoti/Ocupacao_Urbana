# Databricks notebook source
# MAGIC %md
# MAGIC # 00 · Setup
# MAGIC Cria schemas (bronze/silver/gold) e o volume de aterrissagem de arquivos.
# MAGIC O catálogo precisa existir e o usuário/service principal precisa de `USE CATALOG` e `CREATE SCHEMA`.

# COMMAND ----------

dbutils.widgets.text("catalog", "workspace")
catalog = dbutils.widgets.get("catalog")

# COMMAND ----------

for schema in ("bronze", "silver", "gold"):
    spark.sql(f"CREATE SCHEMA IF NOT EXISTS `{catalog}`.{schema}")

# Volume onde o CSV do CadÚnico/Observatório é depositado manualmente
spark.sql(f"CREATE VOLUME IF NOT EXISTS `{catalog}`.bronze.landing")

base = f"/Volumes/{catalog}/bronze/landing"
for pasta in ("ibge_domicilios", "cadunico_pop_rua"):
    dbutils.fs.mkdirs(f"{base}/{pasta}")

print(f"Pronto. Envie os arquivos para {base}/ibge_domicilios/ e {base}/cadunico_pop_rua/")
