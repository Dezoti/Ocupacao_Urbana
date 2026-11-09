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
3. **Valide as tabelas do IBGE (na sua máquina, com internet).**
   `pip install requests`, depois `python scripts/baixar_ibge.py explorar vagos "uso ocasional"` e
   `python scripts/baixar_ibge.py metadados 4712`. Preencha `agregado` em `src/ocupacao/config.py`,
   principalmente a tabela de domicílios vagos e de uso ocasional (hoje `None`).
4. **Baixe e envie os dados.** `python scripts/baixar_ibge.py baixar --municipio 4208203` gera JSONs em `data/ibge/`.
   Envie-os para `/Volumes/<catalog>/bronze/landing/ibge_domicilios/` (pela interface do Catalog ou
   `databricks fs cp <arquivo> dbfs:/Volumes/<catalog>/bronze/landing/ibge_domicilios/`).
   Para a população em situação de rua, baixe `municipios_serie_historica_pop_rua.xlsx` no [repositório do Observatório](https://obpoprua.direito.ufmg.br/repositorio_dados_tabelas.html), converta com `python scripts/converter_pop_rua_observatorio.py <xlsx> cadunico_pop_rua.csv` (precisa de `pip install openpyxl`) e envie o CSV para `.../cadunico_pop_rua/`.
   As pastas e o volume são criados pelo notebook `src/00_setup.py` (primeira task do job).
5. **Rode o job:** `databricks bundle run pipeline_ocupacao -t free`.
6. **Dashboard:** teste as consultas de `dashboards/queries.sql` no editor SQL e crie o dashboard a partir de `dashboards/ocupacao_itajai.lvdash.json`:
   ```bash
   databricks warehouses list                  # anote o ID do warehouse
   databricks current-user me                  # anote o userName
   databricks workspace mkdirs /Workspace/Users/<userName>/dashboards
   python scripts/gerar_request_dashboard.py <ID_DO_WAREHOUSE> <userName>
   databricks lakeview create --dataset-catalog workspace --dataset-schema gold --json @dashboards/request_dashboard.json
   ```
   O `create` devolve o `dashboard_id`. Publique com `databricks lakeview publish <ID> --warehouse-id <ID_DO_WAREHOUSE>`.

## Desenvolvimento
```bash
pip install -e ".[dev]"
ruff check .
pytest
```
Fluxo: branch de feature → pull request (CI roda lint, testes e `bundle validate`) → merge em `main` (deploy).

Secrets necessários no GitHub: `DATABRICKS_HOST` e `DATABRICKS_TOKEN`. Na Free Edition, confirme se é possível gerar token; se não for, faça o deploy manualmente (`databricks bundle deploy`) e deixe o CI só com lint e testes.

## Status
- [x] Estrutura, parser da API, notebooks, CI/CD
- [ ] Validar números de tabela SIDRA (ver `config.py`)
- [x] CSV de população em situação de rua (série anual 2012-2021, Observatório UFMG)
- [x] Catálogo `workspace` e ambiente único configurados
- [x] Dashboard em `dashboards/ocupacao_itajai.lvdash.json` (ainda não criado no workspace)
- [ ] Notebooks ainda não foram executados em um workspace real
