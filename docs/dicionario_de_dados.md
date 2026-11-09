# Dicionário de dados

## Bronze
| Tabela | Descrição |
|---|---|
| `bronze.ibge_domicilios_raw` | Arquivos JSON (gerados por `scripts/baixar_ibge.py`) com a resposta da API de Dados Agregados do IBGE, 1 linha por arquivo (`conteudo`). Colunas de controle: `_ingestion_timestamp`, `_source`, `_source_file`. |
| `bronze.cadunico_pop_rua_raw` | CSV do CadÚnico/Observatório carregado via Auto Loader, tudo como texto. Colunas de controle: `_ingestion_timestamp`, `_source`, `_source_file`. |

## Silver
| Tabela | Chave | Descrição |
|---|---|---|
| `silver.domicilios_censo` | fonte, variavel_id, categoria, localidade_id, periodo | Domicílios do Censo achatados. `tipo_domicilio` ∈ ocupado, vago, uso_ocasional, outro. `valor` é nulo quando o IBGE retorna símbolo (`-`, `..`, `...`, `X`). |
| `silver.pop_rua` | municipio_codigo, ano_mes | Pessoas em situação de rua no CadÚnico. |

## Gold
| Tabela | Descrição |
|---|---|
| `gold.ocupacao_municipio` | Ocupados, vagos, uso ocasional, total e percentuais por município/ano. |
| `gold.pop_rua_serie` | Série mensal de pessoas em situação de rua. |
| `gold.indicadores_municipio` | Série mensal x estoque do Censo 2022: `vagos_por_pessoa_em_situacao_de_rua`. |

## Limitações
- O Censo é uma foto de 2022; o CadÚnico é mensal e **subestima** a população em situação de rua (depende de abordagem do poder público).
- "Vago" e "uso ocasional" são categorias distintas do IBGE. Em cidades litorâneas, uso ocasional (veraneio) não equivale a imóvel ocioso.
- Números de tabela SIDRA em `src/ocupacao/config.py` marcados como `validada: False` precisam ser conferidos antes da primeira carga.
- Não carregue dados pessoais (nome de proprietário em cadastro de IPTU, por exemplo): LGPD.
