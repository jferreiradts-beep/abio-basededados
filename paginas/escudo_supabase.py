import flet as ft
from supabase import create_client
from dotenv import load_dotenv
import os

# escudo_supabase (decorador) removido — tratamento de erros centralizado em main.py


def criar_cliente_supabase():
    load_dotenv()
    endereco = os.getenv("ENDERECO")
    chave = os.getenv("CHAVE")
    return create_client(endereco, chave)

def login_supabase(cliente=None):
    # Mantendo compatibilidade com código antigo se chamado sem argumentos (embora o ideal seja migrar)
    if cliente is None:
         cliente = criar_cliente_supabase()

    load_dotenv()
    usuario = os.getenv("USUARIO")
    senha = os.getenv("SENHA")
    
    try:
        cliente.auth.sign_in_with_password({ "email": usuario, "password": senha })
        return cliente
    except Exception as e:
        print(f"Erro no login automático: {e}")
        return cliente

class aviso():
    def __init__(self, page, aviso = 'Algum erro aconteceu'):
        self.page = page
        self.aviso = ft.Text(aviso)
        self.mostrar_aviso()

    def montar_aviso(self):
        return ft.AlertDialog(
            title=ft.Text("Atenção!"),
            content=ft.Container(
                width=300, height=100,
                content=ft.Column([self.aviso])
            ),
            actions=[
                ft.TextButton("Fechar", on_click=self.fechar_janela)
            ]
        )

    def mostrar_aviso(self):
        self.janela_aviso = self.montar_aviso()
        self.page.overlay.append(self.janela_aviso)
        self.janela_aviso.open = True
        self.page.update()

    def fechar_janela(self, e):
        self.janela_aviso.open = False
        self.page.update()