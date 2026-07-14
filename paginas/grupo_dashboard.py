import flet as ft
import pandas as pd
from datetime import date, datetime
from formulario_coluna2 import verAcontecimentos
from escudo_supabase import aviso

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
        self.page.voltar_dados['dados_pagina'].append({
            'grupo_dashboard_nucleo_id': self.page.session.get("grupo_dashboard_nucleo_id"),
            'grupo_dashboard_grupo_id': self.page.session.get("grupo_dashboard_grupo_id"),
            'id': self.page.session.get("id")
        })
        
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
        matricula = item.get('id_matricula') or 0
        escopo_id = item.get('id_escopo') or 0
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
    def __init__(self, page, pai=None):
        self.page = page
        self.pai = pai
        self.btn_imprimir = ft.ElevatedButton("Imprimir", width=100, on_click=lambda e: self.botoes_acoes('imprimir'))
        self.btn_voltar = ft.ElevatedButton("Voltar", width=100, on_click=lambda e: self.botoes_acoes('voltar'))

    def botoes_acoes(self, acao):
        if acao == 'imprimir':
            try:
                from gerar_certificado import montarFichaGrupos
                if self.pai:
                    ficha = montarFichaGrupos(self.page.cliente, self.pai.dados['dados_gerais'], self.pai.dados_tabela.dados)
                    url_pdf = ficha.imprimir_ficha(self.page.session.get("id"))
                    self.page.launch_url(url=url_pdf, web_window_name="_blank")
            except Exception as e:
                from escudo_supabase import aviso
                aviso(self.page, f"Erro ao gerar a ficha de grupos: {str(e)}")

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
                    self.btn_imprimir,
                    self.btn_voltar,
                ], alignment=ft.MainAxisAlignment.END, spacing=20)
            )
        ])
        


class grupoBase():
    def __init__(self, page: ft.Page):
        self.page = page
        self.dados = {'dados_gerais': {}, 'detalhe': []}
        
        self.dropdown_nucleo = ft.Dropdown(
            label="Núcleo",
            width=250,
            on_change=self.ao_selecionar_nucleo
        )
        self.dropdown_grupo = ft.Dropdown(
            label="Grupo",
            width=250,
            on_change=self.ao_selecionar_grupo
        )
        self.texto_coordenador = ft.Text("Coordenador: ", size=16, weight="bold")
        
        self.montar_layout()
        self.carregar_nucleos_e_restaurar()

    def carregar_nucleos_e_restaurar(self):
        resposta = self.page.cliente.table('nucleo').select('id, nome').order('nome').execute()
        opcoes = [ft.dropdown.Option(key=str(n['id']), text=n['nome']) for n in resposta.data]
        self.dropdown_nucleo.options = opcoes

        # Restaurar estado se voltar para a página
        if 'nucleo_id' in self.page.avancar_dados:
            saved_nucleo_id = self.page.avancar_dados.pop('nucleo_id')
        else:
            saved_nucleo_id = self.page.session.get('grupo_dashboard_nucleo_id')

        if saved_nucleo_id:
            self.dropdown_nucleo.value = str(saved_nucleo_id)
            self.page.session.set("grupo_dashboard_nucleo_id", saved_nucleo_id)
            
            resposta_grupos = self.page.cliente.table('grupo').select('id, nome').eq('nucleo_id', saved_nucleo_id).order('nome').execute()
            opcoes_grupos = [ft.dropdown.Option(key=str(g['id']), text=g['nome']) for g in resposta_grupos.data]
            self.dropdown_grupo.options = opcoes_grupos
            
            if 'grupo_id' in self.page.avancar_dados:
                saved_grupo_id = self.page.avancar_dados.pop('grupo_id')
            else:
                saved_grupo_id = self.page.session.get('grupo_dashboard_grupo_id')
            
            if saved_grupo_id:
                self.dropdown_grupo.value = str(saved_grupo_id)
                self.page.session.set("grupo_dashboard_grupo_id", saved_grupo_id)
                self.page.session.set("id", str(saved_grupo_id))
                self.atualizar_dados()
                self.linha_botoes_obj.btn_imprimir.visible = True
            else:
                self.page.session.set("grupo_dashboard_grupo_id", None)
                self.page.session.set("id", None)
        else:
            self.page.session.set("grupo_dashboard_nucleo_id", None)
            self.page.session.set("grupo_dashboard_grupo_id", None)
            self.page.session.set("id", None)
        
        self.dropdown_nucleo.update()
        self.dropdown_grupo.update()
        self.texto_coordenador.update()
        if hasattr(self, 'linha_botoes_obj'):
            self.linha_botoes_obj.btn_imprimir.update()

    def ao_selecionar_nucleo(self, e):
        nucleo_id = self.dropdown_nucleo.value
        self.page.session.set("grupo_dashboard_nucleo_id", nucleo_id)
        if nucleo_id:
            resposta = self.page.cliente.table('grupo').select('id, nome').eq('nucleo_id', nucleo_id).order('nome').execute()
            opcoes = [ft.dropdown.Option(key=str(g['id']), text=g['nome']) for g in resposta.data]
            self.dropdown_grupo.options = opcoes
            self.dropdown_grupo.value = None
            self.dropdown_grupo.update()
            
            # Limpar dados
            self.limpar_dados()
        else:
            self.dropdown_grupo.options = []
            self.dropdown_grupo.value = None
            self.dropdown_grupo.update()
            self.limpar_dados()

    def ao_selecionar_grupo(self, e):
        grupo_id = self.dropdown_grupo.value
        self.page.session.set("grupo_dashboard_grupo_id", grupo_id)
        if grupo_id:
            self.page.session.set("id", str(grupo_id))
            self.atualizar_dados()
            self.linha_botoes_obj.btn_imprimir.visible = True
            self.linha_botoes_obj.btn_imprimir.update()
        else:
            self.limpar_dados()

    def limpar_dados(self):
        self.page.session.set("grupo_dashboard_grupo_id", None)
        self.texto_coordenador.value = "Coordenador: "
        self.texto_coordenador.update()
        
        self.dados = {'dados_gerais': {}, 'detalhe': []}
        self.dados_tabela.dados = []
        self.dados_tabela._atualizar()
        
        if hasattr(self, 'linha_botoes_obj'):
            self.linha_botoes_obj.btn_imprimir.visible = False
            self.linha_botoes_obj.btn_imprimir.update()

    def obter_dados(self):
        grupo_id = self.page.session.get("id")
        if not grupo_id:
            return {'dados_gerais': {}, 'detalhe': []}
        dados = self.page.cliente.rpc('painel_do_grupo', {'p_grupo_id': int(grupo_id)}).execute()
        return dados.data

    def montar_dados_gerais(self):
        outros_dados = ft.Row([
            self.dropdown_nucleo,
            self.dropdown_grupo,
            self.texto_coordenador
        ], spacing=20, alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.CENTER)

        return ft.Column([outros_dados], alignment=ft.MainAxisAlignment.CENTER)

    def atualizar_dados(self):
        # Atualiza os dados da tabela
        self.dados = self.obter_dados()
        
        coordenador = self.dados.get('dados_gerais', {}).get('coordenador') or 'Não definido'
        self.texto_coordenador.value = f"Coordenador: {coordenador}"
        self.texto_coordenador.update()
        
        self.dados_tabela.dados = list(self.dados.get('detalhe', []))
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
                padding=20,
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
        self.linha_botoes_obj = linhaBotoes(self.page, self)
        self.linha_botoes = self.linha_botoes_obj.montar_linha_botoes()
        self.linha_botoes_obj.btn_imprimir.visible = False

        # Adicionar à pagina
        self.page.add(
            ft.Row([
                ft.Column([
                    cabecalho,
                    dados_gerais,
                    tabela,
                    self.linha_botoes],
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

def iniciar_dashboard_nucleos(id=None):
    def main(page: ft.Page):
        from escudo_supabase import login_supabase
        page.cliente = login_supabase()
        if id:
            page.session.set("id", str(id))
        page.avancar_dados = {}
        page.voltar_dados = {'endereco': [], 'dados_pagina': []}

        grupoBase(page)
    return main


if __name__ == "__main__":
    ft.app(target=iniciar_dashboard_nucleos())
