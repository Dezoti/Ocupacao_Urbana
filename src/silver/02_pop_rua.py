# Databricks notebook source
# MAGIC %md
# MAGIC # Silver · População em situação de rua
# MAGIC Renomeia colunas conforme `CADUNICO_COLUNAS`, tipa, filtra o município e deduplica
# MAGIC mantendo o registro mais recente por (município, ano). Série **anual**.

# COMMAND ----------

import os
import sys

sys.path.append(os.path.abspath(".."))

from pyspark.sql import Window
from pyspark.sql import functions as F

from ocupacao.config import CADUNICO_COLUNAS

dbutils.widgets.text("catalog", "workspace")
dbutils.widgets.text("municipio_codigo", "4208203")
catalog = dbutils.widgets.get("catalog")
municipio = dbutils.widgets.get("municipio_codigo")

# COMMAND ----------

if not spark.catalog.tableExists(f"{catalog}.bronze.cadunico_pop_rua_raw"):
    # Ainda não há CSV ingerido: cria a tabela vazia para a gold continuar funcionando.
    vazio = spark.createDataFrame(
        [],
        "municipio_codigo string, ano int, qtd_pop_rua long, "
        "_ingestion_timestamp timestamp, _source_file string",
    )
    (
        vazio.write.format("delta")
        .mode("overwrite")
        .option("overwriteSchema", "true")
        .saveAsTable(f"`{catalog}`.silver.pop_rua")
    )
    dbutils.notebook.exit("bronze sem dados: silver.pop_rua criada vazia")

raw = spark.table(f"`{catalog}`.bronze.cadunico_pop_rua_raw")

faltando = [c for c in CADUNICO_COLUNAS.values() if c not in raw.columns]
if faltando:
    raise ValueError(
        f"Colunas ausentes no CSV: {faltando}. Ajuste CADUNICO_COLUNAS em config.py. "
        f"Colunas encontradas: {raw.columns}"
    )

df = (
    raw.select(
        F.lpad(F.col(CADUNICO_COLUNAS["cod_ibge"]).cast("string"), 7, "0").alias("municipio_codigo"),
        F.col(CADUNICO_COLUNAS["ano"]).cast("int").alias("ano"),
        F.col(CADUNICO_COLUNAS["qtd_pop_rua"]).cast("long").alias("qtd_pop_rua"),
        "_ingestion_timestamp",
        "_source_file",
    )
    .filter(F.col("municipio_codigo") == municipio)
)

w = Window.partitionBy("municipio_codigo", "ano").orderBy(F.col("_ingestion_timestamp").desc())
df = df.withColumn("_rn", F.row_number().over(w)).filter("_rn = 1").drop("_rn")

# Qualidade mínima
assert df.filter("ano IS NULL OR qtd_pop_rua IS NULL OR qtd_pop_rua < 0").count() == 0, (
    "ano ou qtd_pop_rua inválidos"
)

(
    df.write.format("delta")
    .mode("overwrite")
    .option("overwriteSchema", "true")
    .saveAsTable(f"`{catalog}`.silver.pop_rua")
)

spark.sql(
    f"COMMENT ON TABLE `{catalog}`.silver.pop_rua IS "
    "'Pessoas em situação de rua no CadÚnico, por município e ano (Observatório UFMG, 2012-2021). "
    "Subestima o total real.'"
)
