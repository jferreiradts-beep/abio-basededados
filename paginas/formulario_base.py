import flet as ft
import pandas as pd
import os
from formulario_coluna2 import funcao_menu_lateral  
from escudo_supabase import login_supabase
from formatar_campos import formatar_cpf_cnpj
import re
            

class janelaNovoRotulo():
    def __init__(self, page, resposta, atualizar_estrutura_de_campos):
        self.page = page
        self.atualizar_estrutura_de_campos = atualizar_estrutura_de_campos
        self.tipo = page.session.get("tipo")
        self.cliente = self.page.cliente
        self.resposta = resposta

        self.nome_novo_rotulo = ft.TextField(label="Nome", width=150)
        self.descricao_novo_rotulo = ft.TextField(label="Descrição", width=300)

        self.janela = ft.AlertDialog(
            title=ft.Text("Novo rótulo de..."),
            content=ft.Container(
                width=350, height=100,
                content=ft.Column([
                    self.nome_novo_rotulo,
                    self.descricao_novo_rotulo
                ])
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=self.cancelar_novo_rotulo),
                ft.TextButton("Salvar", on_click=self.salvar_novo_rotulo)
            ]
        )

    def cancelar_novo_rotulo(self, e):
        self.janela.open = False
        self.page.update()

    def salvar_novo_rotulo(self, e):
        dados = {
            "nome": self.nome_novo_rotulo.value,
            "descricao": self.descricao_novo_rotulo.value
        }

        try:
            salvar_rotulo = self.cliente.table(f"campos_{self.tipo}").insert(dados).execute()
            novo_id = salvar_rotulo.data[0]['id']
            self.resposta['campos_ajustaveis'].append({'id': novo_id, 'nome': self.nome_novo_rotulo.value})

            self.atualizar_estrutura_de_campos()
            self.page.snack_bar = ft.SnackBar(ft.Text(f"Rotulo criado com sucesso! ID: {novo_id}") )

        except Exception as e:
            self.page.snack_bar = ft.SnackBar( ft.Text(f"Erro ao criar rotulo: {e}"), bgcolor="red" )
        
        finally:
            self.cancelar_novo_rotulo(None)
            self.page.snack_bar.open = True

class botoesFormulario():
    def __init__(self, page, resposta, ver_janela_nrotulo, atualizar_estrutura_de_campos):
        self.page = page
        self.resposta = resposta
        self.ver_janela_nrotulo = ver_janela_nrotulo
        self.atualizar_estrutura_de_campos = atualizar_estrutura_de_campos

        self.botoes = ft.Row([
                ft.ElevatedButton("Novo campo", width=150, on_click=self.novo_campo),
                ft.ElevatedButton("Novo rótulo", width=150, on_click=self.novo_rotulo),
                ft.ElevatedButton("Voltar", width=150, on_click=self.voltar),
                ft.ElevatedButton("Salvar", width=150, on_click=self.salvar)
            ], spacing=46)

    def novo_campo(self, e):
        self.resposta['dados_ajustaveis'].append({'campo_id': '', 'valor': ''})
        self.atualizar_estrutura_de_campos()

    def novo_rotulo(self, e):
        self.ver_janela_nrotulo()

    def voltar(self, e):
        retorno = self.page.voltar_dados['endereco'][-1] if self.page.voltar_dados['endereco'] else '/dashboard'
        voltar_dados = self.page.voltar_dados['dados_pagina'][-1] if self.page.voltar_dados['dados_pagina'] else None
        if voltar_dados:
            for chave, valor in voltar_dados.items():
                self.page.session.set(chave, valor)

        self.page.voltar_dados['endereco'].pop()
        self.page.voltar_dados['dados_pagina'].pop()

        self.page.go(retorno)

    def salvar(self, e):
        self.cliente = self.page.cliente
        self.tipo = self.page.session.get('tipo')
        resposta = self.cliente.rpc('salvar_formulario', {'p_tabela': self.tipo, 'p_dados': self.resposta}).execute()
        self.page.session.set('id', resposta.data['id'])


class estruturaDeCampos():
    def __init__(self, page, resposta):
        self.page = page
        self.resposta = resposta
        self.area_rolavel = ft.Column(spacing=20,
            expand=True,
            scroll=ft.ScrollMode.AUTO,
            alignment=ft.MainAxisAlignment.START,
            horizontal_alignment=ft.CrossAxisAlignment.START)
        self.construir_area_rolavel()

    def campo_fixo(self, metainformacao, valor_inicial = '', opcoes = [], largura=(150, 200), chave=''):
        
        def atualizar_valor(e, chave):
            valor = re.sub(r'\D', '', e.control.value) if chave == 'cpf' else e.control.value
            self.resposta['dados_fixos'][chave] = valor

            if metainformacao['rotulo'] == 'Tipo de escopo':
                self.page.session.set("tipo_escopo", e.control.value)
                nome_label = next(opcao['nome'] for opcao in opcoes if opcao['id'] == int(e.control.value))
                self.page.session.set("nome_escopo", nome_label)

        campo = ft.Text(metainformacao['rotulo'], width=largura[0], weight="bold")
        if len(opcoes) > 0:
            opcoes_lista = []
            encurtar = len(opcoes) > 6
            opcoes = sorted(opcoes, key=lambda x: x['nome'])
            for opcao in opcoes:
                nome = opcao['nome'].split(' ')[0]+ ' ' + opcao['nome'].split(' ')[-1] if encurtar else opcao['nome']
                opcoes_lista.append(ft.dropdown.Option(key=opcao['id'], text=nome))
            valor = ft.Dropdown(value=valor_inicial, options=opcoes_lista, width=largura[1], text_style=ft.TextStyle(size=13), menu_height= 300,
                                on_change=lambda e, chave=chave: atualizar_valor(e, chave))
        else:
            valor_inicial = valor_inicial or self.page.avancar_dados.get(chave, '')
            valor_inicial = formatar_cpf_cnpj(valor_inicial) if chave == 'cpf' else valor_inicial
            valor = ft.TextField(value=valor_inicial, width=largura[1], text_style=ft.TextStyle(size=13),
                                 on_blur=lambda e, chave=chave: atualizar_valor(e, chave))
    
        if metainformacao['rotulo'] == 'CPF ou CNPJ':
            valor.on_change = lambda e: (setattr(e.control, "value", formatar_cpf_cnpj(e.control.value)),
                                         e.control.update())

        if metainformacao['rotulo'] == 'Tipo de escopo':
            self.page.session.set("tipo_escopo", valor_inicial)
            nome_label = [opcao['nome'] for opcao in opcoes if opcao['id'] == valor_inicial][0]
            self.page.session.set("nome_escopo", nome_label)

        return ft.Row([campo,valor], alignment=ft.MainAxisAlignment.CENTER, spacing=10)

    def campo_ajustavel(self, posicao, opcoes_label=[], valor_inicial='', largura=(150, 200)):
        
        def atualizar_label(e):
            self.resposta['dados_ajustaveis'][posicao]['campo_id'] = e.control.value

        def atualizar_valor(e):
            self.resposta['dados_ajustaveis'][posicao]['valor'] = e.control.value


        # Dropdown como "label"
        opcoes_lista = [ft.dropdown.Option(key=opcao['id'], text=opcao['nome']) for opcao in opcoes_label] +\
            [ft.dropdown.Option(key='Eliminar', text='Eliminar')]

        label_dropdown = ft.Dropdown(
            value=self.resposta['dados_ajustaveis'][posicao].get('campo_id'),
            options=opcoes_lista,
            hint_text='Selecione',
            width=largura[0],
            text_style=ft.TextStyle(size=13, weight="bold"),
            border=ft.InputBorder.NONE,
            border_radius=0,
            on_change=atualizar_label
        )

        # Campo de texto para o valor
        valor_textfield = ft.TextField(
            value=valor_inicial,
            width=largura[1],
            text_style=ft.TextStyle(size=13),
            on_blur=atualizar_valor
        )

        return ft.Row([label_dropdown, valor_textfield], alignment=ft.MainAxisAlignment.CENTER, spacing=10)

    def construir_area_rolavel(self):
        # Construir campo nome
        nome_opcoes = self.resposta['opcoes']['nome'] if 'nome' in self.resposta['opcoes'] else []
        nome = ft.Row([
            self.campo_fixo(self.resposta['campos_fixos']['nome'], self.resposta['dados_fixos']['nome'], \
                largura=(150, 360), chave='nome', opcoes=nome_opcoes)
        ],
        spacing=20,
        alignment=ft.MainAxisAlignment.START)
        
        # Construir colunas
        outros_fixos = [
            campo
            for campo, info in sorted(
                self.resposta["campos_fixos"].items(),
                key=lambda item: item[1]["ordem"]
            )
            if campo not in ["id", "nome"]
        ]

        primeira_coluna = []
        segunda_coluna = []

        for i, campo in enumerate(outros_fixos):
            opcoes = self.resposta['opcoes'][campo] if campo in self.resposta['opcoes'] else []
            if i % 2 == 0:
                primeira_coluna.append(self.campo_fixo(self.resposta['campos_fixos'][campo], self.resposta['dados_fixos'][campo], opcoes, chave=campo))
            else:
                segunda_coluna.append(self.campo_fixo(self.resposta['campos_fixos'][campo], self.resposta['dados_fixos'][campo], opcoes, chave=campo))
        
        for i, campo in enumerate(self.resposta['dados_ajustaveis']):
            if (i + len(outros_fixos)) % 2 == 0:
                primeira_coluna.append(self.campo_ajustavel(i, self.resposta['campos_ajustaveis'], self.resposta['dados_ajustaveis'][i]['valor']))
            else:
                segunda_coluna.append(self.campo_ajustavel(i, self.resposta['campos_ajustaveis'], self.resposta['dados_ajustaveis'][i]['valor']))

        self.area_rolavel.controls = [
            nome,
            ft.Row([
                ft.Column(primeira_coluna, spacing=10),
                ft.Column(segunda_coluna, spacing=10)
                ], 
                alignment=ft.MainAxisAlignment.START,
                vertical_alignment=ft.CrossAxisAlignment.START, 
            spacing=20)
        ]

        # Limpar avançar dados
        self.page.avancar_dados = {}

class dadosFormulario():
    def __init__(self, page):
        self.page = page
        self.tipo = self.page.session.get("tipo")
        self.id = self.page.session.get("id")

        self.resposta = self.baixar_dados()

        if self.tipo == 'uprod':
            self.titulo = f'Detalhe da Unidade de Produção'
        else:
            self.titulo = f'Detalhe d{self.tipo[-1]} {self.tipo.capitalize()}'

    def baixar_dados(self):
        dados = self.page.cliente.rpc('preencher_formulario', {'p_tabela': self.tipo, 'p_registro': self.id}).execute()
        return dados.data

class baseFormulario():
    def __init__(self, page):
        self.page = page

        # Criar classes
        self.dados = dadosFormulario(self.page)                               # Modelo de dados
        self.estrutura = estruturaDeCampos(self.page, self.dados.resposta)    # Estrutura de campos
        self.janela_rotulo = janelaNovoRotulo(self.page, self.dados.resposta, # Janela de rotulos
                        self.atualizar_estrutura_de_campos)    
        self.botoes = botoesFormulario(self.page, self.dados.resposta,        # Botões
                        self.ver_janela_nrotulo,
                        self.atualizar_estrutura_de_campos)


        # Configurar página
        self.page.title = 'SPG ABIO: ' + self.dados.titulo
        self.construir_layout()

        # Carregar dados de municipios em menu lateral de escopos
        if self.page.session.get("tipo") == 'escopo':
            self.menu_lateral.opcoes_mun_estados = pd.read_csv(os.path.join('mapa', 'municipios_estados.csv'))

    def ver_janela_nrotulo(self):
        if self.janela_rotulo.janela not in self.page.overlay:
            self.page.overlay.append(self.janela_rotulo.janela)
        self.janela_rotulo.janela.open = True
        self.page.update()

    def atualizar_estrutura_de_campos(self):
        self.estrutura.construir_area_rolavel()
        self.estrutura.area_rolavel.update()

    def construir_layout(self):
        # 1️⃣ Cabeçalho
        cabecalho = ft.Row([
            ft.Text("☰", size=24),  # menu placeholder
            ft.Text("SPG ABIO", size=24, weight="bold"),
        ], alignment=ft.MainAxisAlignment.START, spacing=20)

        # 2️⃣ Espaço de formulario
        espaco_formulario = ft.Column([
            ft.Container(
                height= 520,
                width= (150 + 200) * 2 + (20 + 10 + 20 + 10 + 20),
                bgcolor=ft.Colors.GREY_200,
                border_radius=10,
                padding=20,
                content=ft.Column([
                    ft.Text(self.dados.titulo, size=24, weight="bold"),
                    self.estrutura.area_rolavel,
                    self.botoes.botoes
                ])
            )
        ],
        spacing=20,
        alignment=ft.MainAxisAlignment.START,
        horizontal_alignment=ft.CrossAxisAlignment.START)
        
        # 3️⃣ Espaço costumizável
        self.menu_lateral = funcao_menu_lateral(self.page, self.dados.resposta, self.atualizar_estrutura_de_campos)
        
        # Verifica se o menu lateral tem atributo 'menu' (já foi implementado)
        conteudo_menu = self.menu_lateral.menu if hasattr(self.menu_lateral, 'menu') else self.menu_lateral
        espaco_costumizavel = ft.Column([
            ft.Container(
                height=520,
                width= 350,
                bgcolor=ft.Colors.GREY_200,
                border_radius=10,
                content=conteudo_menu,
                padding=20)
        ],
        spacing=20,
        alignment=ft.MainAxisAlignment.START,
        horizontal_alignment=ft.CrossAxisAlignment.START)
        
        #  Adiciona tudo à página
        self.page.add(
            ft.Row([
                ft.Column(
                    [
                        cabecalho,
                        ft.Row([
                            espaco_formulario,
                            espaco_costumizavel,
                        ],
                        spacing=20,
                        alignment=ft.MainAxisAlignment.CENTER,
                        vertical_alignment=ft.CrossAxisAlignment.START
                        )
                    ],
                    spacing=20,
                    alignment=ft.MainAxisAlignment.CENTER
                    )
                ],
                alignment=ft.MainAxisAlignment.CENTER,
            )
        )



def iniciar_formulario(tipo = 'escopo', id = 295):
    def main(page: ft.Page):
        page.cliente = login_supabase()
        page.session.set("tipo", tipo)
        page.session.set("id", id)
        page.avancar_dados = {}
        page.voltar_dados = {}
        
        baseFormulario(page)
    return main

if __name__ == "__main__":
    ft.app(target=iniciar_formulario())
