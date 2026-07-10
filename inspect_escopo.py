import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
endereco = os.getenv("ENDERECO")
chave = os.getenv("CHAVE")
cliente = create_client(endereco, chave)

# Login
usuario = os.getenv("USUARIO")
senha = os.getenv("SENHA")
try:
    if usuario and senha:
        cliente.auth.sign_in_with_password({ "email": usuario, "password": senha })
        print("Logged in successfully.")
except Exception as e:
    print(f"Login failed: {e}")

try:
    res = cliente.rpc("preencher_formulario", {"p_tabela": "escopo", "p_registro": 342}).execute()
    print("Raw response:", res)
    print("Data:", res.data)
except Exception as e:
    print("Error calling RPC:", e)
