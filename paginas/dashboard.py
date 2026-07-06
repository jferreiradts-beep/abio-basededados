import flet as ft
import pandas as pd
import numpy as np

import os
import re
import geopandas as gpd
import matplotlib
matplotlib.use('Agg') # <--- Evita erros de GUI/Thread no Flet
import matplotlib.pyplot as plt
import matplotlib.colors
import tempfile
import math


class janelaNovaMatricula():
    def __init__(self, page, grupo_id):
        self.page = page

        # Criar campos
        grupos = self.page.cliente.table('grupo').select('id, nome').execute()
        lista_grupos = []
        for grupo in grupos.data:
            lista_grupos.append(ft.dropdown.Option(key = grupo['id'], text = grupo['nome']))

        self.grupo = ft.Dropdown(label='Grupo', value=grupo_id, options=lista_grupos)
        self.matricula = ft.TextField(label='Matricula')
        self.mensagem = ft.Text(value="", size=10, color="red")
        
        self.janela= ft.AlertDialog(
            title=ft.Text("Nova matricula"),
            content=ft.Container(
                width=350, height=150,
                content=ft.Column([
                    self.grupo, 
                    self.matricula,
                    ft.Row([self.mensagem])
                ])
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=self.fechar_janela_nova_matricula),
                ft.TextButton("Criar", on_click=self.salvar_nova_matricula)
            ]
        )

        self.page.overlay.append(self.janela)
        self.janela.open = True
        self.page.update()

    def fechar_janela_nova_matricula(self, e):
        self.janela.open = False
        self.page.update()

    def salvar_nova_matricula(self, e):
        self.mensagem.value = ""
        self.janela.update()
        
        # Testar matricula
        if not re.fullmatch(r'^\d{2}-\d{3}$', self.matricula.value):
            self.mensagem.value = "Matricula inválida"
            self.janela.update()
            return
        
        # Salvar matricula
        try:
            resposta = self.page.cliente.table('matricula').insert({
                'grupo_id': self.grupo.value,
                'nome': self.matricula.value
            }).execute()

            novo_id = resposta.data[0]['id']

            self.page.session.set('id', novo_id)
            
            self.janela.open = False
            self.page.update()
            
            self.page.go('/matricula')

        except Exception as error:
            print("ERROR", error)
            erro_str = str(error).lower()
            if '23505' in erro_str or 'duplicate key' in erro_str:
                self.mensagem.value = f"A matrícula {self.matricula.value} já está atribuída."
            else:
                self.mensagem.value = f"Erro ao salvar matricula: {error}"
            self.janela.update()

class gridCards:
    def __init__(self, valores):
        self.valores = valores
        self.cards = self.criar_cards()
        

    def criar_cards(self):
        cards = []
        self.textos = []
        for i in range(8):
            altura = 80 if i < 4 else 100 # Primeira linha menor
            texto_valor = ft.Text(
                self.valores[f'c{i+1}']['valor'],
                weight=ft.FontWeight.BOLD,
                size=16,
                text_align=ft.TextAlign.CENTER
            )
            self.textos.append(texto_valor)

            card = ft.Container(
                content=ft.Column([
                    ft.Text(self.valores['c'+str(i+1)]['texto'], size=14, text_align=ft.TextAlign.CENTER),
                    texto_valor
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    width=127,
                    height=altura,
                    bgcolor=ft.Colors.GREEN_100, 
                    border_radius=10,
                    padding=10)

            cards.append(card)
        return cards

    def montar_layout(self):
        linha1 = ft.Row(self.cards[:4])
        linha2 = ft.Row(self.cards[4:])

        return ft.Container(
                width=560,
                height=250,
                bgcolor=ft.Colors.GREY_200,
                border_radius=10,
                padding=10,
                content=ft.Column([
                    ft.Text('Dados gerais', size=18, weight="bold", text_align='Center'),
                    linha1, linha2
                    ], spacing=10)
                )

    def atualizar_cards(self, novos_valores):
        for i, texto_valor in enumerate(self.textos):
            texto_valor.value = novos_valores[f'c{i+1}']['valor']
            if texto_valor.page:
                texto_valor.update()  # ← atualiza o widget no app apenas se já estiver na tela

class painelMapa:
    def __init__(self, page, dados):
        self.page = page
        self.dados = dados.dados
    
    def executar_mapa(self):
        # Carregar shp com caminhos absolutos
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        mapa_path = os.path.join(BASE_DIR, 'mapa', 'RJeAdjacencias_100km.geojson')
        limites_path = os.path.join(BASE_DIR, 'mapa', 'EstadoRJ.geojson')

        mapa = gpd.read_file(mapa_path)
        mapa_limites = gpd.read_file(limites_path)

        # Cruzar com dados
        escopos_pMun = self.dados.groupby(['estado', 'municipio'])['id_escopo'].count().reset_index()
        mapa_escopos = mapa.merge(
            escopos_pMun,
            how='left',
            left_on=['SIGLA_UF', 'NM_MUN'],
            right_on=['estado', 'municipio']
        )
        mapa_escopos = mapa_escopos[(mapa_escopos['SIGLA_UF'] == 'RJ') | (mapa_escopos['id_escopo'].notna())]
        mapa_escopos['escopos_log'] = mapa_escopos['id_escopo'].apply(lambda x: np.log(x) if pd.notnull(x) and x > 0 else None)

        # Preparar a legenda
        min_val = mapa_escopos['id_escopo'].min()
        max_val = math.ceil(mapa_escopos['id_escopo'].max() / 10)*10
        q1 = min_val + (max_val - min_val) / 3
        q2 = min_val + 2 * (max_val - min_val) / 3

        valores_reais = [min_val, round(q1), round(q2), max_val]
        log_ticks = [0] + [np.log(x) for x in valores_reais[1:]]

        # Fazer a figura
        fig, ax = plt.subplots(figsize=(5.6, 2.5))

        mapa_escopos.plot(
            column='escopos_log',
            cmap='Greens',         # branco → verde escuro
            linewidth=0.2,
            edgecolor='gray',
            ax=ax,
        )
        mapa_limites.plot(
            ax=ax,
            facecolor='none',
            edgecolor='black',
            linewidth=1,
        )

        # Inserir a legenda
        vmax = np.log(max_val)
        sm = plt.cm.ScalarMappable(cmap='Greens', norm=matplotlib.colors.Normalize(vmin=0, vmax=vmax))
        sm._A = []

        # Colorbar com ticks reais
        cbar = fig.colorbar(sm, ax=ax)
        cbar.set_ticks(log_ticks)
        cbar.set_ticklabels([f"{int(x)}" for x in valores_reais])

        # Finalização
        plt.axis('off')
        plt.tight_layout()

        # Salvar em memória (BytesIO) e converter para Base64
        import io
        import base64
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=200, transparent=True, bbox_inches='tight', pad_inches=0)
        plt.close(fig)
        buf.seek(0)
        img_base64 = base64.b64encode(buf.read()).decode('utf-8')
        return img_base64

    def montar_mapa(self):
        # Cria o container placeholder e guarda a referência
        self.container_mapa = ft.Container(
            width=410, height=250, bgcolor=ft.Colors.GREY_200, border_radius=10,
            content=ft.Stack([
                ft.Container(
                    content=ft.Text(
                        value='Escopos por município',
                        size=18,
                        weight='bold'
                        ),
                    left=10,
                    top=10
                    ),
                ft.Container(
                    content=ft.ProgressRing(),
                    alignment=ft.alignment.center,
                )
                ])
            )
        return self.container_mapa
    
    def atualizar_mapa(self):
        img_base64 = self.page.session.get('mapa')

        if img_base64 is None:
            img_base64 = self.executar_mapa()
            self.page.session.set('mapa', img_base64)

        # Atualiza o conteúdo do container existente
        self.container_mapa.content = ft.Stack([
                ft.Container(
                    content=ft.Image(src_base64=img_base64, fit=ft.ImageFit.CONTAIN),
                    alignment=ft.alignment.center,
                    width=410,
                    height=250,
                    padding=ft.padding.only(top=35, bottom=10, left=10, right=10)
                ),
                ft.Container(
                    content=ft.Text(
                        value='Escopos por município',
                        size=18,
                        weight='bold'
                        ),
                    left=10,
                    top=10
                    )
                ])
        self.container_mapa.update()

class colunaIndividual:
    def __init__(self, page, dados, nome, filtro):
        self.page = page
        self.nome = nome
        self.dados = dados
        self.filtro = filtro

        self.coluna_seguinte = None
        self.lista = ft.ListView(expand=True, spacing=5, padding=5)


        self.carregar_conteudo()
        self.criar_botao_novo()

    def definir_largura(self):
        if self.nome == 'matricula':
            return 370
        elif self.nome == 'escopo':
            return 115
        else:
            return 205

    def carregar_conteudo(self):    
        self.lista.controls.clear()
        for idx, nome in self.dados.filtrar_dados(self.nome, self.filtro[self.nome]['valor']):
            texto = ft.Text(nome, size=14,
                            style=ft.TextStyle(
                                weight=ft.FontWeight.BOLD if idx == self.filtro[self.nome]['id'] else ft.FontWeight.NORMAL,
                                color=ft.Colors.GREEN_900 if idx == self.filtro[self.nome]['id'] else ft.Colors.BLACK,
                                decoration=ft.TextDecoration.UNDERLINE if idx == self.filtro[self.nome]['id'] else ft.TextDecoration.NONE
                            ))
            
            item = ft.GestureDetector(
                content=ft.Container(content=texto, padding=0),
                on_tap=lambda e, id_selecionado=idx: self.selecionar(id_selecionado),
                on_double_tap=lambda e, id_selecionado=idx: self.ir_para_formulario(id_selecionado)
            )

            self.lista.controls.append(item)

        try:
            self.lista.update()
        except AssertionError:
            pass

    def criar_botao_novo(self):
        self.botao_novo = ft.ElevatedButton(
            'Novo',
            width=75, height=25,
            style=ft.ButtonStyle(
                color=ft.Colors.GREEN,
                text_style=ft.TextStyle(size=11, weight=ft.FontWeight.BOLD)
            ),
            on_click=lambda e: self.ir_para_formulario('0')
        )

    def ir_para_formulario(self, id_selecionado):
        # 'matricula' tem navegação própria — tratar primeiro e retornar
        if self.nome == 'matricula':
            self.page.voltar_dados['endereco'].append(self.page.route)
            self.page.voltar_dados['dados_pagina'].append({'dashboard_filtro': self.filtro})
            if id_selecionado == '0':
                janelaNovaMatricula(self.page, self.filtro['grupo']['id'])
            else:
                self.page.session.set('id', id_selecionado)
                self.page.go('/matricula')
            return

        # Para nucleo, grupo e escopo: tipo = nome
        self.page.session.set('tipo', self.nome)

        # Dados extras que cada painel precisa passar para o formulário
        avancar_extras = {
            'grupo':  {'nucleo_id': self.filtro['nucleo']['id']},
            'uprod': {'matricula_id': self.filtro['matricula']['id']},
            'escopo': {'uprod_id': self.filtro['uprod']['id']},
        }
        self.page.avancar_dados.update(avancar_extras.get(self.nome, {}))

        self.page.voltar_dados['endereco'].append(self.page.route)
        self.page.voltar_dados['dados_pagina'].append({'dashboard_filtro': self.filtro})

        id_final = str(int(id_selecionado)) if id_selecionado != '0' else '0'
        self.page.session.set('id', id_final)

        self.page.go('/formulario')

    def selecionar(self, id_selecionado):
        # Desmarca se clicar no mesmo id, marca se clicar em outro
        if id_selecionado == self.filtro[self.nome]['id']:
            id_selecionado = 0
        self.filtro[self.nome]['id'] = id_selecionado
        self.carregar_conteudo()

        # Atualizar colunas seguintes
        # valor_pai: o ID selecionado que alimenta a próxima coluna.
        # Depois da primeira coluna seguinte, o pai passa a ser 0 (nada selecionado),
        # de modo que colunas mais distantes fiquem vazias.
        valor_pai = id_selecionado
        coluna = self.coluna_seguinte
        seguinte_primeiro = True
        while coluna:
            self.filtro[coluna.nome]['valor'] = valor_pai
            self.filtro[coluna.nome]['id'] = 0
            coluna.carregar_conteudo()
            coluna.lista.update()

            if seguinte_primeiro:
                coluna.botao_novo.disabled = True if valor_pai == 0 else False
                seguinte_primeiro = False
            else:
                coluna.botao_novo.disabled = True
            coluna.botao_novo.update()

            # A partir daqui o pai é sempre 0: colunas mais à frente ficam vazias
            valor_pai = 0
            coluna = coluna.coluna_seguinte

        # Chamar a produção de dados para produzir o card grid
        # no caso de escopos — se desselecionou (id=0), usa o filtro do pai para actualizar os cards
        if self.nome == 'escopo':
            valor_para_cards = self.filtro[self.nome]['valor'] if id_selecionado == 0 else id_selecionado
            self.dados.filtrar_dados(self.nome, valor_para_cards)

    def montar_coluna(self):
        return ft.Container(
            width=self.definir_largura(),
            height=300,
            bgcolor=ft.Colors.GREEN_100,
            border_radius=10,
            padding=10,
            content=ft.Column([
                    ft.Text(dadosDashboard.MAPA_LABEL.get(self.nome, self.nome), size=16, weight="bold"),
                    self.lista,
                    ft.Container(self.botao_novo, alignment=ft.alignment.center)],
                alignment=ft.MainAxisAlignment.START,
                horizontal_alignment=ft.CrossAxisAlignment.START,
                spacing=10))

        
class colunasDashboard:
    def __init__(self, page, dados):
        self.page = page
        self.dados = dados
        self.construir_colunas()

    
    def construir_colunas(self):
        self.filtro = self.page.session.get('dashboard_filtro')
        if self.filtro is None:
            self.filtro = {
                'nucleo':    {'valor': 'all', 'id': 0},
                'grupo':     {'valor': 0, 'id': 0},
                'matricula': {'valor': 0, 'id': 0},
                'uprod':     {'valor': 0, 'id': 0},
                'escopo':    {'valor': 0, 'id': 0}
            }

        self.colunas = [
            colunaIndividual(self.page, self.dados, 'nucleo',    self.filtro),
            colunaIndividual(self.page, self.dados, 'grupo',     self.filtro),
            colunaIndividual(self.page, self.dados, 'matricula', self.filtro),
            colunaIndividual(self.page, self.dados, 'uprod',     self.filtro),
            colunaIndividual(self.page, self.dados, 'escopo',    self.filtro)
        ]

        for i in range(len(self.colunas) - 1):
            self.colunas[i].coluna_seguinte = self.colunas[i + 1]

        for coluna in self.colunas[1:]:
            if self.filtro[coluna.nome]['valor'] == 0:
                coluna.botao_novo.disabled = True
            else:
                coluna.botao_novo.disabled = False

    def limpar_filtro(self, e):
        self.filtro['nucleo']    = {'valor': 'all', 'id': 0}
        self.filtro['grupo']     = {'valor': 0, 'id': 0}
        self.filtro['matricula'] = {'valor': 0, 'id': 0}
        self.filtro['uprod']     = {'valor': 0, 'id': 0}
        self.filtro['escopo']    = {'valor': 0, 'id': 0}

        self.colunas[0].selecionar(0)

    def linha_inferior(self):
        return ft.Row(
            [coluna.montar_coluna() for coluna in self.colunas],
            spacing=10
        )



class dadosDashboard:
    # Chaves internas = nomes das colunas da view (sem acento, sem maiúsculas)
    MAPA_LABEL = {
        'nucleo':    'Núcleos',
        'grupo':     'Grupos',
        'matricula': 'Matrículas',
        'uprod':     'Unid. Produção',
        'escopo':   'Escopos'
    }
    MAPA_COLUNA_FILTRO = {
        'grupo':     'id_nucleo',
        'matricula': 'id_grupo',
        'uprod':     'id_matricula',
        'escopo':    'id_uprod'
    }

    def __init__(self, cliente, situacoes=None):
        if situacoes is None:
            situacoes = ['ativo', 'suspenso', 'cancelado']
        self.atualizar_cards = None
        self.baixar_dados(cliente, situacoes)

    def baixar_dados(self, cliente, situacoes):
        # Baixar dados
        self.dados = cliente.table('vw_dados_com_associado').select('*').execute()
        df = pd.DataFrame(self.dados.data)
        if 'situacao' in df.columns:
            df = df[df['situacao'].isin(situacoes) | df['situacao'].isna() | (df['situacao'] == '')]
        self.dados = df
        
        self.dados_de_associados = cliente.table('vw_escopo_cpf_visivel').select('*').execute()
        self.dados_de_associados = pd.DataFrame(self.dados_de_associados.data)


    def definir_coluna(self, nome):
        return nome  # a chave interna é o próprio nome da coluna na view

    def criar_filtro(self, nome, valor_filtro):
        if valor_filtro == 'all':
            return pd.Series([True] * len(self.dados))
        elif valor_filtro == 0:
            return pd.Series([False] * len(self.dados))

        # Cada coluna é filtrada pelo ID do seu pai na hierarquia:
        # Grupos → filtrado por id_nucleo, Matriculas → por id_grupo, Escopos → por matricula
        coluna_filtro = self.MAPA_COLUNA_FILTRO.get(nome)
        if coluna_filtro:
            return self.dados[coluna_filtro] == valor_filtro
        return None

    def dados_cardGrid(self, dados_filtrados, ass_filtrados):

        # Calcular os valores
        grupos = dados_filtrados['id_grupo'].nunique()
        matriculas = dados_filtrados['matricula'].nunique()
        escopos = dados_filtrados['id_escopo'].nunique()
        hoje = pd.Timestamp.today()
        um_mes = hoje + pd.DateOffset(months=1)
        quatro_meses = hoje + pd.DateOffset(months=4)
        vencidos = dados_filtrados.loc[dados_filtrados['validade'] <= hoje, 'id_escopo'].nunique()
        escopos_1m = dados_filtrados.loc[(dados_filtrados['validade'] > hoje) & (dados_filtrados['validade'] <= um_mes), 'id_escopo'].nunique()
        escopos_4m = dados_filtrados.loc[(dados_filtrados['validade'] > um_mes) & (dados_filtrados['validade'] <= quatro_meses), 'id_escopo'].nunique()
     
        # Retornar os valores
        return {
            'c1': {'texto': 'Grupos', 'valor': grupos},
            'c2': {'texto': 'Matrículas', 'valor': matriculas},
            'c3': {'texto': 'Associados', 'valor': ass_filtrados},
            'c4': {'texto': 'Escopos ativos', 'valor': escopos},
            'c5': {'texto': 'Escopos a vencer (4m)', 'valor': escopos_4m},
            'c6': {'texto': 'Escopos a vencer (1m)', 'valor': escopos_1m},
            'c7': {'texto': 'Escopos vencidos', 'valor': vencidos},
            'c8': {'texto': 'Escopos\ninativos', 'valor': 0}
        }

    def dados_colunas(self, dados_filtrados, coluna):
        dados = dados_filtrados[[f'id_{coluna}', coluna]].copy()
        # Remover linhas onde o ID da coluna é NaN (ex.: matrícula sem uprod)
        dados = dados.dropna(subset=[f'id_{coluna}'])
        dados = dados.drop_duplicates(subset=[f'id_{coluna}']).sort_values(by=coluna)
        # Converter para int Python puro (pandas usa float64 quando há NULLs)
        idx = [int(x) for x in dados[f'id_{coluna}']]

        if coluna == 'matricula':
            extra = dados_filtrados[['id_matricula', 'primeiro_associado']].drop_duplicates(subset=['id_matricula'])
            dados = dados.merge(extra, on='id_matricula', how='left')
            dados['primeiro_associado'] = dados['primeiro_associado'].fillna('')
            linhas = np.where(
                dados['primeiro_associado'] != '',
                dados['matricula'] + ' - ' + dados['primeiro_associado'],
                dados['matricula']
            ).tolist()
        else:
            linhas = dados[coluna].to_list()

        return zip(idx, linhas)

    def filtrar_dados(self, nome, valor_filtro):
        # Definir coluna e criar filtro
        coluna = self.definir_coluna(nome)
        filtro = self.criar_filtro(nome, valor_filtro)

        # Filtrar dados
        dados_filtrados = self.dados.loc[filtro].copy()
        dados_filtrados['validade'] = pd.to_datetime(dados_filtrados['validade'], errors='coerce')
        ass_filtrados = self.dados_de_associados.loc[self.dados_de_associados['id_escopo'].isin(dados_filtrados['id_escopo'])].copy()
        ass_filtrados = ass_filtrados['id_associado'].nunique()

        # Construir dados dos cards e atualizar cards
        if valor_filtro != 0:
            dados_cards = self.dados_cardGrid(dados_filtrados, ass_filtrados)
            self.atualizar_cards(dados_cards)

        # Construir tuple de alimentação de coluna
        dados_pcoluna = self.dados_colunas(dados_filtrados, coluna)
        return dados_pcoluna
        

class DashboardBase:
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = "SPG ABIO"
        self.page.scroll = "auto"

        # Dados cards zerados
        valores_cards_inicial =  {
            'c1': {'texto': 'Grupos', 'valor': 0},
            'c2': {'texto': 'Matrículas', 'valor': 0},
            'c3': {'texto': 'Associados', 'valor': 0},
            'c4': {'texto': 'Escopos ativos', 'valor': 0},
            'c5': {'texto': 'Escopos a vencer (4m)', 'valor': 0},
            'c6': {'texto': 'Escopos a vencer (1m)', 'valor': 0},
            'c7': {'texto': 'Escopos vencidos', 'valor': 0},
            'c8': {'texto': 'Escopos\ninativos', 'valor': 0}
        }

        # Criar componentes
        situacoes = ['ativo']
        resposta = self.page.cliente.table('configuracoes').select('suspenso, cancelado').eq('id', 1).execute()
        if resposta.data:
            config = resposta.data[0]
            if config.get('suspenso', True): situacoes.append('suspenso')
            if config.get('cancelado', True): situacoes.append('cancelado')
        else:
            situacoes = ['ativo', 'suspenso', 'cancelado']
        
        self.dados = dadosDashboard(self.page.cliente, situacoes)
        self.cards = gridCards(valores_cards_inicial)
        self.mapa = painelMapa(self.page, self.dados)

        # Callback de dados para cards
        self.dados.atualizar_cards = self.cards.atualizar_cards

        self.colunas = colunasDashboard(self.page, self.dados)
        self.montar_layout()
        
        # Chamada assíncrona (na verdade, sequencial pós-render) para carregar o mapa
        self.mapa.atualizar_mapa()

    def criar_menu(self):
        menu = ft.PopupMenuButton(
            icon=ft.Icons.MENU,
            items=[
                ft.PopupMenuItem(text="Configurações", on_click=lambda _: self.page.go("/configuracoes"))
            ]
        )
        return menu

    def baixar_csv_mapa(self, e):
        import os
        import time
        import pandas as pd
        
        try:
            resposta = self.page.cliente.table('vw_mapa_mapa').select('*').execute()
            if not resposta.data:
                self.page.snack_bar = ft.SnackBar(ft.Text("Nenhum dado encontrado na view."), bgcolor="orange")
                self.page.snack_bar.open = True
                self.page.update()
                return

            df = pd.DataFrame(resposta.data)
            csv_str = df.to_csv(index=False, sep=';', encoding='utf-8-sig')

            nome_arquivo = f"mapa_dados_{int(time.time())}.csv"
            caminho_dir = os.path.join(os.path.dirname(__file__), 'assets', 'certificados')
            os.makedirs(caminho_dir, exist_ok=True)
            
            agora = time.time()
            for f in os.listdir(caminho_dir):
                caminho_f = os.path.join(caminho_dir, f)
                if os.path.isfile(caminho_f):
                    if agora - os.path.getmtime(caminho_f) > 3600:
                        try:
                            os.remove(caminho_f)
                        except Exception:
                            pass
            
            caminho_arquivo = os.path.join(caminho_dir, nome_arquivo)
            with open(caminho_arquivo, "w", encoding="utf-8-sig") as file_out:
                file_out.write(csv_str)
                
            self.page.launch_url(url=f"/certificados/{nome_arquivo}", web_window_name="_blank")
            
            self.page.snack_bar = ft.SnackBar(ft.Text("Download iniciado!"), bgcolor="green")
            self.page.snack_bar.open = True
            self.page.update()
            
        except Exception as erro:
            self.page.snack_bar = ft.SnackBar(ft.Text(f"Erro ao gerar CSV: {erro}"), bgcolor="red")
            self.page.snack_bar.open = True
            self.page.update()

    def montar_layout(self):
        # Cabeçalho
        cabecalho = ft.Row(
            [self.criar_menu(),
            ft.Text("SPG ABIO", size=24, weight="bold")],
            alignment=ft.MainAxisAlignment.START, spacing=20
        )

        # Linha superior
        self.mapa_montado = self.mapa.montar_mapa() # <-- para atualizar o mapa
        
        relatorios_container = ft.Container(
            width=130, height=250, bgcolor=ft.Colors.GREY_200, border_radius=10,
            padding=10,
            content=ft.Column([
                ft.Text("Relatórios", size=16, weight="bold"),
                ft.ElevatedButton(
                    "CNPO MAPA",
                    width=100, height=30,
                    style=ft.ButtonStyle(
                        text_style=ft.TextStyle(size=11, weight=ft.FontWeight.BOLD),
                    ),
                    on_click=self.baixar_csv_mapa),
                ft.ElevatedButton(
                    "Rel. Técnico",
                    width=100, height=30,
                    style=ft.ButtonStyle(
                        text_style=ft.TextStyle(size=11, weight=ft.FontWeight.BOLD),
                    ),
                    on_click=lambda _: (
                        self.page.voltar_dados['endereco'].append(self.page.route),
                        self.page.voltar_dados['dados_pagina'].append({'dashboard_filtro': self.colunas.filtro}),
                        self.page.avancar_dados.update({
                            'nucleo_id': self.colunas.filtro.get('nucleo', {}).get('id') or None,
                            'grupo_id': self.colunas.filtro.get('grupo', {}).get('id') or None}),
                        self.page.go('/painel_grupo')
                    )),
                ft.ElevatedButton(
                    "Rel. Financeiro",
                    width=100, height=30,
                    style=ft.ButtonStyle(
                        text_style=ft.TextStyle(size=11, weight=ft.FontWeight.BOLD),
                    ),
                    on_click=lambda _: (
                        self.page.voltar_dados['endereco'].append(self.page.route),
                        self.page.voltar_dados['dados_pagina'].append({'dashboard_filtro': self.colunas.filtro}),
                        self.page.go('/relatorio_financeiro')
                    )),
            ], alignment=ft.MainAxisAlignment.START, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        )
        
        linha_superior = ft.Row(
            [self.cards.montar_layout(), relatorios_container, self.mapa_montado],
            spacing=20
        )

        # Linha inferior
        linha_inferior = self.colunas.linha_inferior()

        # Montar layout
        self.page.add(
            ft.Row([
                ft.Column([
                cabecalho,
                linha_superior,
                linha_inferior
                ], 
                spacing=10,
                alignment=ft.MainAxisAlignment.START,
                )
            ], alignment=ft.MainAxisAlignment.CENTER)
        )


def iniciar_dashboard():
    def main(page: ft.Page):
        from escudo_supabase import login_supabase
        page.cliente = login_supabase()
        DashboardBase(page)
    return main

if __name__ == "__main__":
    ft.app(target=iniciar_dashboard(), view=ft.WEB_BROWSER)
