-- Consultas dos datasets de dashboards/ocupacao_itajai.lvdash.json, com o nome completo
-- das tabelas para você testar no editor SQL do Databricks ANTES de criar o dashboard.
-- (Dentro do JSON as consultas usam só o nome da tabela; o catálogo e o schema são
-- informados na criação com --dataset-catalog workspace --dataset-schema gold.)

-- ds_ocupacao: 1 linha com ocupados, vagos, uso ocasional e taxa de vagos
SELECT municipio, ano, domicilios_ocupados, domicilios_vagos, domicilios_uso_ocasional,
       domicilios_total, pct_vagos / 100.0 AS taxa_vagos
FROM workspace.gold.ocupacao_municipio;

-- ds_composicao: 3 linhas (Ocupados, Vagos, Uso ocasional)
SELECT 'Ocupados' AS tipo, domicilios_ocupados AS qtd FROM workspace.gold.ocupacao_municipio
UNION ALL SELECT 'Vagos', domicilios_vagos FROM workspace.gold.ocupacao_municipio
UNION ALL SELECT 'Uso ocasional', domicilios_uso_ocasional FROM workspace.gold.ocupacao_municipio;

-- ds_pop_rua: uma linha por ano (2012-2021)
SELECT CAST(ano AS STRING) AS ano, qtd_pop_rua
FROM workspace.gold.pop_rua_serie
ORDER BY ano;

-- ds_indicadores: uma linha por ano, com a defasagem até o Censo de 2022
SELECT CAST(ano_cadunico AS STRING) AS ano_cadunico, qtd_pop_rua, defasagem_anos,
       domicilios_vagos, domicilios_uso_ocasional,
       vagos_por_pessoa_em_situacao_de_rua AS vagos_por_pessoa
FROM workspace.gold.indicadores_municipio
ORDER BY ano_cadunico;
