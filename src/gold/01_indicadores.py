# Databricks notebook source
# MAGIC %md
# MAGIC # Gold · Indicadores
# MAGIC - `gold.ocupacao_municipio`: composição dos domicílios (ocupados, vagos, uso ocasional) por município/ano.
# MAGIC - `gold.pop_rua_serie`: série anual de pessoas em situação de rua.
# MAGIC - `gold.indicadores_municipio`: cruza a série anual com o estoque do Censo 2022.
# MAGIC
# MAGIC **Cuidado de interpretação:** o Censo é uma foto de 2022; a série do CadÚnico termina em 2021.
# MAGIC A razão vagos/pessoa usa sempre o estoque de 2022 e traz a coluna `defasagem_anos`.

# COMMAND ----------

dbutils.widgets.text("catalog", "workspace")
catalog = dbutils.widgets.get("catalog")

# COMMAND ----------

# MAGIC %md ## Composição dos domicílios

# COMMAND ----------

spark.sql(f"""
CREATE OR REPLACE TABLE `{catalog}`.gold.ocupacao_municipio
COMMENT 'Domicílios particulares permanentes por tipo (Censo 2022), por município e ano'
AS
WITH base AS (
  SELECT municipio_codigo, localidade_nome AS municipio, ano, tipo_domicilio, SUM(valor) AS qtd
  FROM `{catalog}`.silver.domicilios_censo
  WHERE tipo_domicilio IN ('ocupado', 'vago', 'uso_ocasional')
    AND valor IS NOT NULL
  GROUP BY ALL
),
piv AS (
  SELECT municipio_codigo, municipio, ano,
         SUM(CASE WHEN tipo_domicilio = 'ocupado'       THEN qtd END) AS domicilios_ocupados,
         SUM(CASE WHEN tipo_domicilio = 'vago'          THEN qtd END) AS domicilios_vagos,
         SUM(CASE WHEN tipo_domicilio = 'uso_ocasional' THEN qtd END) AS domicilios_uso_ocasional
  FROM base GROUP BY ALL
)
SELECT *,
  COALESCE(domicilios_ocupados,0) + COALESCE(domicilios_vagos,0) + COALESCE(domicilios_uso_ocasional,0) AS domicilios_total,
  ROUND(100 * domicilios_vagos
        / NULLIF(COALESCE(domicilios_ocupados,0) + COALESCE(domicilios_vagos,0) + COALESCE(domicilios_uso_ocasional,0), 0), 2) AS pct_vagos,
  ROUND(100 * domicilios_uso_ocasional
        / NULLIF(COALESCE(domicilios_ocupados,0) + COALESCE(domicilios_vagos,0) + COALESCE(domicilios_uso_ocasional,0), 0), 2) AS pct_uso_ocasional
FROM piv
""")

# COMMAND ----------

# MAGIC %md ## Série de pessoas em situação de rua

# COMMAND ----------

spark.sql(f"""
CREATE OR REPLACE TABLE `{catalog}`.gold.pop_rua_serie
COMMENT 'Pessoas em situação de rua no CadÚnico por município e ano'
AS
SELECT municipio_codigo, ano, qtd_pop_rua
FROM `{catalog}`.silver.pop_rua
""")

# COMMAND ----------

# MAGIC %md ## Indicador cruzado

# COMMAND ----------

spark.sql(f"""
CREATE OR REPLACE TABLE `{catalog}`.gold.indicadores_municipio
COMMENT 'Pessoas em situação de rua (anual) x domicílios vagos e de uso ocasional (Censo 2022)'
AS
SELECT p.municipio_codigo, o.municipio,
       p.ano AS ano_cadunico, p.qtd_pop_rua,
       o.ano AS ano_censo, o.ano - p.ano AS defasagem_anos,
       o.domicilios_vagos, o.domicilios_uso_ocasional, o.pct_vagos,
       ROUND(o.domicilios_vagos / NULLIF(p.qtd_pop_rua, 0), 2) AS vagos_por_pessoa_em_situacao_de_rua
FROM `{catalog}`.gold.pop_rua_serie p
JOIN `{catalog}`.gold.ocupacao_municipio o
  ON o.municipio_codigo = p.municipio_codigo
 AND o.ano = 2022
""")
