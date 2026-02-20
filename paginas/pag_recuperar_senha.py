import flet as ft
from urllib.parse import urlparse, parse_qs
from escudo_supabase import aviso


class RecuperarSenhaBase:
    def __init__(self, page: ft.Page):
        self.page = page

        # O Supabase após verificar o token faz redirect para:
        #   /recuperar-senha#access_token=...&type=recovery&...
        # Os parâmetros vêm no FRAGMENTO (#hash), não na query string (?).
        # page.query só lê a query string — por isso é sempre vazio aqui.
        # Lemos page.url e extraímos o fragmento manualmente.
        is_recovery = False
        try:
            url = self.page.url or ""
            # Extrair a parte após '#'
            fragment = url.split("#", 1)[1] if "#" in url else ""
            fragment_params = parse_qs(fragment)
            tipo = fragment_params.get("type", [""])[0]
            access_token = fragment_params.get("access_token", [""])[0]

            if tipo == "recovery" and access_token:
                # Guardar tokens em sessão para o cliente Supabase os usar
                refresh_token = fragment_params.get("refresh_token", [""])[0]
                self.page.session.set("recovery_access_token", access_token)
                self.page.session.set("recovery_refresh_token", refresh_token)

                # Autenticar a sessão com os tokens vindos do link de email
                try:
                    self.page.cliente.auth.set_session(access_token, refresh_token)
                except Exception:
                    pass  # set_session pode falhar se já for válida

                is_recovery = True
        except Exception:
            is_recovery = False

        if is_recovery:
            self._montar_modo_definir_senha()
        else:
            self._montar_modo_pedir_link()

    # ─── Modo 1: Pedir link de recuperação ───────────────────────────────────

    def _montar_modo_pedir_link(self):
        email_guardado = self.page.session.get("email_recuperacao") or ""

        self.campo_email = ft.TextField(
            label="Email",
            value=email_guardado,
            width=300
        )

        self.botao_enviar = ft.ElevatedButton(
            text="Enviar link de recuperação",
            width=300,
            on_click=self.enviar_link,
            bgcolor=ft.Colors.BLUE,
            color=ft.Colors.WHITE
        )

        self.botao_voltar = ft.TextButton(
            text="Voltar ao login",
            on_click=lambda _: self.page.go("/login")
        )

        conteudo = ft.Container(
            content=ft.Column(
                [
                    ft.Text("Recuperar senha", size=30, weight=ft.FontWeight.BOLD),
                    ft.Text(
                        "Introduza o seu email e enviaremos um link para redefinir a sua senha.",
                        text_align=ft.TextAlign.CENTER,
                        width=300
                    ),
                    self.campo_email,
                    self.botao_enviar,
                    self.botao_voltar
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=20
            ),
            alignment=ft.alignment.center,
            expand=True
        )

        self.page.add(conteudo)

    def enviar_link(self, e):
        email_val = self.campo_email.value.strip()

        if not email_val:
            aviso(self.page, "Por favor, introduza o seu email.")
            return

        try:
            self.page.cliente.auth.reset_password_for_email(email_val)
            self.page.clean()
            self.page.add(
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Icon(ft.Icons.MARK_EMAIL_READ_OUTLINED, size=60, color=ft.Colors.GREEN),
                            ft.Text("Email enviado!", size=24, weight=ft.FontWeight.BOLD),
                            ft.Text(
                                f"Enviámos um link de recuperação para {email_val}.\n"
                                "Verifique a sua caixa de entrada (e a pasta de spam).",
                                text_align=ft.TextAlign.CENTER,
                                width=320
                            ),
                            ft.ElevatedButton(
                                "Voltar ao login",
                                on_click=lambda _: self.page.go("/login"),
                                bgcolor=ft.Colors.BLUE,
                                color=ft.Colors.WHITE,
                                width=300
                            )
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=20
                    ),
                    alignment=ft.alignment.center,
                    expand=True
                )
            )
            self.page.update()
        except Exception as erro:
            aviso(self.page, f"Erro ao enviar email: {erro}")

    # ─── Modo 2: Definir nova senha ───────────────────────────────────────────

    def _montar_modo_definir_senha(self):
        self.campo_nova_senha = ft.TextField(
            label="Nova senha",
            password=True,
            can_reveal_password=True,
            width=300
        )
        self.campo_confirmar_senha = ft.TextField(
            label="Confirmar nova senha",
            password=True,
            can_reveal_password=True,
            width=300
        )

        self.botao_salvar = ft.ElevatedButton(
            text="Definir senha",
            width=300,
            on_click=self.definir_senha,
            bgcolor=ft.Colors.BLUE,
            color=ft.Colors.WHITE
        )

        conteudo = ft.Container(
            content=ft.Column(
                [
                    ft.Text("Definir senha", size=30, weight=ft.FontWeight.BOLD),
                    ft.Text(
                        "Escolha uma nova senha para a sua conta.",
                        text_align=ft.TextAlign.CENTER,
                        width=300
                    ),
                    self.campo_nova_senha,
                    self.campo_confirmar_senha,
                    self.botao_salvar
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=20
            ),
            alignment=ft.alignment.center,
            expand=True
        )

        self.page.add(conteudo)

    def definir_senha(self, e):
        nova = self.campo_nova_senha.value
        confirmar = self.campo_confirmar_senha.value

        if not nova or not confirmar:
            aviso(self.page, "Preencha os dois campos de senha.")
            return

        if nova != confirmar:
            aviso(self.page, "As senhas não coincidem.")
            return

        if len(nova) < 6:
            aviso(self.page, "A senha deve ter pelo menos 6 caracteres.")
            return

        try:
            self.page.cliente.auth.update_user({"password": nova})
            self.page.clean()
            self.page.add(
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Icon(ft.Icons.CHECK_CIRCLE_OUTLINE, size=60, color=ft.Colors.GREEN),
                            ft.Text("Senha definida!", size=24, weight=ft.FontWeight.BOLD),
                            ft.Text(
                                "A sua senha foi atualizada com sucesso.",
                                text_align=ft.TextAlign.CENTER
                            ),
                            ft.ElevatedButton(
                                "Ir para o login",
                                on_click=lambda _: self.page.go("/login"),
                                bgcolor=ft.Colors.BLUE,
                                color=ft.Colors.WHITE,
                                width=300
                            )
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=20
                    ),
                    alignment=ft.alignment.center,
                    expand=True
                )
            )
            self.page.update()
        except Exception as erro:
            aviso(self.page, f"Erro ao definir senha: {erro}")
