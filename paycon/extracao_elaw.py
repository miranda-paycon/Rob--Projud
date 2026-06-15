import os
import sys
import requests
from datetime import datetime
import openpyxl

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import PAYCON_EMAIL, PAYCON_SENHA

PASTA_EXPORTACOES = os.path.join(os.path.dirname(os.path.dirname(__file__)), "temp", "exportacoes")
os.makedirs(PASTA_EXPORTACOES, exist_ok=True)

URL_BASE = "https://vgrcarrefour.paycon.com.br"
MODEL = "x_flow_elaw_tarefa"

CAMPOS = [
    "create_date",
    "x_id_elaw",
    "x_tarefa",
    "x_status_elaw",
    "x_pasta_id",
    "x_processo_numero",
    "x_qtd_cadastros",
    "x_responsavel",
    "x_setor_responsavel",
    "x_grupo_de_fase",
    "x_prazo",
]

CABECALHOS = [
    "Created on",
    "ID eLaw",
    "Tarefa",
    "Status eLaw",
    "Pasta",
    "Processo",
    "Qtd. Cadastros",
    "Responsável",
    "Setor Responsável",
    "Grupo de Fase",
    "Prazo",
]


def login(session):
    print("Realizando login via API...")
    resp = session.post(f"{URL_BASE}/web/session/authenticate", json={
        "jsonrpc": "2.0",
        "method": "call",
        "params": {
            "db": "vgrcarrefour",
            "login": PAYCON_EMAIL,
            "password": PAYCON_SENHA,
        }
    })
    result = resp.json().get("result", {})
    uid = result.get("uid")
    if not uid:
        raise Exception(f"Login falhou: {result}")
    print(f"Login OK! uid={uid}")
    return uid


def buscar_registros(session, offset=0, limit=80):
    resp = session.post(f"{URL_BASE}/web/dataset/call_kw", json={
        "jsonrpc": "2.0",
        "method": "call",
        "params": {
            "model": MODEL,
            "method": "search_read",
            "args": [[]],
            "kwargs": {
                "fields": CAMPOS,
                "limit": limit,
                "offset": offset,
                "order": "create_date desc",
            }
        }
    })
    return resp.json().get("result", [])


def contar_registros(session):
    resp = session.post(f"{URL_BASE}/web/dataset/call_kw", json={
        "jsonrpc": "2.0",
        "method": "call",
        "params": {
            "model": MODEL,
            "method": "search_count",
            "args": [[]],
            "kwargs": {}
        }
    })
    return resp.json().get("result", 0)


def formatar_valor(valor):
    if valor is False or valor is None:
        return ""
    if isinstance(valor, list):
        return valor[1] if len(valor) > 1 else str(valor[0])
    return str(valor)


def executar():
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})

    login(session)

    total = contar_registros(session)
    print(f"Total de registros: {total}")

    todos_dados = []
    offset = 0
    limit = 100

    while offset < total:
        print(f"Buscando registros {offset + 1} até {min(offset + limit, total)} de {total}...")
        registros = buscar_registros(session, offset=offset, limit=limit)
        if not registros:
            break
        for reg in registros:
            linha = [formatar_valor(reg.get(campo)) for campo in CAMPOS]
            todos_dados.append(linha)
        offset += limit

    # Salva no Excel
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    nome_arquivo = os.path.join(PASTA_EXPORTACOES, f"elaw_tarefas_{timestamp}.xlsx")

    print(f"Salvando {len(todos_dados)} registros no Excel...")
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "eLaw Tarefas"
    ws.append(CABECALHOS)
    for linha in todos_dados:
        ws.append(linha)

    wb.save(nome_arquivo)
    print(f"Arquivo salvo em: {nome_arquivo}")
    return nome_arquivo


if __name__ == "__main__":
    executar()
