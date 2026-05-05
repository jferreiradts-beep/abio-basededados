import flet as ft
from dashboard import DashboardBase
from formulario_base import baseFormulario
from pag_matricula import MatriculaBase
from lista_produtos import baseProdutos
from escudo_supabase import escudo_supabase, login_supabase, criar_cliente_supabase
from pag_login import LoginBase
from pag_recuperar_senha import RecuperarSenhaBase
from grupo_dashboard import grupoBase
from pag_configuracoes import ConfiguracoesBase

def main(page: ft.Page):
    # Inicializa cliente sem logar automaticamente (agora o login é na tela)
    page.cliente = criar_cliente_supabase()
    page.voltar_dados = {'endereco': [], 'dados_pagina': []}
    page.avancar_dados = {}
    page.auth_user = None  # Cache para o usuário autenticado

    # Público: rotas que não precisam de login
    PUBLIC_ROUTES = ["/login", "/recuperar-senha", "/certificados/"]

    def route_change(route):
        import traceback

        # Rota raiz redireciona para o dashboard (auth check cuida do resto)
        if page.route == "/" or page.route == "":
            page.go("/dashboard")
            return
        
        # Verificar se o usuário está logado para rotas protegidas
        rota_publica = any(page.route == r or page.route.startswith(r) for r in PUBLIC_ROUTES)
        if not rota_publica:
            if page.auth_user is None:
                try:
                    sessao = page.cliente.auth.get_session()
                    if sessao:
                        page.auth_user = sessao.user
                    else:
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
            elif page.route == "/configuracoes":
                ConfiguracoesBase(page)
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

    # Tenta restaurar sessão salva no navegador (equivalente a cookies)
    def restaurar_sessao():
        try:
            access_token = page.client_storage.get("sb_access_token")
            refresh_token = page.client_storage.get("sb_refresh_token")
            if access_token and refresh_token:
                page.cliente.auth.set_session(access_token, refresh_token)
                sessao = page.cliente.auth.get_session()
                if sessao:
                    page.auth_user = sessao.user
                    print("[AUTH] Sessão restaurada do client_storage")
                    return True
        except Exception as e:
            print(f"[AUTH] Falha ao restaurar sessão: {e}")
            try:
                page.client_storage.remove("sb_access_token")
                page.client_storage.remove("sb_refresh_token")
            except Exception:
                pass
        return False

    # Lógica de entrada inicial
    if page.route == "/" or page.route == "" or page.route is None:
        if restaurar_sessao():
            page.go("/dashboard")
        else:
            page.go("/login")
    else:
        # Se veio com uma rota específica na URL, tenta restaurar sessão antes
        restaurar_sessao()
        page.on_route_change(page.route)


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8080))
    # Usando caminho absoluto para evitar bugs no servidor embutido dependendo do diretório de execução
    diretorio_assets = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
    ft.app(target=main, view=ft.AppView.WEB_BROWSER, port=port, host="0.0.0.0", assets_dir=diretorio_assets)