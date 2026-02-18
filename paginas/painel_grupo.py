import flet as ft
import pandas as pd
from escudo_supabase import login_supabase, aviso


class dados():
    def __init__(self, page):
        self.page = page
        self.cliente = page.cliente
        self.id = page.session.get("id")
        dados_gerais, dados_escopos = self.baixar_dados()

    def baixar_dados(self):
        dados = self.cliente.rpc('preencher_formulario', {'p_tabela': 'grupo', 'p_registro': self.id}).execute()
        dados_escopos = self.cliente.table('vw_dados_com_associado').select('*').eq('id_grupo', f'g{self.id}').execute()
        return dados.data, dados_escopos

def iniciar_painel(tipo = 'grupo', id = 12):
    def main(page: ft.Page):
        page.cliente = login_supabase()
        page.session.set("tipo", tipo)
        page.session.set("id", id)
        page.avancar_dados = {}
        page.voltar_dados = {}
        
        basePainel(page)
    return main

if __name__ == "__main__":
    ft.app(target=iniciar_painel())
