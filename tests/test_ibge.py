from ocupacao.ibge import (
    classificar_domicilio,
    montar_url,
    para_numero,
    parse_agregados,
)

PAYLOAD = [
    {
        "id": "93",
        "variavel": "Domicílios",
        "unidade": "Unidades",
        "resultados": [
            {
                "classificacoes": [
                    {"id": "1", "nome": "Espécie", "categoria": {"100": "Vagos"}}
                ],
                "series": [
                    {
                        "localidade": {
                            "id": "4208203",
                            "nivel": {"id": "N6", "nome": "Município"},
                            "nome": "Itajaí - SC",
                        },
                        "serie": {"2022": "12345", "2010": "-"},
                    }
                ],
            },
            {
                "classificacoes": [
                    {"id": "1", "nome": "Espécie", "categoria": {"101": "Uso ocasional"}}
                ],
                "series": [
                    {
                        "localidade": {
                            "id": "4208203",
                            "nivel": {"id": "N6", "nome": "Município"},
                            "nome": "Itajaí - SC",
                        },
                        "serie": {"2022": "999"},
                    }
                ],
            },
        ],
    }
]


def test_para_numero():
    assert para_numero("123") == 123.0
    assert para_numero("1.5") == 1.5
    for simbolo in ("-", "..", "...", "X", "", None, "abc"):
        assert para_numero(simbolo) is None


def test_classificar_domicilio():
    assert classificar_domicilio("Espécie: Vagos") == "vago"
    assert classificar_domicilio("Espécie: Uso ocasional") == "uso_ocasional"
    assert classificar_domicilio("Particular permanente ocupado") == "ocupado"
    assert classificar_domicilio("Coletivo") == "outro"
    assert classificar_domicilio("Total") == "outro"
    # "desocupado" não pode ser tratado como "ocupado"
    assert classificar_domicilio("Domicílio desocupado") == "outro"


def test_parse_agregados():
    linhas = parse_agregados(PAYLOAD)
    assert len(linhas) == 3
    vago_2022 = next(
        x for x in linhas if x["tipo_domicilio"] == "vago" and x["periodo"] == "2022"
    )
    assert vago_2022["valor"] == 12345.0
    assert vago_2022["localidade_id"] == "4208203"
    assert vago_2022["nivel_id"] == "N6"
    sem_valor = next(x for x in linhas if x["periodo"] == "2010")
    assert sem_valor["valor"] is None and sem_valor["valor_raw"] == "-"
    assert any(x["tipo_domicilio"] == "uso_ocasional" for x in linhas)


def test_montar_url():
    url = montar_url("4712", "4208203", periodos="2022", classificacao="1[all]")
    assert url.endswith("?localidades=N6[4208203]&classificacao=1[all]")
    assert "/4712/periodos/2022/variaveis/all" in url


def test_envelope_ida_e_volta():
    from ocupacao.ibge import ler_envelope, montar_envelope

    env = montar_envelope("fonte_x", "4712", "4208203", "http://x", PAYLOAD, "2026-11-05T12:00:00")
    import json

    lido = ler_envelope(json.dumps(env))
    assert lido["fonte"] == "fonte_x"
    assert len(parse_agregados(lido["payload"])) == 3


def test_envelope_invalido():
    import pytest

    from ocupacao.ibge import ler_envelope

    with pytest.raises(ValueError):
        ler_envelope('{"payload": []}')


CATALOGO_AGRUPADO = [
    {
        "id": "CD",
        "nome": "Censo Demográfico",
        "agregados": [
            {"id": "4712", "nome": "Domicílios particulares permanentes, por espécie"},
            {"id": "9999", "nome": "Domicílios VAGOS e de uso ocasional"},
        ],
    },
    {"id": "PA", "nome": "Pesquisa X", "agregados": [{"id": "1", "nome": "Outra coisa"}]},
]


def test_catalogo_e_filtro():
    from ocupacao.ibge import achatar_catalogo, filtrar_catalogo

    cat = achatar_catalogo(CATALOGO_AGRUPADO)
    assert len(cat) == 3 and cat[0]["pesquisa"] == "Censo Demográfico"
    assert [a["id"] for a in filtrar_catalogo(cat, ["vagos"])] == ["9999"]
    assert [a["id"] for a in filtrar_catalogo(cat, ["DOMICILIOS"])] == ["4712", "9999"]
    assert len(filtrar_catalogo(cat, [])) == 3


def test_catalogo_lista_plana_e_formato_inesperado():
    from ocupacao.ibge import achatar_catalogo

    assert achatar_catalogo([{"id": 5, "nome": "Tabela"}]) == [
        {"pesquisa": "", "id": "5", "nome": "Tabela"}
    ]
    assert achatar_catalogo({"erro": "x"}) == []
