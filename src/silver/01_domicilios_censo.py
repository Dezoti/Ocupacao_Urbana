# Databricks notebook source
# MAGIC %md
# MAGIC # Silver · Domicílios do Censo
# MAGIC Lê os arquivos JSON da bronze, mantém o **download mais recente** de cada (fonte, município),
# MAGIC achata com `ocupacao.ibge.parse_agregados` e grava a tabela tipada.
# MAGIC Reconstrução completa a cada execução, então é idempotente.

# COMMAND ----------

import os
import sys

sys.path.append(os.path.abspath(".."))

from pyspark.sql import functions as F
from pyspark.sql.types import DoubleType, StringType, StructField, StructType

from ocupacao import ibge

dbutils.widgets.text("catalog", "workspace")
catalog = dbutils.widgets.get("catalog")

# COMMAND ----------

bronze = spark.table(f"`{catalog}`.bronze.ibge_domicilios_raw").select("conteudo", "_source_file")

ultimos = {}  # (fonte, municipio) -> (envelope, arquivo)
for r in bronze.collect():
    env = ibge.ler_envelope(r["conteudo"])
    chave = (env["fonte"], env["municipio_codigo"])
    if chave not in ultimos or env["baixado_em"] > ultimos[chave][0]["baixado_em"]:
        ultimos[chave] = (env, r["_source_file"])

if not ultimos:
    raise RuntimeError("Bronze vazia: envie os JSONs para o Volume e rode a bronze antes.")

linhas = []
for env, arquivo in ultimos.values():
    for linha in ibge.parse_agregados(env["payload"]):
        linha.update(
            fonte=env["fonte"],
            municipio_codigo=env["municipio_codigo"],
            _source_file=arquivo,
        )
        linhas.append(linha)

# COMMAND ----------

schema = StructType(
    [
        StructField("fonte", StringType()),
        StructField("municipio_codigo", StringType()),
        StructField("variavel_id", StringType()),
        StructField("variavel", StringType()),
        StructField("unidade", StringType()),
        StructField("classificacoes_json", StringType()),
        StructField("categoria", StringType()),
        StructField("tipo_domicilio", StringType()),
        StructField("localidade_id", StringType()),
        StructField("localidade_nome", StringType()),
        StructField("nivel_id", StringType()),
        StructField("periodo", StringType()),
        StructField("valor_raw", StringType()),
        StructField("valor", DoubleType()),
        StructField("_source_file", StringType()),
    ]
)

df = (
    spark.createDataFrame(linhas, schema)
    .withColumn("ano", F.col("periodo").substr(1, 4).cast("int"))
    .withColumn("_processed_at", F.current_timestamp())
)

# Qualidade mínima: chaves não nulas
assert df.filter("municipio_codigo IS NULL OR periodo IS NULL").count() == 0, "chaves nulas"

(
    df.write.format("delta")
    .mode("overwrite")
    .option("overwriteSchema", "true")
    .saveAsTable(f"`{catalog}`.silver.domicilios_censo")
)

spark.sql(
    f"COMMENT ON TABLE `{catalog}`.silver.domicilios_censo IS "
    "'Domicílios do Censo 2022 (IBGE) por município, achatados a partir da API de Dados Agregados'"
)
