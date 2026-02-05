import os
from dotenv import load_dotenv
from supabase import create_client

import json

load_dotenv()
endereco = os.getenv("ENDERECO")
chave = os.getenv("CHAVE")
usuario = os.getenv("USUARIO")
senha = os.getenv("SENHA")

cliente = create_client(endereco, chave)
cliente.auth.sign_in_with_password({ "email": usuario, "password": senha })

resposta = cliente.rpc('fn_produtos_por_escopo', {'p_tipo': 3, 'p_escopo_id': 1}).execute()
resposta = resposta.data

with open('resposta.json', 'w') as arquivo:
    json.dump(resposta, arquivo, indent=4)