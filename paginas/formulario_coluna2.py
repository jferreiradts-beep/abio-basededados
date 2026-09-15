import flet as ft
import pandas as pd
import base64
import unicodedata
from datetime import datetime
from formatar_campos import aplicarMascara

MASCARA_CPF_CNPJ = aplicarMascara("###.###.###-##; ##.###.###/####-##")
MASCARA_DATA = aplicarMascara("data")
from gerar_certificado import montarCertificado, montarFRI
from escudo_supabase import aviso


def funcao_menu_lateral(page, *args):
    tipo = page.session.get('tipo')
    if tipo == 'escopo':
        return menuEscopo(page, *args)
    else:
        return ft.Column([])

######################
# Menu do escopo
######################

# Classe registro de atividade

class escopoNaoSalvo():
    def __init__(self, tipo = False, fechar_janela = None):
        self.fechar_janela = fechar_janela
        self.tipo = tipo
        self.janela = self.montar_janela()

    def montar_janela(self):
        aviso = 'Antes de adicionar novas informações, preencha os dados no formulário principal e salve.'
        aviso_tipo = 'Antes de cadastrar produtos, selecione o tipo de escopo.'
        
        if self.tipo:
            self.aviso = ft.Text(aviso_tipo)
        else:
            self.aviso = ft.Text(aviso)
        
        return ft.AlertDialog(
            title=ft.Text("Atenção!"),
            content=ft.Container(
                width=300, height=150,
                content=ft.Column([self.aviso], scroll=ft.ScrollMode.AUTO)
            ),
            actions=[
                ft.TextButton("Fechar", on_click=self.fechar_janela)
            ]
        )
        

class verAcontecimentos():
    def __init__(self, page, id, ao_salvar=None):
        self.page = page
        self.id = id
        self.ao_salvar = ao_salvar
        self.modificado = False
        self.acontecimentos_dados = []
        self.exibir_janela_contecimentos()

    def obter_dados(self):
        try:
            resposta = self.page.cliente.rpc(
                'obter_acontecimentos_escopo',
                {'p_id': int(self.id)}
            ).execute()
            dados = resposta.data
            if isinstance(dados, str):
                import json
                dados = json.loads(dados)
            return dados or []
        except Exception as err:
            print(f"Erro ao obter acontecimentos do escopo: {err}")
            return []

    def carregar_tabela(self):
        self.lista_acontecimentos.controls.clear()
        idx = 0
        self._ac_larguras = [90, 180, 270]
        for a in self.acontecimentos_dados:
            raw_data = a.get("data") or ""
            try:
                dt_str = datetime.strptime(raw_data, "%Y-%m-%d").strftime("%d/%m/%Y")
            except Exception:
                dt_str = raw_data

            tipo_str = a.get("tipo") or ""
            obs_str = a.get("observacoes") or ""

            valores = [dt_str, tipo_str, obs_str]
            cor_fundo = ft.Colors.WHITE if idx % 2 == 0 else ft.Colors.GREY_100

            linha = ft.GestureDetector(
                content=ft.Container(
                    content=ft.Row(
                        [ft.Container(
                            content=ft.Text(v, size=13, overflow=ft.TextOverflow.ELLIPSIS),
                            width=w, padding=ft.padding.symmetric(horizontal=8, vertical=10)
                        ) for v, w in zip(valores, self._ac_larguras)],
                        spacing=0,
                    ),
                    bgcolor=cor_fundo,
                ),
                on_double_tap_down=lambda e, id_ac=a.get('id'): self.abrir_dialog_acontecimento(id_ac)
            )
            self.lista_acontecimentos.controls.append(linha)
            idx += 1

    def abrir_dialog_acontecimento(self, id_acontecimento):
        from pag_matricula import janelaAcontecimento
        
        if hasattr(self, 'janela_acontecimentos') and self.janela_acontecimentos:
            self.janela_acontecimentos.open = False
            self.page.update()

        janelaAcontecimento(
            self.page, 
            self.id, 
            id_acontecimento, 
            ao_salvar=self.ao_acontecimento_salvo, 
            escopo=True,
            ao_fechar=self.ao_fechar_edicao
        )

    def ao_acontecimento_salvo(self, novos_dados=None):
        self.modificado = True
        if novos_dados and isinstance(novos_dados, list) and len(novos_dados) > 0 and isinstance(novos_dados[0], dict) and 'tipo' in novos_dados[0]:
            self.acontecimentos_dados = novos_dados
        else:
            self.acontecimentos_dados = self.obter_dados()
        self.carregar_tabela()

    def ao_fechar_edicao(self):
        if hasattr(self, 'janela_acontecimentos') and self.janela_acontecimentos:
            self.janela_acontecimentos.open = True
            self.page.update()

    def fechar_janela_acontecimentos(self, e=None):
        if self.modificado and self.ao_salvar and callable(self.ao_salvar):
            self.ao_salvar()

        self.janela_acontecimentos.open = False
        self.page.update()

    def montar_janela(self):
        if str(self.id) == '0' or self.page.session.get('id') == '0':
            return escopoNaoSalvo(fechar_janela=self.fechar_janela_acontecimentos).janela

        self.acontecimentos_dados = self.obter_dados()

        self._ac_larguras = [90, 180, 270]
        self._ac_titulos = ["Data", "Tipo", "Observações"]

        cabecalho_ac_row = ft.Container(
            content=ft.Row(
                [ft.Container(
                    content=ft.Text(t, weight="bold", size=13),
                    width=w, padding=ft.padding.symmetric(horizontal=8, vertical=10)
                ) for t, w in zip(self._ac_titulos, self._ac_larguras)],
                spacing=0,
            ),
            bgcolor=ft.Colors.GREY_300,
            border_radius=ft.border_radius.only(top_left=4, top_right=4),
        )

        self.lista_acontecimentos = ft.ListView(expand=True, spacing=0, padding=0)
        self.carregar_tabela()

        tab_ac_container = ft.Container(
            content=ft.Column([
                cabecalho_ac_row,
                self.lista_acontecimentos,
            ], spacing=0, expand=True),
            expand=True
        )

        btn_novo_ac = ft.ElevatedButton(
            "Novo acontecimento",
            on_click=lambda e: self.abrir_dialog_acontecimento(0),
            style=ft.ButtonStyle(padding=ft.padding.symmetric(horizontal=16, vertical=10))
        )

        btn_fechar = ft.TextButton("Fechar", on_click=self.fechar_janela_acontecimentos)

        return ft.AlertDialog(
            title=ft.Text("Acontecimentos"),
            content=ft.Container(
                width=580, height=400,
                content=tab_ac_container,
                padding=5
            ),
            actions=[
                btn_novo_ac,
                btn_fechar
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )

    def exibir_janela_contecimentos(self):
        self.janela_acontecimentos = self.montar_janela()
        self.page.overlay.append(self.janela_acontecimentos)
        self.janela_acontecimentos.open = True
        self.page.update()


# Classe ver ou editar produtos

class verProdutos():
    def __init__(self, page, tipo_escopo=None):
        self.page = page
        self.tipo_escopo = tipo_escopo
        self.dados_produtos = self.obter_dados()
        self.exibir_janela_produtos()

    def obter_dados(self):
        resposta = self.page.cliente.rpc('obter_produtos', {'p_escopo_id': self.page.session.get('id')}).execute()
        return resposta.data or {}

    def montar_janela(self):
        if self.page.session.get('id') == '0':
            return escopoNaoSalvo(fechar_janela=self.fechar_janela_produtos).janela

        if self.tipo_escopo is None:
            return escopoNaoSalvo(tipo=True, fechar_janela=self.fechar_janela_produtos).janela

        grupos_produtos = self.dados_produtos.get(str(self.tipo_escopo), [])
            
        self.coluna_produtos = ft.Column([], scroll=ft.ScrollMode.AUTO)
        for grupo in grupos_produtos:
            lista_txt = ', '.join(sorted(grupo['produtos'], key=lambda s: unicodedata.normalize('NFD', s)))
            subcoluna = ft.Column([
                    ft.Text(grupo['grupo'], size=16, weight="bold"),
                    ft.Text(lista_txt + '.'),
                    ft.Divider()
                ])
            self.coluna_produtos.controls.append(subcoluna)

        # Criar janela
        janela = ft.AlertDialog(
            title=ft.Text(self.page.session.get("nome_escopo")),
            content=ft.Container(
                width=560, height=400,
                content=self.coluna_produtos
            ),
            actions=[
                ft.TextButton("Editar", on_click=self.editar_janela_produtos),
                ft.TextButton("Ok", on_click=self.cancelar_janela_produtos)
            ]
        )

        return janela

    def editar_janela_produtos(self, e):
        self.cancelar_janela_produtos(e)
        self.page.avancar_dados['tipo_escopo'] = self.tipo_escopo
        self.page.go('/produtos')

    def cancelar_janela_produtos(self, e):
        self.janela_produtos.open = False
        self.page.update()

    def exibir_janela_produtos(self):
        self.janela_produtos = self.montar_janela()
        self.page.overlay.append(self.janela_produtos)
        self.janela_produtos.open = True
        self.page.update()

    def fechar_janela_produtos(self, e):
        self.janela_produtos.open = False
        self.page.update()

class nomesCertificado():
    def __init__(self, page):
        self.page = page
        self.nomes = self.obter_dados()
        self.exibir_janela_nomes_certificados()

    def obter_dados(self):
        resposta = self.page.cliente.rpc('obter_associados_por_escopo', {'p_escopo_id': self.page.session.get('id')}).execute()
        return resposta.data
    
    def montar_janela(self):
        if self.page.session.get('id') == '0':
            return escopoNaoSalvo(fechar_janela=self.fechar_janela_nomes).janela

        todos_sem_vinculo = all([not nome['vinculo'] for nome in self.nomes['associados']])
        
        self.lista_checkboxes = []
        coluna_nomes = ft.Column([], scroll=ft.ScrollMode.AUTO)
        for nome in self.nomes['associados']:
            chk = ft.Checkbox(value= todos_sem_vinculo or nome['vinculo'], data=nome['id'])
            txt = ft.Text(value=f'{nome["nome"]} - {MASCARA_CPF_CNPJ.aplicar_mascara(nome["cpf"])}', weight="bold", width=350)
            self.lista_checkboxes.append(chk)
            coluna_nomes.controls.append(ft.Row([chk, txt]))

        self.mensagem = ft.Text('É necessário selecionar pelo menos um nome para o certificado.')
        return ft.AlertDialog(
            title=ft.Text("Nomes no certificado"),
            content=ft.Container(
                width=400, height=250,
                content=ft.Column([
                    self.mensagem,
                    ft.Divider(),
                    coluna_nomes
                    ])
            ),
            actions=[
                ft.TextButton("Salvar", on_click=self.salvar_janela_nomes),
                ft.TextButton("Fechar", on_click=self.fechar_janela_nomes)
            ]
        )

    def fechar_janela_nomes(self, e):
        self.janela_nomes.open = False
        self.page.update()

    def salvar_janela_nomes(self, e):
        if all([not chk.value for chk in self.lista_checkboxes]):
            self.mensagem.color = ft.Colors.RED
            self.mensagem.update()
            return
        elif all([chk.value for chk in self.lista_checkboxes]):
            lista_nomes = []
        else:
            lista_nomes = [chk.data for chk in self.lista_checkboxes if chk.value]

        self.page.cliente.rpc('atualizar_relacao_nm', {'p_tabela': 'rel_ass_esc', 'p_coluna_fixa': 'escopo_id',
                                                        'p_valor_fixo': self.page.session.get('id'),
                                                        'p_ids_opostos': lista_nomes}).execute()
        self.fechar_janela_nomes(e)

    def exibir_janela_nomes_certificados(self):
        self.janela_nomes = self.montar_janela()
        self.page.overlay.append(self.janela_nomes)
        self.janela_nomes.open = True
        self.page.update()


class imprimirEscopo():
    def __init__(self, page, escopo = True):
        self.page = page
        self.escopo = escopo
        self.salvar_certificado()

    def salvar_certificado(self):
        import os
        import time
        try:
            if self.escopo:
                resposta = self.page.cliente.table('configuracoes').select('assinatura, assinatura_cargo').eq('id', 1).execute()
                if resposta.data:
                    config = resposta.data[0]
                    nome_assinante = config.get('assinatura') or "WELLINGTON MARY"
                    cargo_assinante = config.get('assinatura_cargo') or "DIRETOR TÉCNICO DA ABIO"
                else:
                    nome_assinante = "WELLINGTON MARY"
                    cargo_assinante = "DIRETOR TÉCNICO DA ABIO"
                
                certificado = montarCertificado(self.page.cliente, self.page.session.get('id'), nome_assinante, cargo_assinante)
                buffer_pdf = certificado.gerar_certificado()
            else:
                certificado = montarFRI(self.page.cliente, self.page.session.get('id'))
                buffer_pdf = certificado.gerar_fri()

            nome_arquivo = certificado.nome_arquivo
            
            # Diretório temporário na pasta assets (resolvido a partir deste script)
            caminho_dir = os.path.join(os.path.dirname(__file__), 'assets', 'certificados')
            os.makedirs(caminho_dir, exist_ok=True)
            
            # Limpar arquivos antigos (mais de 1 hora) para não lotar o disco
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
            with open(caminho_arquivo, "wb") as file_out:
                file_out.write(buffer_pdf)

            print(f"Certificado gerado: {nome_arquivo}")
            self.page.launch_url(url=f"/certificados/{nome_arquivo}", web_window_name="_blank")
        except ValueError as e:
            aviso(self.page, str(e))
        except Exception as e:
            aviso(self.page, f"Erro inesperado ao gerar documento: {str(e)}")

        
class menuEscopo():
    def __init__(self, page, dados, atualizar_formulario):
        self.page = page
        self.dados = dados
        self.atualizar_formulario = atualizar_formulario
        self.opcoes_mun_estados = None  # <-- inicializa a variavel; carrega quando estiver pronto,
                                        # a partir do formulario base
        self.menu = self.montar_menu()


    def obter_dados(self):
        try:
            escopo_id = int(self.page.session.get('id') or 0)
        except (ValueError, TypeError):
            escopo_id = 0
            
        dados = self.page.cliente.rpc('obter_info_escopo', {'p_escopo_id': escopo_id}).execute()
        return dados.data

    @staticmethod
    def _fmt_data(valor):
        """Converte AAAA-MM-DD para DD/MM/AAAA; devolve o original se falhar."""
        try:
            return datetime.strptime(valor, '%Y-%m-%d').strftime('%d/%m/%Y')
        except (ValueError, TypeError):
            return valor or ''

    def ver_registro_acontecimentos(self, e):
        id = self.page.session.get('id')
        verAcontecimentos(self.page, id, ao_salvar=self.atualizar_dados_basicos)

    def atualizar_dados_basicos(self):
        dados = self.obter_dados()
        self.txt_validade.value = self._fmt_data(dados['validade'])
        self.txt_ultima_atividade.value = dados['ultima_atualizacao']
        self.txt_validade.update()
        self.txt_ultima_atividade.update()
        
    def visualizar_produtos(self, e):
        tipo_escopo = self.dados['dados_fixos'].get('nome')
        if tipo_escopo:
            try:
                res = self.page.cliente.table('tipo_escopo').select('nome').eq('id', int(tipo_escopo)).execute()
                if res.data:
                    self.page.session.set("nome_escopo", res.data[0]['nome'])
            except Exception as err:
                print(f"Erro ao buscar nome do escopo: {err}")
        verProdutos(self.page, tipo_escopo=tipo_escopo)


    def editar_nomes_certificado(self, e):
        nomesCertificado(self.page)

    def imprimir_certificado(self, e):
        imprimirEscopo(self.page)
        
    def ficha_rastrabilidade_individual(self, e):
        imprimirEscopo(self.page, escopo=False)        
            
    def montar_menu(self):
        dados = self.obter_dados()
        self.txt_validade = ft.Text(self._fmt_data(dados['validade']), weight="bold")
        self.txt_ultima_atividade = ft.Text(dados['ultima_atualizacao'], weight="bold")

        return ft.Column([
            ft.Text('Escopo é a descrição formal das atividades orgânicas que serão avaliadas pelo SPG para fins de conformidade.'),
            ft.Divider(),
            ft.Text('Fazer mais:', size=16, weight="bold"),
            ft.Row([ft.Text('Ver registro de acontecimentos:', width=250),
                    ft.ElevatedButton('Ok', on_click=self.ver_registro_acontecimentos, width=50, height=30)],
                    vertical_alignment=ft.CrossAxisAlignment.CENTER),
            ft.Row([ft.Text('Ver ou editar produtos:', width=250),
                    ft.ElevatedButton('Ok', on_click=self.visualizar_produtos, width=50, height=30)],
                    vertical_alignment=ft.CrossAxisAlignment.CENTER),
            ft.Row([ft.Text('Editar nomes no certificado:', width=250),
                    ft.ElevatedButton('Ok', on_click=self.editar_nomes_certificado, width=50, height=30)],
                    vertical_alignment=ft.CrossAxisAlignment.CENTER),
            ft.Row([ft.Text('Imprimir certificado:', width=250),
                    ft.ElevatedButton('Ok', on_click=self.imprimir_certificado, width=50, height=30)],
                    vertical_alignment=ft.CrossAxisAlignment.CENTER),
            ft.Row([ft.Text('Ficha de rastrabilidade individual:', width=250),
                    ft.ElevatedButton('Ok', on_click=self.ficha_rastrabilidade_individual, width=50, height=30)],
                    vertical_alignment=ft.CrossAxisAlignment.CENTER),
            ft.Row([ft.Text('')]),
            ft.Divider(),
            ft.Text('Dados básicos:', size=16, weight="bold"),
            ft.Row([ft.Text('Validade:'), self.txt_validade], spacing=10),
            ft.Row([ft.Text('Última atividade:'), self.txt_ultima_atividade], spacing=10),
            ],
            spacing=10)