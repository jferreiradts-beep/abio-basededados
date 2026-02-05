import flet as ft
from paginas.dashboard import DashboardBase
from paginas.formulario_base import baseFormulario
from paginas.pag_matricula import MatriculaBase
from paginas.lista_produtos import baseProdutos
from escudo_supabase import escudo_supabase, login_supabase

def main(page: ft.Page):
    page.cliente = login_supabase()
    page.voltar_dados = {'endereco': [], 'dados_pagina': []}
    page.avancar_dados = {}

    page.go('/dashboard')

    @escudo_supabase
    def route_change(route):
        page.clean()
        
        if page.route == "/dashboard": 
            DashboardBase(page)
        elif page.route == "/formulario":
            baseFormulario(page)
        elif page.route == "/matricula":
            MatriculaBase(page)
        elif page.route == "/produtos":
            baseProdutos(page)
        
        page.update()

    page.on_route_change = route_change
    page.go(page.route)


if __name__ == "__main__":
    ft.app(target=main)