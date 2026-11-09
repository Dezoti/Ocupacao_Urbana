# Databricks notebook source
# MAGIC %md
# MAGIC # Bronze · Domicílios (Censo 2022, arquivos JSON da API IBGE)
# MAGIC A Free Edition não alcança a API do IBGE, então os JSONs são baixados com
# MAGIC `scripts/baixar_ibge.py` e depositados em
# MAGIC `/Volumes/<catalog>/bronze/landing/ibge_domicilios/`.
# MAGIC Este notebook ingere cada arquivo **inteiro, como texto**, com Auto Loader (incremental).

# COMMAND ----------

from pyspark.sql import functions as F

dbutils.widgets.text("catalog", "workspace")
catalog = dbutils.widgets.get("catalog")

base = f"/Volumes/{catalog}/bronze/landing"
origem = f"{base}/ibge_domicilios/"
checkpoint = f"{base}/_checkpoints/ibge_domicilios"

# COMMAND ----------

stream = (
    spark.readStream.format("cloudFiles")
    .option("cloudFiles.format", "text")
    .option("wholetext", "true")
    .load(origem)
    .withColumnRenamed("value", "conteudo")
    .withColumn("_ingestion_timestamp", F.current_timestamp())
    .withColumn("_source", F.lit("api.servicodados.ibge.gov.br (via arquivo)"))
    .withColumn("_source_file", F.col("_metadata.file_path"))
)

(
    stream.writeStream.option("checkpointLocation", checkpoint)
    .trigger(availableNow=True)
    .toTable(f"`{catalog}`.bronze.ibge_domicilios_raw")
    .awaitTermination()
)
