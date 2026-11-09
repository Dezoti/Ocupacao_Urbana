# Ocupação urbana: imóveis ocupados e vagos x pessoas em situação de rua

Pipeline em Databricks (arquitetura medalhão) que cruza domicílios ocupados, vagos e de uso ocasional (Censo 2022, IBGE)
com a população em situação de rua (CadÚnico). Recorte inicial: **Itajaí-SC (4208203)**; o município é um parâmetro.

```
API IBGE ──(script local)──► JSON no Volume ──► bronze.ibge_domicilios_raw ──► silver.domicilios_censo ──┐
                                                                       ├─► gold.* ─► Dashboard
CSV CadÚnico ──► bronze.cadunico_pop_rua_raw ──► silver.pop_rua ───────┘
```

## Estrutura
```
databricks.yml            bundle (ambiente único `free`, catálogo `workspace`)
resources/pipeline_job.yml  job: setup → bronze → silver → gold
resources/dashboard.yml   dashboard como recurso do bundle
src/ocupacao/             código Python testável (cliente e parser da API)
scripts/baixar_ibge.py    baixa os dados do IBGE na sua máquina (a Free Edition bloqueia a API)
src/{bronze,silver,gold}/ notebooks do pipeline
dashboards/                dashboard (JSON do Lakeview) e consultas para teste
tests/                    pytest
docs/                     dicionário de dados e limitações
```

## Primeiros passos
1. **Pré-requisito:** workspace com Unity Catalog e um catálogo. Na Databricks Free Edition (um único workspace, só serverless, sem acesso à API do IBGE) use o catálogo `workspace` (já é o padrão em `databricks.yml`).
2. **Instale e autentique o Databricks CLI**, depois: `databricks auth login --host <url-do-workspace>`. O host não fica no `databricks.yml`: o CLI usa o perfil do login (se tiver mais de um perfil, acrescente `-p <perfil>` aos comandos).
3. **Tabelas do IBGE (já validadas).** `src/ocupacao/config.py` usa as tabelas SIDRA 4712 (domicílios ocupados) e 9866 (vagos e de uso ocasional) do Censo 2022.
   Para explorar outras: `pip install requests`, depois `python scripts/baixar_ibge.py explorar vagos "uso ocasional"` e `python scripts/baixar_ibge.py metadados <agregado>`.
4. **Baixe e envie os dados.** `python scripts/baixar_ibge.py baixar --municipio 4208203` gera JSONs em `data/ibge/`.
   Envie-os para `/Volumes/<catalog>/bronze/landing/ibge_domicilios/` (pela interface do Catalog ou
   `databricks fs cp <arquivo> dbfs:/Volumes/<catalog>/bronze/landing/ibge_domicilios/`).
   Para a população em situação de rua, baixe `municipios_serie_historica_pop_rua.xlsx` no [repositório do Observatório](https://obpoprua.direito.ufmg.br/repositorio_dados_tabelas.html), converta com `python scripts/converter_pop_rua_observatorio.py <xlsx> cadunico_pop_rua.csv` (precisa de `pip install openpyxl`) e envie o CSV para `.../cadunico_pop_rua/`.
   As pastas e o volume são criados pelo notebook `src/00_setup.py` (primeira task do job).
5. **Rode o job:** `databricks bundle run pipeline_ocupacao -t free`.
6. **Dashboard:** teste as consultas de `dashboards/queries.sql` no editor SQL. O dashboard é um recurso do bundle (`resources/dashboard.yml`, a partir de `dashboards/ocupacao_itajai.lvdash.json`) e é criado e publicado no `databricks bundle deploy -t free`.
   O warehouse fica na variável `warehouse_id` (`databricks warehouses list` mostra o ID; ajuste em `databricks.yml`).
   Para editar: altere o dashboard no workspace, rode `databricks bundle generate dashboard --existing-id <ID> --resource ocupacao_itajai --dashboard-dir dashboards --force` (ou edite o JSON) e faça um novo deploy.

## Desenvolvimento
```bash
pip install -e ".[dev]"
ruff check .
pytest
```
Fluxo: branch de feature → pull request (o CI roda lint e testes) → merge em `main`.

O deploy no Databricks é manual: `databricks bundle deploy -t free`, seguido de `databricks bundle run pipeline_ocupacao -t free`.
O workflow `.github/workflows/deploy.yml` só roda sob demanda (`workflow_dispatch`) e exige os secrets `DATABRICKS_HOST` e `DATABRICKS_TOKEN`, que podem não estar disponíveis na Free Edition.

## Status
- [x] Estrutura, parser da API, notebooks e CI (lint + testes)
- [x] Tabelas SIDRA 4712 e 9866 validadas (Censo 2022)
- [x] População em situação de rua: série anual 2012-2021 (Observatório UFMG, CadÚnico)
- [x] Catálogo `workspace` e ambiente único configurados
- [x] Pipeline executado de ponta a ponta no workspace (bronze → silver → gold)
- [x] Dashboard criado no workspace a partir de `dashboards/ocupacao_itajai.lvdash.json`
- [x] Dashboard como recurso do bundle (criado e publicado no deploy)
- [ ] Agendamento do job (depende da Free Edition)
- [ ] Fonte mais recente de população em situação de rua (a série vai só até 2021)
- [ ] Outros municípios

## Limitações
- A série de população em situação de rua termina em 2021 e subestima a realidade; o Censo 2022 é de outro ano (ver `defasagem_anos` na tabela `gold.indicadores_municipio`).
- A Free Edition bloqueia o acesso à API do IBGE; por isso o download é feito localmente e os JSONs são enviados ao Volume.
