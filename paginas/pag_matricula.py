import flet as ft
from formatar_campos import formatar_cpf_cnpj
import re

class Eliminar:
    def __init__(self, page):
        self.page = page
        self.exibir_janela()

    def exibir_janela(self):
        self.montar_janela()
        self.page.overlay.append(self.janela_eliminar)
        self.janela_eliminar.open = True
        self.page.update()

    def montar_janela(self):
        self.janela_eliminar = ft.AlertDialog(
            title=ft.Text("Eliminar"),
            content=ft.Container(
                width=350, height=100,
                content=ft.Column([
                    ft.Text(f'Você tem certeza que deseja eliminar a matrícula {self.page.session.get("id")}? Todos os dados a ela vinculados serão eliminados.'),
                    ft.TextField(label="Digite ELIMINAR para confirmar")
                ])
            ),
            actions=[
                ft.ElevatedButton("Eliminar", on_click=lambda e: self.eliminar()),
                ft.ElevatedButton("Cancelar", on_click=lambda e: self.cancelar())
            ]
        )

    def eliminar(self):
        try:
            self.page.cliente.rpc('eliminar_e_atualizar', {
                'p_tabela': 'matriculas',
                'p_coluna': 'matricula',
                'p_id': self.page.session.get('id')
            }).execute()
            
            self.janela_eliminar.open = False
            self.page.overlay.remove(self.janela_eliminar)
            self.page.update()
            self.page.go('/dashboard')
            
        except Exception as e:
            print(f"Erro ao eliminar: {e}")
            self.page.snack_bar = ft.SnackBar(content=ft.Text(f"Erro: {e}"), bgcolor="red")
            self.page.snack_bar.open = True
            self.page.update()

    def cancelar(self):
        self.janela_eliminar.open = False
        self.page.update()

class janelaNovoAssociado:
    def __init__(self, page, coluna_matricula=None):
        self.page = page
        self.coluna_matricula = coluna_matricula
        self.exibir_janela()
        
    def montar_janela(self):
        nome = ft.TextField(label="Nome")
        cpf = ft.TextField(label="CPF",
                           on_change=lambda e: (setattr(e.control, "value", formatar_cpf_cnpj(e.control.value)),
                                                e.control.update()))
        self.campos = [nome, cpf]

        self.janela_novo_associado = ft.AlertDialog(
            title=ft.Text("Novo associado"),
            content=ft.Container(
                width=350, height=100,
                content=ft.Column(self.campos)
            ),
            actions=[
                ft.ElevatedButton("Ir", on_click=lambda e: self.ir()),
                ft.ElevatedButton("Cancelar", on_click=lambda e: self.cancelar())
            ]
        )

    def exibir_janela(self):
        self.montar_janela()
        self.page.overlay.append(self.janela_novo_associado)
        self.janela_novo_associado.open = True
        self.page.update()
        
    def ir(self):
        # Se o cpf não existir, ele cria um novo associado
        cpf= re.sub(r'\D', '', self.campos[1].value)
        if len(cpf) not in (11, 14):
            return

        print(self.page.session.get('id'))

        resposta = self.page.cliente.rpc('vincular_associado', {
            'p_nome': self.campos[0].value, 
            'p_cpf': cpf,
            'p_matricula': int(self.page.session.get('id'))
            }).execute()

        # Fechar a janela
        self.janela_novo_associado.open = False
        self.page.update()

        # Atualizar voltar_dados como faz ir_para_formulario
        matricula_id = self.page.session.get('id')
        self.page.voltar_dados['endereco'].append('/matricula')
        self.page.voltar_dados['dados_pagina'].append({'id': matricula_id})

        self.page.session.set("tipo", "associado")
        self.page.session.set('id', resposta.data)
        self.page.go('/formulario')

    def cancelar(self):
        self.janela_novo_associado.open = False
        self.page.update()
 
class botoesColMatricula:
    def __init__(self, page, ir_para_formulario):
        self.page = page
        self.ir_para_formulario = ir_para_formulario

        self.botoes = ft.Row(
            [
                ft.ElevatedButton("Novo associado", width=150, on_click=lambda e: self.novo_associado()),
                ft.ElevatedButton("Voltar", width=150, on_click=lambda e: self.voltar()),
            ], spacing=30
        )

    def novo_associado(self):
        janelaNovoAssociado(self.page, self.ir_para_formulario)

    def voltar(self):
        retorno = self.page.voltar_dados['endereco'][-1] if self.page.voltar_dados['endereco'] else '/dashboard'
        voltar_dados = self.page.voltar_dados['dados_pagina'][-1] if self.page.voltar_dados['dados_pagina'] else None
        if voltar_dados:
            for chave, valor in voltar_dados.items():
                self.page.session.set(chave, valor)
                
        self.page.voltar_dados['endereco'].pop()
        self.page.voltar_dados['dados_pagina'].pop()
        self.page.go(retorno)

class colunaMatricula:
    def __init__(self, page, id):
        self.page = page
        self.id = id

        self.dados = self.baixar_dados()

        self.selecionado = {
            'associado': None
        }
    
    def baixar_dados(self):
        dados = self.page.cliente.rpc('dados_de_matricula', {'matricula_input': self.id}).execute()
        return dados.data

    def ir_para_formulario(self, tipo, id_selecionado):
        self.page.session.set("tipo", tipo)
        self.page.session.set('id', id_selecionado)

        self.page.voltar_dados['endereco'].append('/matricula')
        self.page.voltar_dados['dados_pagina'].append({'id': self.id})

        self.page.go('/formulario')
        return

    def selecionar(self, tipo, id_selecionado):
        if tipo in ['associado']:
            self.selecionado[tipo] = id_selecionado
        else:
            self.selecionado = {
                'associado': None
            }

        self.montar_lista_associados()
        self.lista_associados.update()

    def montar_lista_associados(self):
        self.lista_associados.controls.clear()
        for associado in self.dados['associados']:
            idx = associado['id']
            nome = ft.Text(associado['nome'], size=14, width=300,
                            style=ft.TextStyle(
                                weight=ft.FontWeight.BOLD if idx == self.selecionado['associado'] else ft.FontWeight.NORMAL,
                                color=ft.Colors.GREEN_900 if idx == self.selecionado['associado'] else ft.Colors.BLACK,
                                decoration=ft.TextDecoration.UNDERLINE if idx == self.selecionado['associado'] else ft.TextDecoration.NONE))
            cpf_nao_formatado = associado['cpf']
            if len(cpf_nao_formatado) == 11:
                cpf_formatado = cpf_nao_formatado[:3] + '.' + cpf_nao_formatado[3:6] + '.' + cpf_nao_formatado[6:9] + '-' + cpf_nao_formatado[9:]
            elif len(cpf_nao_formatado) == 14:
                cpf_formatado = cpf_nao_formatado[:2] + '.' + cpf_nao_formatado[2:5] + '.' + cpf_nao_formatado[5:8] + '/' + cpf_nao_formatado[8:12] + '-' + cpf_nao_formatado[12:]
            else:
                cpf_formatado = cpf_nao_formatado

            cpf = ft.Text(cpf_formatado, size=14, width=200,
                            style=ft.TextStyle(
                                weight=ft.FontWeight.BOLD if idx == self.selecionado['associado'] else ft.FontWeight.NORMAL,
                                color=ft.Colors.GREEN_900 if idx == self.selecionado['associado'] else ft.Colors.BLACK,
                                decoration=ft.TextDecoration.UNDERLINE if idx == self.selecionado['associado'] else ft.TextDecoration.NONE))
            
            item = ft.GestureDetector(
                content=ft.Container(
                    content=ft.Row([nome, cpf]),
                    padding=0
                ),
                on_tap=lambda e, id_selecionado=idx: self.selecionar('associado', id_selecionado),
                on_double_tap=lambda e, id_selecionado=idx: self.ir_para_formulario('associado', id_selecionado)
            )
            self.lista_associados.controls.append(item)
       
    def montar_layout(self):
        # Linha de matrícula
        matricula = ft.Row(
            [ft.Text("Matrícula:", size=20, weight="bold", width=150),
            ft.TextField(value=self.dados['dados gerais']['matricula'], width=200, text_style=ft.TextStyle(size=20))],
            alignment=ft.MainAxisAlignment.START, spacing=10
        )

        #Linha do grupo
        lista_grupos = []
        for grupo in self.dados['grupos']:
            lista_grupos.append(ft.dropdown.Option(key=grupo['id'], text=grupo['nome']))

        grupo = ft.Row(
            [ft.Text("Grupo:", size=14, weight="bold", width=150),
            ft.Dropdown(value=self.dados['dados gerais']['grupo'], options=lista_grupos, 
                        expand=True, width=300,
                        text_style=ft.TextStyle(size=14))
            ],
            alignment=ft.MainAxisAlignment.START, spacing=10
        )

        # Linha lista de associados
        self.lista_associados = ft.ListView(expand=True, spacing=5, padding=5)
        self.montar_lista_associados()

        # Linha de botoes
        self.botoes = botoesColMatricula(self.page, self.ir_para_formulario)

        return ft.Column(
            [
                matricula,
                grupo,
                ft.Divider(),
                ft.Text("Associados", size=20, weight="bold"),
                ft.Container(
                    content=self.lista_associados,
                    width=560,
                    height=260,
                ),
                ft.Divider(),
                self.botoes.botoes
            ]
        )


class MatriculaBase:
    def __init__(self, page):
        self.page = page
        self.page.title = "SPG ABIO: Matrícula"
        self.page.scroll = "auto"
        self.matricula = self.page.session.get('id')

        self.coluna_matricula = colunaMatricula(self.page, self.matricula) 
        self.montar_layout()


    def criar_menu(self):
        menu = ft.PopupMenuButton(
            icon=ft.Icons.MENU,
            items=[]
        )
        return menu

    def montar_layout(self):
        # Cabeçalho
        cabecalho = ft.Row(
            [self.criar_menu(),
            ft.Text("SPG ABIO", size=24, weight="bold")],
            alignment=ft.MainAxisAlignment.START, spacing=20
        )

        # Coluna 1
        coluna1 = ft.Container(
            content=self.coluna_matricula.montar_layout(),
            width=560,
            height=550,
            bgcolor=ft.Colors.GREY_200,
            border_radius=10,
            padding=20,
        )

        # Coluna 2
        coluna2 = ft.Container(
            content=ft.Column(
                [
                    ft.Text("Observações", size=20, weight="bold"),
                ],
            ),
            width=560,
            height=550,
            bgcolor=ft.Colors.GREY_200,
            border_radius=10,
            padding=10,
        )


        
        self.page.add(
            ft.Row(
                [
                    ft.Column(
                        [
                            cabecalho,
                            ft.Row([
                                coluna1,
                                coluna2,
                            ])
                        ],
                        alignment=ft.MainAxisAlignment.START,
                        horizontal_alignment=ft.CrossAxisAlignment.START,
                        spacing=10
                    )   
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                vertical_alignment=ft.CrossAxisAlignment.START,
                spacing=10
            )
        )


def iniciar_matricula(matricula = '01-012'):
    def main(page: ft.Page):
        from escudo_supabase import login_supabase
        page.cliente = login_supabase()
        page.session.set("id", matricula)
        MatriculaBase(page)
    return main

if __name__ == "__main__":
    ft.app(target=iniciar_matricula())