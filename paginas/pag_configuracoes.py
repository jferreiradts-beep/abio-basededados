import flet as ft

class ConfiguracoesBase:
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = "Configurações"
        self.page.scroll = "auto"

        # Load values from Supabase
        resposta = self.page.cliente.table('configuracoes').select('*').eq('id', 1).execute()

        if resposta.data:
            config = resposta.data[0]
            nome_assinante = config.get('assinatura') or "WELLINGTON MARY"
            cargo_assinante = config.get('assinatura_cargo') or "DIRETOR TÉCNICO DA ABIO"
            is_suspenso = config.get('suspenso', True)
            is_cancelado = config.get('cancelado', True)
            self.registro_existe = True
        else:
            nome_assinante = "WELLINGTON MARY"
            cargo_assinante = "DIRETOR TÉCNICO DA ABIO"
            is_suspenso = True
            is_cancelado = True
            self.registro_existe = False

        # UI Components
        self.txt_nome = ft.TextField(label="Nome de quem assina o certificado", value=nome_assinante, width=400)
        self.txt_cargo = ft.TextField(label="Cargo de quem assina o certificado", value=cargo_assinante, width=400)

        self.chk_ativo = ft.Checkbox(label="Ativo", value=True, disabled=True)
        self.chk_suspenso = ft.Checkbox(label="Suspenso", value=is_suspenso)
        self.chk_cancelado = ft.Checkbox(label="Cancelado", value=is_cancelado)

        btn_salvar = ft.ElevatedButton("Salvar", on_click=self.salvar, color=ft.Colors.GREEN)
        btn_voltar = ft.ElevatedButton("Voltar", on_click=lambda _: self.page.go("/dashboard"))

        # Layout
        self.page.add(
            ft.Row([
                ft.Column([
                    ft.Text("Configurações", size=24, weight="bold"),
                    ft.Divider(),
                    ft.Text("Certificado", size=18, weight="bold"),
                    self.txt_nome,
                    self.txt_cargo,
                    ft.Divider(),
                    ft.Text("Filtro do Dashboard (Situação)", size=18, weight="bold"),
                    self.chk_ativo,
                    self.chk_suspenso,
                    self.chk_cancelado,
                    ft.Divider(),
                    ft.Row([btn_voltar, btn_salvar], spacing=20)
                ], spacing=15, alignment=ft.MainAxisAlignment.START)
            ], alignment=ft.MainAxisAlignment.CENTER)
        )

    def salvar(self, e):
        dados_novos = {
            'assinatura': self.txt_nome.value,
            'assinatura_cargo': self.txt_cargo.value,
            'suspenso': self.chk_suspenso.value,
            'cancelado': self.chk_cancelado.value
        }

        try:
            if self.registro_existe:
                self.page.cliente.table('configuracoes').update(dados_novos).eq('id', 1).execute()
            else:
                dados_novos['id'] = 1
                self.page.cliente.table('configuracoes').insert(dados_novos).execute()
                self.registro_existe = True
            
            self.page.snack_bar = ft.SnackBar(ft.Text("Configurações salvas com sucesso!"), bgcolor=ft.Colors.GREEN)
        except Exception as error:
            self.page.snack_bar = ft.SnackBar(ft.Text(f"Erro ao salvar: {error}"), bgcolor=ft.Colors.RED)
            
        self.page.snack_bar.open = True
        self.page.update()
