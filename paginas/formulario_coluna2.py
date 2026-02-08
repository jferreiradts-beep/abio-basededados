import flet as ft
import pandas as pd
import os
import base64
from datetime import datetime
from formatar_campos import formatar_cpf_cnpj, formatar_data
from gerar_certificado import montarCertificado


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
        print(self.tipo)
        self.janela = self.montar_janela()

    def montar_janela(self):
        aviso = 'Antes de adicionar novas informações, preencha os dados no formulário principal e salve.'
        aviso_tipo = 'Antes de cadastrar produtos, selecione o tipo de escopo.'
        
        if self.tipo:
            self.aviso = ft.Text(aviso_tipo)
        else:
            self.aviso = ft.Text(aviso)
        
        print(self.aviso)
        
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
    def __init__(self, page):
        self.page = page
        self.exibir_janela_contecimentos()

    def obter_dados(self):
        dicionario_acontecimentos = self.page.cliente.table('tipo_acontecimento').select('*').execute()
        resposta = self.page.cliente.table('acontecimentos').select('*').eq('escopo_id', self.page.session.get('id')).execute()
        return dicionario_acontecimentos.data, resposta.data

    def montar_lista_acontecimentos(self):
        self.dados_acontecimentos = self.obter_dados()
        
        # Ordenação por data e ordem
        ordem_tipos = {tipo['id']: tipo['ordem'] for tipo in self.dados_acontecimentos[0]}
        acontecimentos = sorted(
            self.dados_acontecimentos[1], 
            key=lambda x: (x['data'], ordem_tipos.get(x['tipo_id'], 0)), 
            reverse=True
        )
        lista_acontecimentos = ft.Column([], scroll=ft.ScrollMode.AUTO, expand=True)
        for acontecimento in acontecimentos:
            tipo_acontecimento = next((item for item in self.dados_acontecimentos[0] if item['id'] == acontecimento['tipo_id']), None)
            txt_data = ft.Text(value=acontecimento['data'], width=100, weight="bold" if tipo_acontecimento['destaque'] else "normal")
            txt_tipo = ft.Text(value=tipo_acontecimento['nome'], width=200, weight="bold" if tipo_acontecimento['destaque'] else "normal")
            txt_observacoes = ft.Text(value=acontecimento['observacoes'], width=240, weight="bold" if tipo_acontecimento['destaque'] else "normal")
            btn_editar = ft.IconButton(ft.Icons.EDIT, on_click=lambda e, a=acontecimento: self.editar_acontecimento(e, a))
            lista_acontecimentos.controls.append(ft.Row([
                txt_data,
                txt_tipo,
                txt_observacoes,
                btn_editar
            ]))
        return lista_acontecimentos

    def montar_linha_botoes(self, inicial = True):
        self.botoes = {
            'alterar': ft.TextButton("Alterar", visible=False),
            'eliminar': ft.TextButton("Eliminar", visible=False),
            'voltar': ft.TextButton("Voltar", on_click=self.voltar_acontecimento, visible=False),
            'adicionar': ft.TextButton("Adicionar", on_click=self.adicionar_acontecimento),
            'fechar': ft.TextButton("Fechar", on_click=self.fechar_janela_acontecimentos)
        }

        return ft.Row([
            self.botoes['alterar'],
            self.botoes['eliminar'],
            self.botoes['voltar'],
            self.botoes['adicionar'],
            self.botoes['fechar']
        ], alignment=ft.MainAxisAlignment.END)

    # Ações de botões
    def editar_acontecimento(self, e, x):
        # Limpar aviso se existir
        if self.formulario_acontecimento['aviso'].value != '':
            self.formulario_acontecimento['aviso'].value = ''
            self.formulario_acontecimento['aviso'].update()

        for chave in ['data', 'tipo_id', 'observacoes']:
            self.formulario_acontecimento[chave].value = x[chave]
            self.formulario_acontecimento[chave].update()

        for nome in ['adicionar', 'fechar']:
            self.botoes[nome].visible = False 
        for nome in ['alterar', 'eliminar', 'voltar']:
            self.botoes[nome].visible = True

        self.botoes['alterar'].on_click = lambda e, idx=x['id']: self.alterar_acontecimento(e, idx)
        self.botoes['eliminar'].on_click = lambda e, idx=x['id']: self.eliminar_acontecimento(e, idx)

        self.linha_botoes.update()

    def alterar_acontecimento(self, e, idx):
        dados = {chave: valor.value for chave, valor in self.formulario_acontecimento.items() if chave != 'aviso'}
        dados['escopo_id'] = self.page.session.get('id')

        try:
            data_formatada = datetime.strptime(dados['data'], '%Y-%m-%d')
            dados['data'] = data_formatada.strftime('%Y-%m-%d')
                
        except ValueError:
            self.formulario_acontecimento['aviso'].value = "Por favor, insira uma data válida (AAAA-MM-DD)."
            self.formulario_acontecimento['aviso'].update()
            return
        
        self.page.cliente.table('acontecimentos').update(dados).eq('id', idx).execute()
        self.lista_acontecimentos.controls.clear()
        self.lista_acontecimentos.controls.extend(self.montar_lista_acontecimentos().controls)
        self.lista_acontecimentos.update()
        self.voltar_acontecimento(e)

    def eliminar_acontecimento(self, e, idx):
        self.page.cliente.table('acontecimentos').delete().eq('id', idx).execute()
        self.lista_acontecimentos.controls.clear()
        self.lista_acontecimentos.controls.extend(self.montar_lista_acontecimentos().controls)
        self.lista_acontecimentos.update()
        self.voltar_acontecimento(e)

    def voltar_acontecimento(self, e):
        # Limpar aviso se existir
        if self.formulario_acontecimento['aviso'].value != '':
            self.formulario_acontecimento['aviso'].value = ''
            self.formulario_acontecimento['aviso'].update()

        self.formulario_acontecimento, layout_acontecimento = self.montar_formulario()
        self.formulario_layout.controls.clear()
        self.formulario_layout.controls.append(layout_acontecimento)
        self.formulario_layout.update()
        
        for nome in ['alterar', 'eliminar', 'voltar']:
            self.botoes[nome].visible = False
        for nome in ['adicionar', 'fechar']:
            self.botoes[nome].visible = True
        self.linha_botoes.update()

    def adicionar_acontecimento(self, e):
        dados = {chave: valor.value for chave, valor in self.formulario_acontecimento.items() if chave != 'aviso'}
        dados['escopo_id'] = self.page.session.get('id')

        try:
            data_formatada = datetime.strptime(dados['data'], '%Y-%m-%d')
            dados['data'] = data_formatada.strftime('%Y-%m-%d')
                
        except ValueError:
            self.formulario_acontecimento['aviso'].value = "Por favor, insira uma data válida (AAAA-MM-DD)."
            self.formulario_acontecimento['aviso'].update()
            return
        
        self.page.cliente.table('acontecimentos').insert(dados).execute()
        self.lista_acontecimentos.controls.clear()
        self.lista_acontecimentos.controls.extend(self.montar_lista_acontecimentos().controls)
        self.lista_acontecimentos.update()
        self.voltar_acontecimento(e)


    def fechar_janela_acontecimentos(self, e):
        self.janela_acontecimentos.open = False
        self.page.update()    



    # Montar janela
    def montar_formulario(self):
        formulario_campos = {}
        formulario_campos['data'] = ft.TextField(label="Data", width=150,
            on_change= lambda e: (setattr(e.control, 'value', formatar_data(e.control.value)), e.control.update())
        )
        
        opcoes_acontecimento = []
        for item in sorted(self.dados_acontecimentos[0], key=lambda x: x['ordem']):
            opcoes_acontecimento.append(ft.dropdown.Option(key=str(item['id']), text=item['nome']))
        formulario_campos['tipo_id'] = ft.Dropdown(options=opcoes_acontecimento, width=340, label='Tipo de acontecimento')
        formulario_campos['observacoes'] = ft.TextField(label="Observações", width=500)
        formulario_campos['aviso'] = ft.Text(value="", color=ft.Colors.RED)

        formulario_layout = ft.Column([
                        ft.Row([
                            formulario_campos['data'],
                            formulario_campos['tipo_id'],
                        ]),
                        formulario_campos['observacoes'],
                        formulario_campos['aviso']
                    ])
        
        return formulario_campos, formulario_layout



    def montar_janela(self):
        if self.page.session.get('id') == '0':
            return escopoNaoSalvo(fechar_janela=self.fechar_janela_acontecimentos).janela

        self.lista_acontecimentos = self.montar_lista_acontecimentos()
        self.formulario_acontecimento, self.formulario_layout = self.montar_formulario()        
        self.linha_botoes = self.montar_linha_botoes()

        # Montar janela
        return ft.AlertDialog(
            title=ft.Text("Acontecimentos"),
            content=ft.Container(
                width=610, height=400,
                content=ft.Column([
                    ft.Divider(),
                    self.lista_acontecimentos, 
                    ft.Divider(),
                    self.formulario_layout,
                ], expand=True)
            ),
            actions= [self.linha_botoes]
        )


    def exibir_janela_contecimentos(self):
        self.janela_acontecimentos = self.montar_janela()
        self.page.overlay.append(self.janela_acontecimentos)
        self.janela_acontecimentos.open = True
        self.page.update()


# Classe ver ou editar produtos

class verProdutos():
    def __init__(self, page):
        self.page = page
        self.dados_produtos = self.obter_dados()
        self.exibir_janela_produtos()

    def obter_dados(self):
        resposta = self.page.cliente.rpc('obter_produtos', {'p_escopo_id': self.page.session.get('id')}).execute()
        return resposta.data

    def montar_janela(self):
        # Caso não tenha um escopo salvo, exibe mensagem
        if self.page.session.get('id') == '0' or self.page.session.get('tipo_escopo') is None:
            if self.page.session.get('id') == '0':
                return escopoNaoSalvo(fechar_janela=self.fechar_janela_produtos).janela
            else:
                return escopoNaoSalvo(tipo=True, fechar_janela=self.fechar_janela_produtos).janela

        escopo = next(iter(self.dados_produtos))
        grupos_produtos = self.dados_produtos[escopo]
            
        self.coluna_produtos = ft.Column([], scroll=ft.ScrollMode.AUTO)
        for grupo in grupos_produtos:
            lista_txt = ', '.join(sorted(grupo['produtos']))
            subcoluna = ft.Column([
                    ft.Text(grupo['grupo'], size=16, weight="bold"),
                    ft.Text(lista_txt + '.'),
                    ft.Divider()
                ])
            self.coluna_produtos.controls.append(subcoluna)

        # Criar janela
        janela = ft.AlertDialog(
            title=ft.Text(escopo),
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
            txt = ft.Text(value=f'{nome["nome"]} - {formatar_cpf_cnpj(nome["cpf"])}', weight="bold", width=350)
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

class novaUProd():
    def __init__(self, page, dados, atualizar_formulario, opcoes_mun_estados):
        self.page = page
        self.dados = dados
        self.atualizar_formulario = atualizar_formulario
        self.opcoes_mun_estados = opcoes_mun_estados
        self.exibir_janela_nova_uprod()


    def linha_mun_estados(self, estado = None):
        # Definir estados e municípios
        lista_municipios = self.opcoes_mun_estados.loc[self.opcoes_mun_estados['SIGLA_UF'] == estado, 'NM_MUN']
        lista_municipios = [ft.dropdown.Option(x) for x in lista_municipios]

        dd_estado = ft.Dropdown(label='Estado', value=estado, options= lista_estados, width=150,
                                on_change = self.atualizar_dd_municipios) 
        dd_municipio = ft.Dropdown(label='Município', options= lista_municipios, width=150)

        return ft.Row([
            dd_estado,
            dd_municipio
        ])

    def atualizar_dd_municipios(self, e):
        lista_municipios = self.opcoes_mun_estados.loc[self.opcoes_mun_estados['SIGLA_UF'] == e.control.value, 'NM_MUN']
        self.dd_municipio.options = [ft.dropdown.Option(x) for x in lista_municipios]
        self.dd_municipio.update()
    
    def montar_janela_nova_uprod(self):
        if self.page.session.get('id') == '0':
            return escopoNaoSalvo(fechar_janela=self.fechar_janela_nuprod).janela

        lista_estados = [ft.dropdown.Option(x) for x in self.opcoes_mun_estados['SIGLA_UF'].unique()]
        self.txt_nome_uprod = ft.TextField(label='Nome da unidade de produção')
        self.txt_endereco = ft.TextField(label= 'Endereço')
        self.dd_estado = ft.Dropdown(label='Estado', options= lista_estados, width=150, on_change= self.atualizar_dd_municipios)
        self.dd_municipio = ft.Dropdown(label='Município', options= None, width=150)

        return ft.AlertDialog(
            title=ft.Text("Adicionar unidade de produção"),
            content=ft.Container(
                width=350, height=200,
                content=ft.Column([
                    self.txt_nome_uprod,
                    self.txt_endereco,
                    ft.Row([
                        self.dd_estado,
                        self.dd_municipio
                    ])
                ])
            ),
            actions=[
                ft.TextButton("Salvar", on_click=self.salvar_uprod),
                ft.TextButton("Cancelar", on_click=self.fechar_janela_nuprod)
            ]
        )

    def fechar_janela_nuprod(self, e):
        self.janela_nova_uprod.open = False
        self.page.update()

    def salvar_uprod(self, e):
        dados = {
            'nome': self.txt_nome_uprod.value,
            'endereco': self.txt_endereco.value,
            'estado': self.dd_estado.value,
            'municipio': self.dd_municipio.value
        }
        try:
            salvar_uprod = self.page.cliente.table('uprod').insert(dados).execute()
            novo_id = salvar_uprod.data[0]['id']
            self.dados['opcoes']['uprod_id'].append({'id': novo_id, 'nome': dados['nome']})
            self.dados['dados_fixos']['uprod_id'] = novo_id

            self.atualizar_formulario()
            self.page.snack_bar = ft.SnackBar(ft.Text(f"Unidade de produção criada com sucesso! ID: {novo_id}") )

        except Exception as e:
            self.page.snack_bar = ft.SnackBar( ft.Text(f"Erro ao criar rotulo: {e}"), bgcolor="red" )

        finally:
            self.cancelar_uprod(None)
            self.page.snack_bar.open = True

    def exibir_janela_nova_uprod(self):
        self.janela_nova_uprod = self.montar_janela_nova_uprod()
        self.page.overlay.append(self.janela_nova_uprod)
        self.janela_nova_uprod.open = True
        self.page.update()


class imprimirEscopo():
    def __init__(self, page):
        self.page = page
        self.salvar_certificado()

    def salvar_certificado(self):
        certificado = montarCertificado(self.page.cliente, self.page.session.get('id'))
        buffer_pdf = certificado.gerar_certificado()
        
        pdf_base64 = base64.b64encode(buffer_pdf).decode('utf-8')
        data_url = f"data:application/pdf;base64,{pdf_base64}"
        self.page.launch_url(url=data_url, web_window_name="_blank")
        
        
class menuEscopo():
    def __init__(self, page, dados, atualizar_formulario):
        self.page = page
        self.dados = dados
        self.atualizar_formulario = atualizar_formulario
        self.opcoes_mun_estados = None  # <-- inicializa a variavel; carrega quando estiver pronto,
                                        # a partir do formulario base
        self.menu = self.montar_menu()


    def obter_dados(self):
        dados = self.page.cliente.rpc('obter_info_escopo', {'p_escopo_id': self.page.session.get('id')}).execute()
        return dados.data

   
    def ver_registro_acontecimentos(self, e):
        verAcontecimentos(self.page)
        
    def visualizar_produtos(self, e):
        verProdutos(self.page)


    def adicionar_unidade_producao(self, e):
        novaUProd(self.page, self.dados, self.atualizar_formulario, self.opcoes_mun_estados)

    def editar_nomes_certificado(self, e):
        nomesCertificado(self.page)

    def imprimir_certificado(self, e):
        imprimirEscopo(self.page)
        
    def ficha_rastrabilidade_individual(self, e):
        print('ficha_rastrabilidade_individual')
        
            
    def montar_menu(self):
        dados = self.obter_dados()
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
            ft.Row([ft.Text('Adicionar unidade de produção:', width=250),
                    ft.ElevatedButton('Ok', on_click=self.adicionar_unidade_producao, width=50, height=30)],
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
            ft.Divider(),
            ft.Text('Dados básicos:', size=16, weight="bold"),
            ft.Row([ft.Text('Validade:'), ft.Text(dados['validade'], weight="bold")], spacing=10),
            ft.Row([ft.Text('Última atividade:'), ft.Text(dados['ultima_atualizacao'], weight="bold")], spacing=10),
            
            ],
            spacing=10)