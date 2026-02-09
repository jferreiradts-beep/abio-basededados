import flet as ft
from escudo_supabase import login_supabase, aviso


class DialogoEditarControle():
    def __init__(self, page, atualizar_painel):
        self.page = page
        self.cliente = page.cliente
        self.atualizar_painel = atualizar_painel
        
        self.controle = None
        self.controle_id = None
        self.tipo = None
        
        self.montar_janela()

    def configurar(self, controle, controle_id, tipo):
        self.controle = controle
        self.controle_id = controle_id
        self.tipo = tipo
        
        # Atualiza UI do diálogo
        txt_titulo = 'Edite o nome do produto:' if self.tipo == 'produto' else 'Edite o nome do grupo:'
        self.janela.title.value = txt_titulo
        self.nome_corrigido.value = self.controle.value
        
        # Reseta estado visual dos botões
        self.conteiner_nome.height = 50
        self.conteiner_nome.content = self.nome_corrigido
        
        for botao in ['eliminar', 'salvar', 'cancelar']:
            self.botoes[botao].visible = True
        for botao in ['confirmar', 'voltar']:
            self.botoes[botao].visible = False
            
        # Atualiza visibilidade baseada no tipo
        if self.tipo != 'produto':
            self.botoes['eliminar'].visible = False
            self.botoes['confirmar'].visible = False
            self.botoes['voltar'].visible = False

        self.janela.update()

    def salvar(self, e):
        tabela = 'produtos' if self.tipo == 'produto' else 'grupo_prod'
        try:
            self.cliente.table(tabela).update({'nome': self.nome_corrigido.value}).eq('id', self.controle_id).execute()
            self.controle.value = self.nome_corrigido.value
            self.controle.update()
            self.fechar()
        except Exception as error:
            aviso(self.page, f"Erro ao salvar: {error}")

    def cancelar(self, e):
        self.fechar()

    def fechar(self):
        self.janela.open = False
        self.janela.update()

    def voltar(self, e):
        self.conteiner_nome.height = 50
        self.conteiner_nome.content = self.nome_corrigido
        self.conteiner_nome.update()

        for botao in ['eliminar', 'salvar', 'cancelar']:
            self.botoes[botao].visible = True
        for botao in ['confirmar', 'voltar']:
            self.botoes[botao].visible = False
        self.linha_botoes.update()

    def confirmar(self, e, txt_escreva):
        if txt_escreva == 'ELIMINAR':
            try:
                self.cliente.table('produtos').delete().eq('id', self.controle_id).execute()
                self.atualizar_painel()
                self.fechar()
            except Exception as error:
                aviso(self.page, f"Erro ao eliminar: {error}")

    def eliminar(self, e):
        self.conteiner_nome.height = 200
        escopos = self.page.cliente.table('rel_esc_prod').select('*', count='exact').eq('produto_id', self.controle_id).execute()
        txt_aviso = ft.Text(f"Confirmar a eliminação deste produto afetará {escopos.count} escopo{'s' if escopos.count > 1 else ''}. Para confirmar, escreva ELIMINAR abaixo e clique em Confirmar")
        txt_escreva = ft.TextField(label="ELIMINAR")
        self.conteiner_nome.content = ft.Column([self.nome_corrigido, ft.Divider(), txt_aviso, txt_escreva])
        self.conteiner_nome.update()
        
        for botao in ['eliminar', 'salvar', 'cancelar']:
            self.botoes[botao].visible = False
        for botao in ['confirmar', 'voltar']:
            self.botoes[botao].visible = True
        self.botoes['confirmar'].on_click = lambda e: self.confirmar(e, txt_escreva.value)
        self.linha_botoes.update()

    def momtar_linha_botoes(self):
        self.botoes = {
            'eliminar': ft.ElevatedButton("Eliminar", width=100, on_click=self.eliminar),
            'salvar': ft.ElevatedButton("Salvar", width=100, on_click=self.salvar),
            'cancelar': ft.ElevatedButton("Cancelar", width=100, on_click=self.cancelar),
            'confirmar': ft.ElevatedButton("Confirmar", width=100, visible=False),
            'voltar': ft.ElevatedButton("Voltar", width=100, on_click=self.voltar, visible=False)
        }

        return ft.Row(
            list(self.botoes.values()), 
            alignment=ft.MainAxisAlignment.END
        )

    def montar_janela(self):
        self.nome_corrigido = ft.TextField(label="Nome")
        self.conteiner_nome = ft.Container(
            width=400, height=50,
            content = self.nome_corrigido,
            padding=ft.padding.only(left=20, right=20)
        )
        self.linha_botoes = self.momtar_linha_botoes()

        self.janela = ft.AlertDialog(
            title=ft.Text("Editar"),
            content=self.conteiner_nome,
            actions= [self.linha_botoes]
        )

    def abrir_janela(self):
        # A janela já deve ter ser sido adicionada ao overlay na inicialização do painel
        self.janela.open = True
        self.janela.update()

class janelaNovoProduto():
    def __init__(self, page, opcoes_grupos, atualizar_painel, tipo= 'produto'):
        self.page = page
        self.cliente = page.cliente
        self.tipo = tipo
        self.opcoes_grupos = opcoes_grupos
        self.atualizar_painel = atualizar_painel

    def salvar(self, e):
        if self.tipo == 'produto':
            tabela = 'produtos'
            dados = {'nome': self.novo_nome.value, 'grupo_id': self.pertence.value}
        else:
            tabela = 'grupo_prod'
            dados = {'nome': self.novo_nome.value, 'tipo_escopo_id': self.page.get_session('tipo_escopo')}
       
        try:
            resposta = self.cliente.table(tabela).insert(dados).execute()
            self.cancelar(e)
            self.atualizar_painel()
            print(resposta)
        except Exception as error:
            aviso(self.page, f"Erro ao salvar: {error}")

    def cancelar(self, e):
        self.janela.open = False
        self.page.update()

    def montar_janela(self):
        txt_titulo = 'Novo produto:' if self.tipo == 'produto' else 'Novo grupo:'
        if self.tipo == 'produto':
            opcoes = [ft.dropdown.Option(key=g['id'], text=g['nome']) for g in self.opcoes_grupos]
            self.pertence = ft.Dropdown(label='Grupo', options=opcoes)
        else:
            nome_escopo = self.page.session.get('nome_escopo') or 'Teste'
            self.pertence = ft.Text(nome_escopo, size=18, weight="bold")
        
        self.novo_nome = ft.TextField(label="Nome")
        self.conteiner_nome = ft.Container(
            width=400, height=120,
            content = ft.Column([self.pertence, self.novo_nome]),
            padding=ft.padding.only(left=20, right=20)
        )
        self.janela = ft.AlertDialog(
            title=txt_titulo,
            content=self.conteiner_nome,
            actions= [
                ft.ElevatedButton("Salvar", on_click=self.salvar),
                ft.ElevatedButton("Cancelar", on_click=self.cancelar)
            ]
        )

    def abrir_janela(self):
        self.montar_janela()
        self.page.overlay.append(self.janela)
        self.janela.open = True
        self.page.update()


class metainformacaoEscopo():
    def __init__(self, page, dados):
        self.page = page
        self.dados = dados
        
        self.montar_painel()

    def montar_painel(self):
        grupo = ft.Row([
            ft.Text('Grupo:', weight="bold", size=18),
            ft.Text(self.dados.escopo['grupo'], size=18)
        ])
        matricula = ft.Row([
            ft.Text('Matrícula:', weight="bold", size=18),
            ft.Text(self.dados.escopo['matricula'], size=18)
        ])
        primeiro_associado = ft.Row([
            ft.Text('Primeiro Associado:', weight="bold", size=18),
            ft.Text(self.dados.escopo['primeiro_associado'], size=18)
        ])
        self.escopo_descricao = ft.Container(
            width=1000, height=75,
            bgcolor=ft.Colors.GREY_200,
            border_radius=10,
            padding=10,
            content=ft.Row([
                grupo, matricula, primeiro_associado
            ], spacing=40),
        )

class painelProdutos():
    def __init__(self, page, dados):
        self.page = page
        self.dados = dados

        self.produtos_selecionados = []
        # Inicialmente vazio ou loading
        self.lista_produtos = ft.Column([], scroll=ft.ScrollMode.ADAPTIVE, expand=True)

        # Inicializa o diálogo reutilizável
        self.dialogo_editar = DialogoEditarControle(page, self.atualizar_painel)
        self.page.overlay.append(self.dialogo_editar.janela)

        self.montar_painel()

    def marcar_produto(self, controle, e):
        controle.weight = ft.FontWeight.BOLD if e.control.value else ft.FontWeight.NORMAL
        controle.update()

    def editar_controle(self, controle, controle_id, tipo):
        # Reutiliza o diálogo existente
        self.dialogo_editar.configurar(controle, controle_id, tipo)
        self.dialogo_editar.abrir_janela()

    def verificar_produtos_selecionados(self):
        return [produto.data for produto in self.produtos_selecionados if produto.value]

    def montar_lista(self):
        # ... (rest of implementation)
        lista_temp = [] 
        
        for grupo in self.dados.lista_produtos:
            txt_grupo = ft.Text(grupo['nome'], size=18, weight="bold")
            dblc_grupo = ft.GestureDetector(
                content=txt_grupo,
                on_double_tap=lambda e, controle = txt_grupo, controle_id = grupo['id']: self.editar_controle(controle, controle_id, 'grupo')
            )
            linha = ft.Row([dblc_grupo])

            grupo_produtos = sorted(grupo['produtos'], key=lambda x: x['nome'])
            for i, produto in enumerate(grupo_produtos):
                if i % 4 == 0:
                    lista_temp.append(linha)
                    linha = ft.Row([])

                txt_produto = ft.Text(produto['nome'],
                                width=200,
                                size=14,
                                weight=ft.FontWeight.BOLD if produto['incluso'] else ft.FontWeight.NORMAL)
                ckb_produto = ft.Checkbox(
                    data=produto['id'],
                    value=produto['incluso'],
                    width=20,
                    on_change=lambda e, controle = txt_produto: self.marcar_produto(controle, e)
                )
                dblc_produto = ft.GestureDetector(
                    content=txt_produto,
                    on_double_tap=lambda e, controle = txt_produto, controle_id = produto['id']: self.editar_controle(controle, controle_id, 'produto')
                )

                linha.controls.append(ft.Row([ckb_produto, dblc_produto], spacing=5))
                self.produtos_selecionados.append(ckb_produto)

            lista_temp.append(linha)       
            lista_temp.append(ft.Divider())
        
        return lista_temp

    def carregar_conteudo_lazy(self):
        # Gera os controles pesados
        itens = self.montar_lista()
        
        # Atualiza a lista
        self.lista_produtos.controls = itens
        
        # Remove o loading e mostra o conteúdo real
        self.painel_produtos.content = self.lista_produtos
        self.painel_produtos.update()

    def atualizar_painel(self):
        self.dados.atualizar_dados()
        self.lista_produtos.controls.clear()
        self.produtos_selecionados = []
        
        # Recarrega
        self.carregar_conteudo_lazy()


    def montar_painel(self):
        # Initialmente mostra loading
        self.loading = ft.ProgressRing()
        self.painel_produtos = ft.Container(
            width=1000, height=450,
            bgcolor=ft.Colors.GREY_200,
            border_radius=10,
            padding=20,
            content=self.loading,
            alignment=ft.alignment.center
        )

class linhaBotoes():
    def __init__(self, page, dados, verificar_selecionados, atualizar_painel):
        self.page = page
        self.dados = dados
        self.verificar_selecionados = verificar_selecionados
        self.atualizar_painel = atualizar_painel
        self.montar_linha_botoes()

    def novo_produto(self, opcoes_grupos):
        self.janela_novo_produto = janelaNovoProduto(self.page, opcoes_grupos, self.atualizar_painel)
        self.janela_novo_produto.abrir_janela()

    def novo_grupo(self, e):
        self.janela_novo_grupo = janelaNovoProduto(self.page, [], tipo='grupo')
        self.janela_novo_grupo.abrir_janela()

    def salvar_produtos(self, e):
        produtos = self.verificar_selecionados()
        try:
            self.page.cliente.rpc('atualizar_relacao_nm', {'p_tabela': 'rel_esc_prod', 'p_coluna_fixa': 'escopo_id',
                                                            'p_valor_fixo': self.page.session.get('id'),
                                                            'p_ids_opostos': produtos}).execute()
            aviso(self.page, "Produtos salvos com sucesso")
        except Exception as error:
            aviso(self.page, f"Erro ao salvar: {error}")

    def voltar(self, e):
        self.page.go('/formulario')

    def montar_botoes(self):
        return ft.Row([
            ft.ElevatedButton('Novo produto', width=150, on_click=lambda e: self.novo_produto(self.dados.lista_produtos)),
            ft.ElevatedButton('Novo grupo', width=150, on_click=self.novo_grupo),
            ft.ElevatedButton("Salvar", width=150, on_click=self.salvar_produtos),
            ft.ElevatedButton("Voltar", width=150, on_click=self.voltar)
        ], spacing=30)

    def montar_linha_botoes(self):
        self.linha_botoes = ft.Container(
            width=1000, height=50,
            bgcolor=ft.Colors.GREY_200,
            border_radius=10,
            padding=10,
            content=ft.Row([self.montar_botoes()], alignment=ft.MainAxisAlignment.END),
            
        )


class dadosProdutos():
    def __init__(self, page):
        self.page = page
        self.cliente = page.cliente
        self.tipo_escopo = page.session.get("tipo_escopo")
        self.id_escopo = page.session.get("id")

        self.atualizar_dados()
        
    def atualizar_dados(self):
        lista_produtos = self.cliente.rpc('fn_produtos_por_escopo', {
            'p_tipo': self.tipo_escopo,
            'p_escopo_id': self.id_escopo}).execute()
        lista_produtos = lista_produtos.data

        self.escopo = lista_produtos['escopo']
        self.lista_produtos = sorted(lista_produtos['grupos'], key=lambda x: x['nome'])


class baseProdutos():
    def __init__(self, page):
        self.page = page
        self.page.title = "SPG ABIO: Editar produtos"
        self.page.scroll = 'auto'
        self.dados = dadosProdutos(page)
        self.construir_painel()

    def construir_painel(self):
        # 1️⃣ Cabeçalho
        cabecalho = ft.Row([
            ft.Text("☰", size=24),  # menu placeholder
            ft.Text("SPG ABIO", size=24, weight="bold"),
        ], alignment=ft.MainAxisAlignment.START, spacing=20)

        # 2️⃣ Painel de produtos
        self.escopo_descricao = metainformacaoEscopo(self.page, self.dados)
        self.painel_produtos = painelProdutos(self.page, self.dados)
        self.linha_botoes = linhaBotoes(self.page, self.dados, self.painel_produtos.verificar_produtos_selecionados, self.painel_produtos.atualizar_painel)
        
        # 3️⃣ Layout principal
        layout = ft.Row([
            ft.Column([
                cabecalho,
                self.escopo_descricao.escopo_descricao,
                self.painel_produtos.painel_produtos,
                self.linha_botoes.linha_botoes
            ], 
            alignment=ft.MainAxisAlignment.START)
        ],
        alignment=ft.MainAxisAlignment.CENTER)

        self.page.add(layout)
        
        # Gatilho para carregar o conteúdo pesado APÓS o render inicial
        self.painel_produtos.carregar_conteudo_lazy()


def iniciar_painel_produtos(tipo_escopo = 3, id_escopo = 1):
    def main(page: ft.Page):
        page.cliente = login_supabase()
        page.session.set("tipo_escopo", tipo_escopo)
        page.session.set("id", id_escopo)
        
        baseProdutos(page)
    return main

if __name__ == "__main__":
    ft.app(target=iniciar_painel_produtos())
