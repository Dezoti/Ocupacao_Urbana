"""Gera o corpo da requisição para criar o dashboard no Databricks.

Evita problemas de aspas no terminal: o `databricks lakeview create` lê tudo de um arquivo.

Uso (a partir da raiz do repositório):
    python scripts/gerar_request_dashboard.py <ID_DO_WAREHOUSE> <userName>
    databricks lakeview create --dataset-catalog workspace --dataset-schema gold \
        --json @dashboards/request_dashboard.json
"""

import json
import sys
from pathlib import Path


def main() -> None:
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    warehouse_id, usuario = sys.argv[1], sys.argv[2]

    raiz = Path(__file__).resolve().parents[1]
    dashboard = (raiz / "dashboards" / "ocupacao_itajai.lvdash.json").read_text(encoding="utf-8")
    json.loads(dashboard)  # falha cedo se o JSON do dashboard estiver inválido

    corpo = {
        "display_name": "Ocupação urbana - Itajaí",
        "warehouse_id": warehouse_id,
        "parent_path": f"/Workspace/Users/{usuario}/dashboards",
        "serialized_dashboard": dashboard,
    }
    saida = raiz / "dashboards" / "request_dashboard.json"
    saida.write_text(json.dumps(corpo, ensure_ascii=False), encoding="utf-8")
    print(f"Arquivo gerado: {saida}")


if __name__ == "__main__":
    main()
