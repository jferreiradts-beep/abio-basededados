import flet as ft
import pandas as pd
import os
from formulario_coluna2 import funcao_menu_lateral  
from escudo_supabase import aviso
from formatar_campos import formatar_cpf_cnpj
import re

COR_MODIFICADO = "#FFFDE7"   # amarelo pálido — campo com valor não salvo
COR_NORMAL     = None        # fundo padrão do tema

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

            self.cancelar_novo_rotulo(None)
            self.atualizar_estrutura_de_campos()
            aviso(self.page, f"Rotulo criado com sucesso! ID: {novo_id}")

        except Exception as e:
            self.cancelar_novo_rotulo(None)
            aviso(self.page, f"Erro ao criar rotulo: {e}")
        

class botoesFormulario():
    def __init__(self, page, resposta, ver_janela_nrotulo, atualizar_estrutura_de_campos):
        self.page = page
        self.resposta = resposta
        self.ver_janela_nrotulo = ver_janela_nrotulo
        self.atualizar_estrutura_de_campos = atualizar_estrutura_de_campos

        self.botoes = ft.Row([
                ft.ElevatedButton("Novo campo", width=130, on_click=self.novo_campo),
                ft.ElevatedButton("Novo rótulo", width=130, on_click=self.novo_rotulo),
                ft.ElevatedButton("Excluir", width=130, disabled=True, on_click= lambda e: print('excluir')),
                ft.ElevatedButton("Salvar", width=130, on_click=self.salvar),
                ft.ElevatedButton("Voltar", width=130, on_click=self.voltar)
            ], spacing=20)

    def novo_campo(self, e):
        self.resposta['dados_ajustaveis'].append({'campo_id': '', 'valor': '', 'novo': True})
        self.atualizar_estrutura_de_campos()

    def novo_rotulo(self, e):
        self.ver_janela_nrotulo()

    def voltar(self, e):
        endereco_lista = self.page.voltar_dados.get('endereco', [])
        dados_lista    = self.page.voltar_dados.get('dados_pagina', [])
        retorno     = endereco_lista[-1] if endereco_lista else '/dashboard'
        voltar_dados = dados_lista[-1] if dados_lista else None
        if voltar_dados:
            for chave, valor in voltar_dados.items():
                self.page.session.set(chave, valor)
        if endereco_lista:
            self.page.voltar_dados['endereco'].pop()
        if dados_lista:
            self.page.voltar_dados['dados_pagina'].pop()
        self.page.go(retorno)

    def salvar(self, e):
        self.cliente = self.page.cliente
        self.tipo = self.page.session.get('tipo')
        try:
            resposta = self.cliente.rpc('salvar_formulario', {'p_tabela': self.tipo, 'p_dados': self.resposta}).execute()
        except Exception as ex:
            aviso(self.page, f"Erro de ligação ao servidor: {ex}")
            return

        if resposta and resposta.data.get('status') == 'success':
            novo_id = resposta.data['id']
            self.page.session.set('id', novo_id)
            self.resposta['dados_fixos']['id'] = novo_id
            # Limpar a cor de todos os campos (sinal visual de guardado)
            if hasattr(self, 'campos_ref'):
                for inst in self.campos_ref:
                    inst.marcar_salvo()
        else:
            mensagem = resposta.data.get('message', 'Erro desconhecido') if resposta else 'Sem resposta'
            aviso(self.page, f"Erro ao salvar formulário: {mensagem}")


class aplicarMascara():
    """Aplica uma máscara de formatação a um valor.
    Se mascaras=None, o método aplicar_mascara devolve o valor inalterado (no-op).
    """
    def __init__(self, mascaras: str | None):
        if mascaras:
            self.mascaras = sorted(mascaras.split('; '), key=lambda x: x.count('#'))
            self.c_mascaras = [x.count('#') for x in self.mascaras]
            self.aplicar_mascara = self._aplicar_mascara_texto
            self.salvar_limpo = self._salvar_limpo_texto
            self.on_change = self._on_change_texto   # formata o display em tempo real
        else:
            self.aplicar_mascara = lambda valor: valor  # no-op
            self.salvar_limpo = lambda valor: valor
            self.on_change = lambda e: None             # no-op

    def _aplicar_mascara_texto(self, valor):
        valor_limpo = re.sub(r'[^0-9]', '', valor)
        if len(valor_limpo) == 0:
            return None

        # Decidir máscara aplicável
        c = len(valor_limpo)
        id_mascara = next((i for i, limite in enumerate(self.c_mascaras) if c <= limite), -1)
        mascara = self.mascaras[id_mascara] if id_mascara != -1 else None

        # Aplicar máscara
        i = 0
        valor_final = ''
        for m in mascara:
            if m == '#':
                if i >= c:
                    break
                valor_final += valor_limpo[i]
                i += 1
            else:
                valor_final += m

        return valor_final

    def _salvar_limpo_texto(self, valor):
        return re.sub(r'[^0-9]', '', valor)

    def _on_change_texto(self, e):
        """Formata o valor enquanto o utilizador digita, actualizando o controlo."""
        e.control.value = self._aplicar_mascara_texto(e.control.value)
        e.control.update()



class campoFixo():
    def __init__(self, page, resposta, campo, largura=(100, 250)):
        self.page = page
        self.resposta = resposta
        self.campo = campo
        self.largura = largura
        self._dependentes = []   # outros campoFixo que precisam ser actualizados quando este muda

        # Sempre cria a máscara — ela própria sabe o que fazer com None
        mascara_str = self.resposta['campos_fixos'][self.campo].get('mascara')
        self.mascara = aplicarMascara(mascara_str)

        self.campo_ui = self.criar_campo()

    # ------------------------------------------------------------------
    # Observer: ligar dependências entre campos
    # ------------------------------------------------------------------
    def registar_dependente(self, outro_campo):
        """Regista um campoFixo que deve recarregar as suas opções quando este campo muda."""
        self._dependentes.append(outro_campo)

    def recarregar_opcoes(self):
        """Recarrega as opções do dropdown com base no valor actual do campo pai."""
        opcoes_raw = self.consultar_opcoes()
        self._entrada.options = [
            ft.dropdown.Option(key=str(op['id']), text=op['opcao']) for op in opcoes_raw
        ]
        self._entrada.value = None
        self.resposta['dados_fixos'][self.campo] = ''
        # Notificar os próprios dependentes desta instância (encadeamento)
        for dep in self._dependentes:
            dep.recarregar_opcoes()
        self._entrada.update()

    # ------------------------------------------------------------------
    # Construção do widget
    # ------------------------------------------------------------------
    def obter_valor_inicial(self):
        valor_remoto = self.resposta['dados_fixos'].get(self.campo, None)
        if not valor_remoto:
            self.resposta['dados_fixos'][self.campo] = self.page.avancar_dados.get(self.campo, '')

        valor = str(self.resposta['dados_fixos'][self.campo])
        return valor

    def criar_campo(self):
        titulo = ft.Text(self.resposta['campos_fixos'][self.campo]['rotulo'], width=self.largura[0], weight="bold")
        valor_inicial = self.obter_valor_inicial()

        # Cor inicial: amarelo se registo novo (id nulo/zero), normal se existente
        id_val = self.resposta['dados_fixos'].get('id')
        novo_registo = not id_val or str(id_val) in ('0', '', 'None')
        bgcolor_ini = COR_MODIFICADO if novo_registo else COR_NORMAL

        if self.resposta['campos_fixos'][self.campo].get('opcoes'):
            opcoes_raw = self.consultar_opcoes()
            opcoes_lista = [ft.dropdown.Option(key=str(opcao['id']), text=opcao['opcao']) for opcao in opcoes_raw]
            self._entrada = ft.Dropdown(
                value=str(valor_inicial) if valor_inicial else None, options=opcoes_lista,
                width=self.largura[1], text_style=ft.TextStyle(size=13), menu_height=300,
                on_change=lambda e: self.atualizar_campo(e.control.value))
        else:
            self._entrada = ft.TextField(
                value=self.mascara.aplicar_mascara(valor_inicial),
                width=self.largura[1], text_style=ft.TextStyle(size=13),
                on_change=lambda e: (self.mascara.on_change(e), self.atualizar_campo(e.control.value)))

        # Container dá cor uniforme a TextField e Dropdown
        self._container = ft.Container(content=self._entrada, bgcolor=bgcolor_ini, border_radius=5)
        return ft.Row([titulo, self._container], alignment=ft.MainAxisAlignment.CENTER, spacing=10)

    # ------------------------------------------------------------------
    # Feedback visual: campo modificado vs salvo
    # ------------------------------------------------------------------
    def marcar_modificado(self):
        self._container.bgcolor = COR_MODIFICADO
        self._container.update()

    def marcar_salvo(self):
        self._container.bgcolor = COR_NORMAL
        self._container.update()

    def atualizar_campo(self, valor):
        self.resposta['dados_fixos'][self.campo] = self.mascara.salvar_limpo(valor)
        self.marcar_modificado()
        # Notificar dependentes (Observer)
        for dep in self._dependentes:
            dep.recarregar_opcoes()
        self.campo_ui.update()

    def consultar_opcoes(self):
        idx = self.resposta['campos_fixos'][self.campo]['id']
        campo_consulta = self.resposta['campos_fixos'][self.campo]['filtro']
        p_filtro = self.resposta['dados_fixos'].get(campo_consulta)
        p_filtro = 0 if p_filtro == '' else p_filtro
        
        opcoes = self.page.cliente.rpc('obter_opcoes', {'idx': idx, 'p_filtro': p_filtro}).execute()
        return opcoes.data

class campoAjustavel():
    """Campo ajustável (label via Dropdown + valor via TextField).
    Inclui a opção 'Eliminar' com diálogo de confirmação.
    Todos os valores são texto puro, sem máscara.
    """
    def __init__(self, page, resposta, posicao, opcoes_label, atualizar_estrutura_de_campos, largura=(150, 200)):
        self.page = page
        self.resposta = resposta
        self.posicao = posicao
        self.opcoes_label = opcoes_label
        self.atualizar_estrutura_de_campos = atualizar_estrutura_de_campos
        self.largura = largura

        self.dialogo = ft.AlertDialog(
            title=ft.Text("Confirmar eliminação"),
            content=ft.Text(""),  # preenchido em _atualizar_label
            actions=[
                ft.TextButton("Cancelar", on_click=self._eliminar_cancelado),
                ft.TextButton("Eliminar", on_click=self._eliminar_confirmado),
            ]
        )

        self.campo_ui = self._criar_campo()

    def _criar_campo(self):
        # Cor inicial igual à dos campos fixos
        id_val = self.resposta['dados_fixos'].get('id')
        novo_registo = not id_val or str(id_val) in ('0', '', 'None')
        
        # Um campo ajustável começa com a cor modificada se for um novo registro
        # OU se for um campo ajustável especificamente adicionado na sessão atual (novo = True)
        dado_aj = self.resposta['dados_ajustaveis'][self.posicao]
        eh_campo_novo = dado_aj.get('novo', False)
        
        bgcolor_aj = COR_MODIFICADO if (novo_registo or eh_campo_novo) else COR_NORMAL

        opcoes_lista = (
            [ft.dropdown.Option(key=op['id'], text=op['nome']) for op in self.opcoes_label]
            + [ft.dropdown.Option(key='Eliminar', text='Eliminar')]
        )

        self.label_dropdown = ft.Dropdown(
            value=self.resposta['dados_ajustaveis'][self.posicao].get('campo_id'),
            options=opcoes_lista,
            hint_text='Selecione',
            width=self.largura[0],
            text_style=ft.TextStyle(size=13, weight="bold"),
            border=ft.InputBorder.NONE,
            border_radius=0,
            on_change=self._atualizar_label
        )

        self.valor_textfield = ft.TextField(
            value=self.resposta['dados_ajustaveis'][self.posicao].get('valor', ''),
            width=self.largura[1],
            text_style=ft.TextStyle(size=13),
            bgcolor=bgcolor_aj,
            on_blur=self._atualizar_valor
        )

        return ft.Row([self.label_dropdown, self.valor_textfield],
                      alignment=ft.MainAxisAlignment.CENTER, spacing=10)

    def _atualizar_label(self, e):
        if e.control.value == 'Eliminar':
            campo_id = self.resposta['dados_ajustaveis'][self.posicao]['campo_id']
            nome_campo = next(
                (op['nome'] for op in self.opcoes_label if op['id'] == campo_id),
                'este campo'
            )
            self.dialogo.content = ft.Text(f"Tem a certeza que deseja eliminar o campo \u00ab{nome_campo}\u00bb?")
            if self.dialogo not in self.page.overlay:
                self.page.overlay.append(self.dialogo)
            self.dialogo.open = True
            self.page.update()
        else:
            self.resposta['dados_ajustaveis'][self.posicao]['campo_id'] = e.control.value
            self.marcar_modificado()

    def _atualizar_valor(self, e):
        self.resposta['dados_ajustaveis'][self.posicao]['valor'] = e.control.value
        self.marcar_modificado()

    def marcar_modificado(self):
        self.valor_textfield.bgcolor = COR_MODIFICADO
        self.valor_textfield.update()

    def marcar_salvo(self):
        self.valor_textfield.bgcolor = COR_NORMAL
        self.valor_textfield.update()
        # Limpar a tag de novo quando for salvo
        if 'novo' in self.resposta['dados_ajustaveis'][self.posicao]:
            self.resposta['dados_ajustaveis'][self.posicao]['novo'] = False

    def _eliminar_confirmado(self, e):
        self.dialogo.open = False
        self.resposta['dados_ajustaveis'].pop(self.posicao)
        self.atualizar_estrutura_de_campos()
        self.page.update()

    def _eliminar_cancelado(self, e):
        self.dialogo.open = False
        self.label_dropdown.value = self.resposta['dados_ajustaveis'][self.posicao]['campo_id']
        self.label_dropdown.update()
        self.page.update()


class estruturaDeCampos():
    def __init__(self, page, resposta, atualizar_estrutura_de_campos):
        self.page = page
        self.resposta = resposta
        self.atualizar_estrutura_de_campos = atualizar_estrutura_de_campos
        self.area_rolavel = ft.Column(spacing=20,
            expand=True,
            scroll=ft.ScrollMode.AUTO,
            alignment=ft.MainAxisAlignment.START,
            horizontal_alignment=ft.CrossAxisAlignment.START)
        self.construir_area_rolavel()

    def construir_area_rolavel(self):
        # Guardar instâncias para evitar garbage collection dos event handlers
        self._campos = {}
        self._campos_ajustaveis = []

        # Campo nome (mais largo)
        inst_nome = campoFixo(self.page, self.resposta, 'nome', largura=(100, 400))
        self._campos['nome'] = inst_nome
        nome = ft.Row([inst_nome.campo_ui], spacing=20, alignment=ft.MainAxisAlignment.START)

        # Construir colunas com os restantes campos fixos (ordenados por 'ordem')
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
            inst = campoFixo(self.page, self.resposta, campo)
            self._campos[campo] = inst
            if i % 2 == 0:
                primeira_coluna.append(inst.campo_ui)
            else:
                segunda_coluna.append(inst.campo_ui)

        for i, dado in enumerate(self.resposta['dados_ajustaveis']):
            inst_aj = campoAjustavel(
                self.page, self.resposta, i,
                self.resposta['campos_ajustaveis'],
                self.atualizar_estrutura_de_campos
            )
            self._campos_ajustaveis.append(inst_aj)
            if (i + len(outros_fixos)) % 2 == 0:
                primeira_coluna.append(inst_aj.campo_ui)
            else:
                segunda_coluna.append(inst_aj.campo_ui)

        # --- Observer: ligar dependências entre campos fixos ---
        # Se filtro != 'id', este campo depende do valor de outro campo
        for campo_nome, inst in self._campos.items():
            filtro = self.resposta['campos_fixos'].get(campo_nome, {}).get('filtro')
            if filtro and filtro != 'id' and filtro in self._campos:
                self._campos[filtro].registar_dependente(inst)

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
        dados = dados.data
        dados['subtitulo'] = self.baixar_subtitulo()
        return dados

    def baixar_subtitulo(self):
        subtitulo = 'SPG ABIO'

        if self.id == '0':
            return subtitulo + ' - Novo(a) ' + self.tipo

        if self.tipo == 'associado':
            id_matricula = self.page.cliente.table('rel_mat_asso').select('matricula_id').eq('associado_id', self.id).execute()
            id_matricula = id_matricula.data[0]['matricula_id']

            dados = self.page.cliente.table('vw_dados_com_associado').select('*').eq('id_matricula', id_matricula).execute()
            dados = dados.data[0]

            for k, v in dados.items():
                if k[:3] == 'id_' or k == 'primeiro_associado':
                    continue
                else:
                    subtitulo += ' - ' + v
                if k == 'matricula':
                    break
        else:
            dados = self.page.cliente.table('vw_dados_com_associado').select('*').eq(f'id_{self.tipo}', self.id).execute()
            dados = dados.data[0]

            for k, v in dados.items():
                if k == self.tipo:
                    break
                if k[:3] == 'id_' or k == 'primeiro_associado':
                    continue
                else:
                    subtitulo += ' - ' + v

        return subtitulo
        

            

class baseFormulario():
    def __init__(self, page):
        self.page = page

        # Criar classes
        self.dados = dadosFormulario(self.page)                                          # Modelo de dados
        self.estrutura = estruturaDeCampos(self.page, self.dados.resposta,               # Estrutura de campos
                        self.atualizar_estrutura_de_campos)    
        self.janela_rotulo = janelaNovoRotulo(self.page, self.dados.resposta,            # Janela de rotulos
                        self.atualizar_estrutura_de_campos)    
        self.botoes = botoesFormulario(self.page, self.dados.resposta,                   # Botões
                        self.ver_janela_nrotulo,
                        self.atualizar_estrutura_de_campos)
        # Lista plana com todas as instâncias que suportam marcar_salvo()
        self.botoes.campos_ref = (
            list(self.estrutura._campos.values()) +
            self.estrutura._campos_ajustaveis
        )

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
        # Atualizar a lista de referências dos campos nos botões, caso a classe já tenha inicializado botoes
        if hasattr(self, 'botoes'):
            self.botoes.campos_ref = (
                list(self.estrutura._campos.values()) +
                self.estrutura._campos_ajustaveis
            )
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
                    ft.Text(self.dados.resposta['subtitulo'], weight="bold"),
                    ft.Text(self.dados.titulo, size=24, weight="bold"),
                    ft.Divider(),
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



def iniciar_formulario(tipo = 'uprod', id = 12):
    def main(page: ft.Page):
        from escudo_supabase import login_supabase
        page.cliente = login_supabase()
        page.session.set("tipo", tipo)
        page.session.set("id", id)
        page.avancar_dados = {}
        page.voltar_dados = {}
        
        baseFormulario(page)
    return main

if __name__ == "__main__":
    ft.app(target=iniciar_formulario(), view=ft.AppView.WEB_BROWSER)
