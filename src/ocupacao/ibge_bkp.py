"""Cliente e parser da API de Dados Agregados do IBGE (v3)."""

from __future__ import annotations

import json
import re
import unicodedata
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from ocupacao.config import IBGE_API

# Símbolos que o IBGE usa no lugar de números (ver documentação do SIDRA).
SIMBOLOS_SEM_VALOR = {"-", "..", "...", "X", ""}


def _sessao() -> requests.Session:
    s = requests.Session()
    retry = Retry(
        total=5,
        backoff_factor=1.5,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET",),
    )
    s.mount("https://", HTTPAdapter(max_retries=retry))
    return s


def montar_url(
    agregado: str,
    municipio_codigo: str,
    periodos: str = "all",
    variaveis: str = "all",
    classificacao: str | None = None,
) -> str:
    url = (
        f"{IBGE_API}/{agregado}/periodos/{periodos}/variaveis/{variaveis}"
        f"?localidades=N6[{municipio_codigo}]"
    )
    if classificacao:
        url += f"&classificacao={classificacao}"
    return url


def buscar(url: str, timeout: int = 60) -> list[dict[str, Any]]:
    """Faz GET e devolve o JSON já decodificado."""
    resp = _sessao().get(url, timeout=timeout)
    resp.raise_for_status()
    return resp.json()


def catalogo_agregados(pesquisa: str | None = None) -> list[dict[str, str]]:
    """Baixa o catálogo de tabelas (uma linha por tabela).

    `pesquisa` filtra no servidor por sigla da pesquisa (ex.: "CD" = Censo Demográfico).
    """
    url = IBGE_API if not pesquisa else f"{IBGE_API}?pesquisa={pesquisa}"
    return achatar_catalogo(buscar(url))


def achatar_catalogo(bruto: Any) -> list[dict[str, str]]:
    """Normaliza o JSON do catálogo, aceitando agrupado por pesquisa ou lista plana."""
    itens = bruto if isinstance(bruto, list) else []
    linhas = []
    for item in itens:
        if isinstance(item, dict) and "agregados" in item:
            for ag in item["agregados"]:
                linhas.append(
                    {
                        "pesquisa": str(item.get("nome") or item.get("id") or ""),
                        "id": str(ag.get("id", "")),
                        "nome": str(ag.get("nome", "")),
                    }
                )
        elif isinstance(item, dict) and "id" in item and "nome" in item:
            linhas.append({"pesquisa": "", "id": str(item["id"]), "nome": str(item["nome"])})
    return linhas


def filtrar_catalogo(catalogo: list[dict[str, str]], termos: list[str]) -> list[dict[str, str]]:
    """Mantém tabelas cujo nome contém QUALQUER um dos termos (sem acento, sem caixa)."""
    if not termos:
        return list(catalogo)
    termos_n = [_normalizar(t) for t in termos]
    return [a for a in catalogo if any(t in _normalizar(a["nome"]) for t in termos_n)]


def listar_agregados(termos: list[str], pesquisa: str | None = None) -> list[dict[str, str]]:
    """Atalho: baixa o catálogo e filtra pelos termos."""
    return filtrar_catalogo(catalogo_agregados(pesquisa), termos)


def _normalizar(texto: str) -> str:
    sem_acento = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return sem_acento.lower()


def para_numero(valor: Any) -> float | None:
    """Converte o valor textual do IBGE em número; símbolos viram None."""
    if valor is None:
        return None
    texto = str(valor).strip()
    if texto in SIMBOLOS_SEM_VALOR:
        return None
    try:
        return float(texto)
    except ValueError:
        return None


def classificar_domicilio(texto: str) -> str:
    """Mapeia o texto da categoria do IBGE para o tipo usado no projeto."""
    t = _normalizar(texto)
    if "uso ocasional" in t:
        return "uso_ocasional"
    if re.search(r"\bvagos?\b", t):
        return "vago"
    if re.search(r"\bocupados?\b", t):
        return "ocupado"
    return "outro"


def parse_agregados(payload: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Achata o JSON da API em linhas (uma por variável/categoria/local/período)."""
    linhas: list[dict[str, Any]] = []
    for var in payload:
        for res in var.get("resultados", []):
            categorias = {}
            for cl in res.get("classificacoes", []):
                nomes = list(cl.get("categoria", {}).values())
                categorias[cl.get("nome", cl.get("id", "?"))] = nomes[0] if nomes else None
            categoria_txt = " | ".join(f"{k}: {v}" for k, v in categorias.items())
            for serie in res.get("series", []):
                loc = serie.get("localidade", {})
                for periodo, valor in serie.get("serie", {}).items():
                    linhas.append(
                        {
                            "variavel_id": str(var.get("id")),
                            "variavel": var.get("variavel"),
                            "unidade": var.get("unidade"),
                            "classificacoes_json": json.dumps(categorias, ensure_ascii=False),
                            "categoria": categoria_txt,
                            "tipo_domicilio": classificar_domicilio(categoria_txt),
                            "localidade_id": str(loc.get("id")),
                            "localidade_nome": loc.get("nome"),
                            "nivel_id": loc.get("nivel", {}).get("id"),
                            "periodo": str(periodo),
                            "valor_raw": valor,
                            "valor": para_numero(valor),
                        }
                    )
    return linhas


def montar_envelope(
    fonte: str,
    agregado: str,
    municipio_codigo: str,
    url: str,
    payload: list[dict[str, Any]],
    baixado_em: str,
) -> dict[str, Any]:
    """Embrulha a resposta da API com metadados, para gravar como arquivo JSON."""
    return {
        "fonte": fonte,
        "agregado": agregado,
        "municipio_codigo": municipio_codigo,
        "url": url,
        "baixado_em": baixado_em,
        "payload": payload,
    }


def ler_envelope(texto: str) -> dict[str, Any]:
    """Lê o arquivo JSON gerado por `montar_envelope` e valida as chaves."""
    env = json.loads(texto)
    faltando = {"fonte", "municipio_codigo", "baixado_em", "payload"} - env.keys()
    if faltando:
        raise ValueError(f"Arquivo fora do formato esperado, faltam chaves: {sorted(faltando)}")
    return env
