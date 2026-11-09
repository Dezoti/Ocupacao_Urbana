# Databricks notebook source
# MAGIC %md
# MAGIC # Bronze · População em situação de rua (CadÚnico / Observatório)
# MAGIC Ingestão incremental com Auto Loader dos CSVs depositados em
# MAGIC `/Volumes/<catalog>/bronze/landing/cadunico_pop_rua/`. Todas as colunas entram como texto.

# COMMAND ----------

import os
import sys

sys.path.append(os.path.abspath(".."))

from pyspark.sql import functions as F

from ocupacao.config import CADUNICO_SEPARADOR

dbutils.widgets.text("catalog", "workspace")
catalog = dbutils.widgets.get("catalog")

base = f"/Volumes/{catalog}/bronze/landing"
origem = f"{base}/cadunico_pop_rua/"
checkpoint = f"{base}/_checkpoints/cadunico_pop_rua"

# COMMAND ----------

stream = (
    spark.readStream.format("cloudFiles")
    .option("cloudFiles.format", "csv")
    .option("header", "true")
    .option("sep", CADUNICO_SEPARADOR)
    .option("cloudFiles.schemaLocation", checkpoint)
    .load(origem)
    .withColumn("_ingestion_timestamp", F.current_timestamp())
    .withColumn("_source", F.lit("cadunico_observatorio_ufmg"))
    .withColumn("_source_file", F.col("_metadata.file_path"))
)

(
    stream.writeStream.option("checkpointLocation", checkpoint)
    .option("mergeSchema", "true")
    .trigger(availableNow=True)
    .toTable(f"`{catalog}`.bronze.cadunico_pop_rua_raw")
    .awaitTermination()
)
