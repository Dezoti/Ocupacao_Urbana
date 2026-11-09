"""Configuração das fontes de dados.

ATENÇÃO: os números de agregado (tabela SIDRA) abaixo precisam ser validados com
`python scripts/baixar_ibge.py explorar|metadados` antes da primeira carga. Entradas com
`agregado = None` são ignoradas pela ingestão até serem preenchidas.
"""

IBGE_API = "https://servicodados.ibge.gov.br/api/v3/agregados"

# Cada fonte vira uma chamada à API de Dados Agregados do IBGE.
#   agregado       -> id da tabela SIDRA
#   variaveis      -> ids separados por "|" ou "all"
#   periodos       -> "2022", "-1" (último), "all" ou intervalo
#   classificacao  -> ex.: "2[all]" para todas as categorias da classificação 2
IBGE_FONTES = {
    # Documentação consultada cita a tabela 4712 como domicílios do Censo 2022.
    # Confirme variáveis e classificações no notebook de exploração.
    "censo2022_domicilios_ocupados": {
        "agregado": "4712",
        "variaveis": "all",
        "periodos": "2022",
        "classificacao": None,
        "validada": False,
    },
    # Domicílios vagos e de uso ocasional: localizar a tabela no notebook de
    # exploração (busca por "vagos" / "uso ocasional") e preencher aqui.
    "censo2022_domicilios_vagos_uso_ocasional": {
        "agregado": "9866",
        "variaveis": "all",
        "periodos": "2022",
        "classificacao": None,
        "validada": False,
    },
}

# Contrato de entrada do arquivo do CadÚnico / Observatório (população em
# situação de rua). Mapeie aqui os nomes das colunas do CSV real para os nomes
# usados no pipeline.
CADUNICO_COLUNAS = {
    "cod_ibge": "cod_ibge",      # código IBGE do município, 7 dígitos
    "ano": "ano",        # AAAAMM ou AAAA-MM
    "qtd_pop_rua": "qtd_pop_rua",  # nº de pessoas em situação de rua cadastradas
}
CADUNICO_SEPARADOR = ";"
