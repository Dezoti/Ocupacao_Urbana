"""Baixa dados da API do IBGE na sua máquina.

A Databricks Free Edition bloqueia a saída de rede para a API do IBGE, então a
coleta roda aqui e os arquivos JSON são enviados ao Volume do Databricks.

Uso (a partir da raiz do repositório):
    pip install requests
    python scripts/baixar_ibge.py explorar vagos "uso ocasional"
    python scripts/baixar_ibge.py metadados 4712
    python scripts/baixar_ibge.py baixar --municipio 4208203
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ocupacao import ibge  # noqa: E402
from ocupacao.config import IBGE_FONTES  # noqa: E402


def cmd_explorar(args: argparse.Namespace) -> None:
    catalogo = ibge.catalogo_agregados(args.pesquisa)
    print(f"Catálogo carregado: {len(catalogo)} tabelas", file=sys.stderr)
    if not catalogo:
        sys.exit(
            "A API respondeu, mas o catálogo veio vazio ou em formato inesperado. "
            "Tente sem --pesquisa, ou use o comando `metadados <número>` com um número "
            "de tabela que você achou no site do SIDRA."
        )
    achados = ibge.filtrar_catalogo(catalogo, args.termos)
    if not achados:
        print(
            f"Nenhuma tabela contém {args.termos}. Tente termos mais curtos, por exemplo:",
            file=sys.stderr,
        )
        print("  explorar ocupa\n  explorar domicilios --pesquisa CD", file=sys.stderr)
    for ag in achados:
        print(f"{ag['id']:>6}  {ag['nome']}  [{ag['pesquisa']}]")


def cmd_metadados(args: argparse.Namespace) -> None:
    meta = ibge.buscar(f"{ibge.IBGE_API}/{args.agregado}/metadados")
    print(meta["nome"])
    print("Níveis territoriais:", meta["nivelTerritorial"])
    print("\nVariáveis:")
    for v in meta["variaveis"]:
        print(f"  {v['id']}: {v['nome']}")
    print("\nClassificações:")
    for c in meta["classificacoes"]:
        print(f"  {c['id']}: {c['nome']}")
        for k in c["categorias"][:20]:
            print(f"      {k['id']}: {k['nome']}")


def cmd_baixar(args: argparse.Namespace) -> None:
    destino = Path(args.saida)
    destino.mkdir(parents=True, exist_ok=True)
    agora = datetime.now(timezone.utc)
    baixados = 0
    for nome, cfg in IBGE_FONTES.items():
        if not cfg["agregado"]:
            print(f"[ignorada] {nome}: agregado não configurado em config.py")
            continue
        url = ibge.montar_url(
            cfg["agregado"], args.municipio, cfg["periodos"], cfg["variaveis"], cfg["classificacao"]
        )
        payload = ibge.buscar(url)
        env = ibge.montar_envelope(
            nome, cfg["agregado"], args.municipio, url, payload, agora.isoformat()
        )
        arquivo = destino / f"{nome}_{args.municipio}_{agora:%Y%m%dT%H%M%S}.json"
        arquivo.write_text(json.dumps(env, ensure_ascii=False), encoding="utf-8")
        print(f"[ok] {arquivo}")
        baixados += 1
    if not baixados:
        sys.exit("Nenhuma fonte configurada. Preencha IBGE_FONTES em src/ocupacao/config.py.")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    e = sub.add_parser("explorar", help="busca tabelas pelo nome")
    e.add_argument("termos", nargs="*", help="termos (basta um coincidir); vazio lista tudo")
    e.add_argument(
        "--pesquisa", default=None, help="sigla da pesquisa, ex.: CD (Censo Demográfico)"
    )
    e.set_defaults(func=cmd_explorar)

    m = sub.add_parser("metadados", help="mostra variáveis e classificações de uma tabela")
    m.add_argument("agregado")
    m.set_defaults(func=cmd_metadados)

    b = sub.add_parser("baixar", help="baixa as fontes configuradas em config.py")
    b.add_argument("--municipio", default="4208203")
    b.add_argument("--saida", default="data/ibge")
    b.set_defaults(func=cmd_baixar)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
