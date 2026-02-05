import flet as ft

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

        # Layout
        self.conteudo = ft.Container(
            content=ft.Column(
                [
                    ft.Text("Login", size=30, weight=ft.FontWeight.BOLD),
                    self.email,
                    self.senha,
                    self.botao_entrar
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=20
            ),
            alignment=ft.alignment.center,
            expand=True
        )
        
        self.page.add(self.conteudo)

    def fazer_login(self, e):
        email_val = self.email.value
        senha_val = self.senha.value

        if not email_val or not senha_val:
            self.page.snack_bar = ft.SnackBar(ft.Text("Preencha todos os campos!"), bgcolor="red")
            self.page.snack_bar.open = True
            self.page.update()
            return

        try:
            # Tenta autenticar
            self.page.cliente.auth.sign_in_with_password({ "email": email_val, "password": senha_val })
            
            # Se deu certo, vai pro dashboard
            self.page.go("/dashboard")
            
        except Exception as erro:
            print(f"Erro login: {erro}")
            self.page.snack_bar = ft.SnackBar(ft.Text(f"Erro ao entrar: {erro}"), bgcolor="red")
            self.page.snack_bar.open = True
            self.page.update()
