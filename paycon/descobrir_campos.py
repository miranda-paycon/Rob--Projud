import sys
import os
import requests
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import PAYCON_EMAIL, PAYCON_SENHA

URL_BASE = "https://vgrcarrefour.paycon.com.br"
MODEL = "x_flow_elaw_tarefa"

session = requests.Session()
session.headers.update({"Content-Type": "application/json"})

# Login
session.post(f"{URL_BASE}/web/session/authenticate", json={
    "jsonrpc": "2.0", "method": "call",
    "params": {"db": "vgrcarrefour", "login": PAYCON_EMAIL, "password": PAYCON_SENHA}
})

# Busca 1 registro para ver os campos disponíveis
resp = session.post(f"{URL_BASE}/web/dataset/call_kw", json={
    "jsonrpc": "2.0", "method": "call",
    "params": {
        "model": MODEL, "method": "search_read",
        "args": [[]],
        "kwargs": {"limit": 1, "offset": 0}
    }
})

resultado = resp.json().get("result", [])
if resultado:
    print("Campos disponíveis:")
    for campo, valor in resultado[0].items():
        print(f"  {campo}: {repr(valor)[:80]}")
else:
    print("Sem resultado:", resp.json())
