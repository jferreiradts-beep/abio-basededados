import flet as ft
from escudo_supabase import aviso

class LoginBase:
    def __init__(self, page: ft.Page):
        self.page = page

        # Campos de entrada
        self.email = ft.TextField(label="Email", width=300)
        self.senha = ft.TextField(label="Senha", password=True, can_reveal_password=True, width=300)

        # Checkbox salvar login
        self.salvar_login = ft.Checkbox(label="Salvar login", value=False)
        self.aviso_seguranca = ft.Text(
            "⚠️ Por favor, desmarque em computadores compartilhados",
            size=11,
            color=ft.Colors.ORANGE_700,
            italic=True,
            visible=False,
            width=300,
        )
        self.salvar_login.on_change = self.toggle_aviso

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
                    ft.Container(
                        width=300,
                        content=ft.Column([
                            self.salvar_login,
                            self.aviso_seguranca,
                        ], spacing=2),
                    ),
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

        # Login automático para desenvolvimento local (usa credenciais do .env)
        self._tentar_login_automatico()

    def _tentar_login_automatico(self):
        from dotenv import load_dotenv
        import os
        load_dotenv()
        usuario = os.getenv("USUARIO")
        senha = os.getenv("SENHA")
        if usuario and senha:
            try:
                self.page.cliente.auth.sign_in_with_password({"email": usuario, "password": senha})
                self.page.go("/dashboard")
            except Exception:
                pass  # Credenciais inválidas ou ambiente remoto — mostra ecrã de login normalmente

    def toggle_aviso(self, e):
        self.aviso_seguranca.visible = self.salvar_login.value
        self.page.update()

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

            # Salvar sessão no navegador se o usuário marcou a opção
            if self.salvar_login.value:
                sessao = self.page.cliente.auth.get_session()
                if sessao:
                    self.page.client_storage.set("sb_access_token", sessao.access_token)
                    self.page.client_storage.set("sb_refresh_token", sessao.refresh_token)
                    print("[AUTH] Sessão salva no client_storage")
            else:
                # Garante que não há sessão salva de login anterior
                self.page.client_storage.remove("sb_access_token")
                self.page.client_storage.remove("sb_refresh_token")

            # Se deu certo, vai pro dashboard
            self.page.go("/dashboard")

        except Exception as erro:
            aviso(self.page, f"Erro ao entrar: {erro}")
