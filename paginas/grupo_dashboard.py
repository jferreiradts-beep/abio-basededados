import flet as ft
import pandas as pd
from datetime import date, datetime
from formulario_coluna2 import verAcontecimentos
from escudo_supabase import login_supabase, aviso

class quadroTabela():
    # Mapeamento índice → chave do dict de dados
    COLUNAS = [
        ('matricula',         'Matrícula'),
        ('primeiro_associado','Primeiro Associado'),
        ('escopo',            'Escopo'),
        ('validade',          'Validade'),
        ('ultimo_movimento',  'Último\nMovimento'),
        (None,                'Ações'),          # não ordenável
    ]

    def __init__(self, page, dados, ao_salvar = None):
        self.page = page
        self.ao_salvar = ao_salvar
        self.dados = list(dados['detalhe'])      # cópia mutável
        self.sort_campo = 'matricula'            # ordenação inicial
        self.sort_asc   = True
        self._ordenar()
        self._montar()

    def abrir_acontecimentos(self, e, x):
        verAcontecimentos(self.page, x, self.ao_salvar)

    def abrir_formulario(self, e, x, matricula):
        self.page.voltar_dados['endereco'].append(self.page.route)
        self.page.voltar_dados['dados_pagina'].append({'id': self.page.session.get("id")})
        
        if matricula:
            self.page.session.set('id', x)
            self.page.go('/matricula')
        else:
            self.page.session.set('tipo', 'escopo')
            self.page.session.set('id', x)
            self.page.go('/formulario')


    # ── ordenação ──────────────────────────────────────────────────
    def _ordenar(self):
        if self.sort_campo:
            self.dados.sort(
                key=lambda x: (x.get(self.sort_campo) or '').lower(),
                reverse=not self.sort_asc
            )

    def _on_sort(self, campo):
        """Chamado ao clicar no cabeçalho de uma coluna."""
        if self.sort_campo == campo:
            self.sort_asc = not self.sort_asc   # inverte se já era esta
        else:
            self.sort_campo = campo
            self.sort_asc   = True              # nova coluna → ascendente
        self._ordenar()
        self._atualizar()

    # ── linha da tabela ────────────────────────────────────────────
    def _montar_linha(self, item):
        matricula = item.get('matricula', '0')
        escopo_id = item.get('id_escopo', '0')
        botoes = ft.Row([
            ft.ElevatedButton("M", width=30, on_click= lambda e, x=matricula: self.abrir_formulario(e, x, True)),
            ft.ElevatedButton("E", width=30, on_click= lambda e, x=escopo_id: self.abrir_formulario(e, x, False)),
            ft.ElevatedButton("A", width=30, on_click= lambda e, x=escopo_id: self.abrir_acontecimentos(e, x)),
        ])

        validade_str  = item.get('validade', '')
        hoje          = date.today()

        if validade_str:
            validade_date = date.fromisoformat(validade_str)
            dias          = (validade_date - hoje).days

            if dias < 0:
                cor = ft.Colors.RED_700
            elif dias <= 30:
                cor = ft.Colors.ORANGE_700
            elif dias <= 120:
                cor = ft.Colors.AMBER_700
            else:
                cor = None
        else:
            cor = None  # sem validade → cor default

        def txt(valor):
            return ft.Text(valor, color=cor)

        def data_formatada(data):
            if data:
                data_formatada = datetime.strptime(data, '%Y-%m-%d')
                data_formatada = data_formatada.strftime('%d-%m-%Y')
                return data_formatada
            else:
                return ''
            

        return ft.DataRow(cells=[
            ft.DataCell(txt(item.get('matricula',          ''))),
            ft.DataCell(txt(item.get('primeiro_associado', ''))),
            ft.DataCell(txt(item.get('escopo',             ''))),
            ft.DataCell(txt(data_formatada(item.get('validade')))),
            ft.DataCell(txt(item.get('ultimo_movimento',   ''))),
            ft.DataCell(botoes),
        ])

    # ── cabeçalho de coluna ────────────────────────────────────────
    def _label_coluna(self, campo, titulo):
        ativo = (campo == self.sort_campo)
        seta  = (' ↑' if not self.sort_asc else ' ↓') if ativo else ''
        return ft.Text(titulo + seta, weight=ft.FontWeight.BOLD)

    def _montar_coluna(self, campo, titulo):
        def handler(e, c=campo):
            if c:
                self._on_sort(c)
        label = self._label_coluna(campo, titulo)
        return ft.DataColumn(label=label, on_sort=handler if campo else None)

    # ── construção/atualização da tabela ───────────────────────────
    def _montar(self):
        self._dt = ft.DataTable(
            columns=[self._montar_coluna(c, t) for c, t in self.COLUNAS],
            rows   =[self._montar_linha(item) for item in self.dados],
        )
        self.tabela = ft.Column([self._dt], scroll=ft.ScrollMode.AUTO)

    def _atualizar(self):
        # Atualiza cabeçalhos (setas)
        for i, (campo, titulo) in enumerate(self.COLUNAS):
            self._dt.columns[i].label = self._label_coluna(campo, titulo)
        # Atualiza linhas
        self._dt.rows = [self._montar_linha(item) for item in self.dados]
        self._dt.update()


class linhaBotoes():
    def __init__(self, page):
        self.page = page

    def botoes_acoes(self, acao):
        if acao == 'editar':
            self.page.voltar_dados['endereco'].append(self.page.route)
            self.page.voltar_dados['dados_pagina'].append({
                'id': self.page.session.get("id"),
                'tipo': 'grupo' 
                })
            self.page.go('/formulario')

        elif acao == 'imprimir':
            print('imprimir')

        elif acao == 'voltar':
            retorno = self.page.voltar_dados['endereco'][-1] if self.page.voltar_dados['endereco'] else '/dashboard'
            voltar_dados = self.page.voltar_dados['dados_pagina'][-1] if self.page.voltar_dados['dados_pagina'] else None
            if voltar_dados:
                for chave, valor in voltar_dados.items():
                    self.page.session.set(chave, valor)

            self.page.voltar_dados['endereco'].pop()
            self.page.voltar_dados['dados_pagina'].pop()

            self.page.go(retorno)
        else:
            pass

    def montar_linha_botoes(self):
        return ft.Column([
            ft.Container(
                height=60,
                width=1000,
                bgcolor=ft.Colors.GREY_200,
                border_radius=10,
                padding=10,
                content= ft.Row([
                    ft.ElevatedButton("Detalhes", width=100, on_click=lambda e: self.botoes_acoes('editar')),
                    ft.ElevatedButton("Imprimir", width=100, on_click=lambda e: self.botoes_acoes('imprimir')),
                    ft.ElevatedButton("Voltar", width=100, on_click=lambda e: self.botoes_acoes('voltar')),
                ], alignment=ft.MainAxisAlignment.END, spacing=20)
            )
        ])
        


class grupoBase():
    def __init__(self, page: ft.Page):
        self.page = page
        self.dados = self.obter_dados()
        self.montar_layout()

    def obter_dados(self):
        dados = self.page.cliente.rpc('painel_do_grupo', {'p_grupo_id': self.page.session.get("id")}).execute()
        return dados.data

    def montar_dados_gerais(self):
        dados_gerais = self.dados['dados_gerais']
        nome = ft.Row([
            ft.Text(f"Nome: {dados_gerais['nome']}", size=20, weight="bold"),
            ])
        largura_dados = (900 - 20 * 2) / 3

        outros_dados = ft.Row([], spacing=20, alignment=ft.MainAxisAlignment.START)
        for dado in ['nucleo', 'coordenador']:
            outros_dados.controls.append(
                ft.Container(
                    width= largura_dados,
                    height= 50,
                    content= ft.Text(f"{dado.capitalize()}: {dados_gerais[dado]}"),
                )
            )
        return ft.Column([nome, outros_dados])

    def atualizar_dados(self):
        # Atualiza os dados da tabela
        self.dados = self.obter_dados()
        self.dados_tabela.dados = list(self.dados['detalhe'])
        self.dados_tabela._atualizar()
        
    def montar_layout(self):
        # 1️⃣ Cabeçalho
        cabecalho = ft.Row([
            ft.Text("☰", size=24),  # menu placeholder
            ft.Text("SPG ABIO", size=24, weight="bold"),
        ], alignment=ft.MainAxisAlignment.START, spacing=20)

        # 2️⃣ Dados gerais
        dados_gerais = ft.Column([
            ft.Container(
                height= 100,
                width= 1000,
                bgcolor=ft.Colors.GREY_200,
                border_radius=10,
                padding=10,
                content= self.montar_dados_gerais(),
            ),
        ])

        # 3️⃣ Tabela de detalhes
        self.dados_tabela = quadroTabela(self.page, self.dados, self.atualizar_dados)
        tabela = ft.Column([
                ft.Container(
                height= 400,
                width= 1000,
                clip_behavior=ft.ClipBehavior.HARD_EDGE,
                bgcolor=ft.Colors.GREY_200,
                border_radius=10,
                padding=20,
                content= self.dados_tabela.tabela
                ),
        ])


        # 4️⃣ Botões
        linha_botoes = linhaBotoes(self.page).montar_linha_botoes()

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

def iniciar_dashboard_nucleos(id=21):
    def main(page: ft.Page):
        page.cliente = login_supabase()
        page.session.set("id", id)
        page.avancar_dados = {}
        page.voltar_dados = {}

        grupoBase(page)
    return main


if __name__ == "__main__":
    ft.app(target=iniciar_dashboard_nucleos())
