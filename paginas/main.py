import flet as ft
from dashboard import DashboardBase
from formulario_base import baseFormulario
from pag_matricula import MatriculaBase
from lista_produtos import baseProdutos
from escudo_supabase import escudo_supabase, login_supabase, criar_cliente_supabase
from pag_login import LoginBase
from pag_recuperar_senha import RecuperarSenhaBase

def main(page: ft.Page):
    # Inicializa cliente sem logar automaticamente (agora o login é na tela)
    page.cliente = criar_cliente_supabase()
    page.voltar_dados = {'endereco': [], 'dados_pagina': []}
    page.avancar_dados = {}

    page.go('/login')

    @escudo_supabase
    def route_change(route):
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
        elif page.route == "/recuperar-senha":
            RecuperarSenhaBase(page)
        
        page.update()

    page.on_route_change = route_change
    page.go(page.route)


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8080))
    ft.app(target=main, view=ft.AppView.WEB_BROWSER, port=port, host="0.0.0.0")