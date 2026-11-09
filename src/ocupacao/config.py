"""Configuração das fontes de dados.

Os agregados (tabelas SIDRA) abaixo foram conferidos com
`python scripts/baixar_ibge.py metadados <número>`. Entradas com `agregado = None`
são ignoradas pela ingestão.
"""

IBGE_API = "https://servicodados.ibge.gov.br/api/v3/agregados"

# Cada fonte vira uma chamada à API de Dados Agregados do IBGE.
#   agregado       -> id da tabela SIDRA
#   variaveis      -> ids separados por "|" ou "all"
#   periodos       -> "2022", "-1" (último), "all" ou intervalo
#   classificacao  -> ex.: "2[all]" para todas as categorias da classificação 2;
#                     várias classificações separadas por "|"
IBGE_FONTES = {
    # Tabela 4712: domicílios particulares permanentes ocupados (Censo 2022).
    # Variáveis: 381 domicílios, 382 moradores, 5930 média de moradores.
    "censo2022_domicilios_ocupados": {
        "agregado": "4712",
        "variaveis": "all",
        "periodos": "2022",
        "classificacao": None,
        "validada": True,
    },
    # Tabela 9866: domicílios não ocupados, por espécie e tipo de domicílio.
    # Variável 13063 = nº de domicílios (a 1013063 é o percentual, não entra).
    # Classificação 3 (Espécie): 486 = uso ocasional, 487 = vago.
    # Classificação 125 (Tipo de domicílio): 2932 = Total. Fixar o Total evita que as
    # linhas por tipo (casa, apartamento...) sejam somadas junto e inflem a contagem.
    "censo2022_domicilios_vagos_uso_ocasional": {
        "agregado": "9866",
        "variaveis": "13063",
        "periodos": "2022",
        "classificacao": "3[486,487]|125[2932]",
        "validada": True,
    },
}

# Contrato de entrada do CSV de população em situação de rua (CadÚnico, via
# Observatório da UFMG). O CSV é gerado por scripts/converter_pop_rua_observatorio.py.
# Série ANUAL (2012-2021). Mapeie aqui os nomes das colunas do CSV real.
CADUNICO_COLUNAS = {
    "cod_ibge": "cod_ibge",  # código IBGE do município, 7 dígitos
    "ano": "ano",  # ano de referência (AAAA)
    "qtd_pop_rua": "qtd_pop_rua",  # nº de pessoas em situação de rua cadastradas
}
CADUNICO_SEPARADOR = ";"
