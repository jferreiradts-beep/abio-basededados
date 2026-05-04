import flet as ft
from escudo_supabase import aviso

class LoginBase:
    def __init__(self, page: ft.Page):
        self.page = page
        
        # Campos de entrada
        self.email = ft.TextField(label="Email", width=300)
        self.senha = ft.TextField(label="Senha", password=True, can_reveal_password=True, width=300)
        
        # Botão de entrar
        self.botao_entrar = ft.ElevatedButton(
            text="Entrar",
            width=300,
            on_click=self.fazer_login,
            bgcolor=ft.Colors.BLUE,
            color=ft.Colors.WHITE
        )

        # Link de recuperação de senha
        self.link_recuperar = ft.TextButton(
            text="Recuperar senha",
            on_click=self.ir_recuperar_senha
        )

        # Layout
        self.conteudo = ft.Container(
            content=ft.Column(
                [
                    ft.Text("Login", size=30, weight=ft.FontWeight.BOLD),
                    self.email,
                    self.senha,
                    self.botao_entrar,
                    self.link_recuperar
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=20
            ),
            alignment=ft.alignment.center,
            expand=True
        )
        
        self.page.add(self.conteudo)

    def ir_recuperar_senha(self, e):
        self.page.session.set("email_recuperacao", self.email.value)
        self.page.go("/recuperar-senha")

    def fazer_login(self, e):
        email_val = self.email.value
        senha_val = self.senha.value

        if not email_val or not senha_val:
            aviso(self.page, "Preencha todos os campos!")
            self.page.update()
            return

        try:
            # Tenta autenticar
            self.page.cliente.auth.sign_in_with_password({ "email": email_val, "password": senha_val })
            print(self.page.cliente.auth.get_user())
            
            # Se deu certo, vai pro dashboard
            self.page.go("/dashboard")
            
        except Exception as erro:
            aviso(self.page, f"Erro ao entrar: {erro}")
