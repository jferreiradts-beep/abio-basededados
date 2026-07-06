import flet as ft

class relatorioFinanceiroBase():
    def __init__(self, page: ft.Page):
        self.page = page
        self.montar_layout()

    def botoes_acoes(self, acao):
        if acao == 'voltar':
            retorno = self.page.voltar_dados['endereco'][-1] if self.page.voltar_dados['endereco'] else '/dashboard'
            voltar_dados = self.page.voltar_dados['dados_pagina'][-1] if self.page.voltar_dados['dados_pagina'] else None
            if voltar_dados:
                for chave, valor in voltar_dados.items():
                    self.page.session.set(chave, valor)

            if self.page.voltar_dados['endereco']:
                self.page.voltar_dados['endereco'].pop()
            if self.page.voltar_dados['dados_pagina']:
                self.page.voltar_dados['dados_pagina'].pop()

            self.page.go(retorno)

    def montar_linha_botoes(self):
        return ft.Column([
            ft.Container(
                height=60,
                width=1000,
                bgcolor=ft.Colors.GREY_200,
                border_radius=10,
                padding=10,
                content= ft.Row([
                    ft.ElevatedButton("Voltar", width=100, on_click=lambda e: self.botoes_acoes('voltar')),
                ], alignment=ft.MainAxisAlignment.END, spacing=20)
            )
        ])
        
    def montar_layout(self):
        # 1️⃣ Cabeçalho
        cabecalho = ft.Row([
            ft.Text("☰", size=24),  # menu placeholder
            ft.Text("SPG ABIO", size=24, weight="bold"),
        ], alignment=ft.MainAxisAlignment.START, spacing=20)

        # 2️⃣ Dados gerais (Vazio ou Título)
        dados_gerais = ft.Column([
            ft.Container(
                height= 100,
                width= 1000,
                bgcolor=ft.Colors.GREY_200,
                border_radius=10,
                padding=20,
                content= ft.Column([
                    ft.Text("Relatório Financeiro", size=20, weight="bold")
                ], alignment=ft.MainAxisAlignment.CENTER),
            ),
        ])

        # 3️⃣ Área central "Em construção"
        tabela = ft.Column([
                ft.Container(
                height= 400,
                width= 1000,
                clip_behavior=ft.ClipBehavior.HARD_EDGE,
                bgcolor=ft.Colors.GREY_200,
                border_radius=10,
                padding=20,
                content= ft.Column([
                    ft.Text("Em construção", size=24, color=ft.Colors.GREY_500, weight="bold")
                ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
                ),
        ])

        # 4️⃣ Botões
        linha_botoes = self.montar_linha_botoes()

        # Adicionar à pagina
        self.page.add(
            ft.Row([
                ft.Column([
                    cabecalho,
                    dados_gerais,
                    tabela,
                    linha_botoes],
                    spacing=20,
                    alignment=ft.MainAxisAlignment.START,
                    horizontal_alignment=ft.CrossAxisAlignment.START
                )
            ],
            spacing=20,
            alignment=ft.MainAxisAlignment.CENTER,
            vertical_alignment=ft.CrossAxisAlignment.CENTER
            )
        )

def iniciar_relatorio_financeiro():
    def main(page: ft.Page):
        from escudo_supabase import login_supabase
        page.cliente = login_supabase()
        page.avancar_dados = {}
        page.voltar_dados = {'endereco': [], 'dados_pagina': []}

        relatorioFinanceiroBase(page)
    return main

if __name__ == "__main__":
    ft.app(target=iniciar_relatorio_financeiro())
