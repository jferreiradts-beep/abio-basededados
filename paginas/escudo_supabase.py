import flet as ft
import functools
from supabase import create_client
from dotenv import load_dotenv
import os

def escudo_supabase(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # 1. Tenta achar a 'page' dentro do 'self' (primeiro argumento)
        page = None
        if args and hasattr(args[0], 'page'):
            page = args[0].page
        
        # Se não achou a page, roda normal (sem proteção visual)
        if not page:
            return func(*args, **kwargs)

        # 3. Tenta rodar protegido
        try:
            return func(*args, **kwargs)
        except Exception as e:
            # Captura o traceback completo (arquivo, linha, etc.)
            import traceback
            error_trace = traceback.format_exc()
            print(f"Erro capturado pelo escudo: {e}")
            print(error_trace)  # Imprime no console também para facilitar

            page.clean()
            
            # Tenta recuperar de onde viemos (definido no dashboard), ou vai pro Início
            rota_retorno = page.session.get('voltar') or '/'
            
            page.add(
                ft.Column([
                    ft.Icon(ft.Icons.ERROR_OUTLINE, color="red", size=60),
                    ft.Text("Ops! Algo deu errado.", size=25, weight=ft.FontWeight.BOLD),
                    
                    # Mensagem curta do erro
                    ft.Container(
                        content=ft.Text(f"{str(e)}", color="white", weight=ft.FontWeight.BOLD),
                        bgcolor="red", padding=10, border_radius=5
                    ),

                    # Detalhes técnicos (traceback)
                    ft.Container(
                        content=ft.Column([
                            ft.Text("Detalhes técnicos:", weight=ft.FontWeight.BOLD),
                            ft.Text(error_trace, font_family="monospace", size=12, selectable=True)
                        ], scroll=ft.ScrollMode.ALWAYS),
                        height=300,
                        bgcolor=ft.Colors.GREY_200,
                        padding=10,
                        border_radius=5,
                        border=ft.border.all(1, ft.Colors.GREY_400)
                    ),

                    ft.ElevatedButton("Voltar", on_click=lambda _: page.go(rota_retorno))
                ], 
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                scroll=ft.ScrollMode.AUTO
                )
            )
            page.update()

    return wrapper


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