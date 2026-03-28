import flet as ft
from dashboard import DashboardBase
from formulario_base import baseFormulario
from pag_matricula import MatriculaBase
from lista_produtos import baseProdutos
from escudo_supabase import escudo_supabase, login_supabase, criar_cliente_supabase
from pag_login import LoginBase
from pag_recuperar_senha import RecuperarSenhaBase
from grupo_dashboard import grupoBase

def main(page: ft.Page):
    # Inicializa cliente sem logar automaticamente (agora o login é na tela)
    page.cliente = criar_cliente_supabase()
    page.voltar_dados = {'endereco': [], 'dados_pagina': []}
    page.avancar_dados = {}

    # Público: rotas que não precisam de login
    PUBLIC_ROUTES = ["/login", "/recuperar-senha"]  

    def route_change(route):
        import traceback
        
        # Verificar se o usuário está logado para rotas protegidas
        rota_publica = any(page.route == r or page.route.startswith(r + "?") for r in PUBLIC_ROUTES)
        if not rota_publica:
            try:
                sessao = page.cliente.auth.get_session()
                if not sessao:
                    print(f"[AUTH] Usuário não logado. Redirecionando de {page.route} para /login")
                    page.go("/login")
                    return
            except Exception as e:
                print(f"[AUTH] Erro ao verificar sessão: {e}")
                page.go("/login")
                return

        try:
            page.clean()
            
            if page.route == "/login":
                LoginBase(page)
            elif page.route == "/dashboard": 
                DashboardBase(page)
            elif page.route == "/formulario":
                baseFormulario(page)
            elif page.route == "/matricula":
                MatriculaBase(page)
            elif page.route == "/produtos":
                baseProdutos(page)
            elif page.route == "/painel_grupo":
                grupoBase(page)
            elif page.route == "/recuperar-senha" or page.route.startswith("/recuperar-senha?"):
                RecuperarSenhaBase(page)
            page.update()
        except Exception as e:
            error_trace = traceback.format_exc()
            page.clean()
            page.add(
                ft.Column([
                    ft.Icon(ft.Icons.ERROR_OUTLINE, color="red", size=60),
                    ft.Text("Ops! Algo deu errado.", size=25, weight=ft.FontWeight.BOLD),
                    ft.Container(
                        content=ft.Text(f"{str(e)}", color="white", weight=ft.FontWeight.BOLD),
                        bgcolor="red", padding=10, border_radius=5
                    ),
                    ft.Container(
                        content=ft.Column([
                            ft.Text("Detalhes técnicos:", weight=ft.FontWeight.BOLD),
                            ft.Text(error_trace, font_family="monospace", size=12, selectable=True)
                        ], scroll=ft.ScrollMode.ALWAYS),
                        height=300,
                        bgcolor=ft.Colors.GREY_200,
                        padding=10,
                        border_radius=5,
                    ),
                    ft.ElevatedButton("Voltar", on_click=lambda _: page.go("/dashboard"))
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                scroll=ft.ScrollMode.AUTO
                )
            )
            page.update()

    page.on_route_change = route_change
    
    # Lógica de entrada inicial
    if page.route == "/" or page.route == "" or page.route is None:
        page.go("/login")
    else:
        # Se veio com uma rota específica na URL (ex: /dashboard ou /recuperar-senha)
        # chamamos o route_change manualmente para processar a página atual
        page.on_route_change(page.route)


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8080))
    # Usando caminho absoluto para evitar bugs no servidor embutido dependendo do diretório de execução
    diretorio_assets = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
    ft.app(target=main, view=ft.AppView.WEB_BROWSER, port=port, host="0.0.0.0", assets_dir=diretorio_assets)