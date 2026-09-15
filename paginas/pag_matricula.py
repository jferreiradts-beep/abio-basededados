import flet as ft
import asyncio
from datetime import datetime
from formatar_campos import aplicarMascara
from formulario_base import campoFixo
from escudo_supabase import aviso

MASCARA_CPF_CNPJ = aplicarMascara("###.###.###-##; ##.###.###/####-##")
MASCARA_TELEFONE = aplicarMascara("(##) ####-####; (##) #####-####")
COR_MODIFICADO = "#FFF59D"
STATUS_CORES = {
    "Pago": ft.Colors.GREEN_400,
    "Atrasado": ft.Colors.RED_400,
    "Aberto": ft.Colors.AMBER_400,
    "Renegociado": ft.Colors.PURPLE_400
}

class ColunaEsquerda:
    def __init__(self, page, dados_completos, b_salvar, b_voltar):
        self.page = page
        self.dados = dados_completos
        self.alterado = False
        self.b_salvar = b_salvar
        self.b_voltar = b_voltar
        
        self.montar_ui()
        
    def montar_ui(self):
        # --- DADOS GERAIS ---
        self.campos = {}
        
        self.campos['nome'] = campoFixo(self.page, self.dados, 'nome', largura=(0, 140), rotulo_acima=True)
        self.campos['grupo_id'] = campoFixo(self.page, self.dados, 'grupo_id', largura=(0, 360), rotulo_acima=True)

        self.campos['ta_id'] = campoFixo(self.page, self.dados, 'ta_id', largura=(0, 160), rotulo_acima=True)
        self.campos['modalidade_pag'] = campoFixo(self.page, self.dados, 'modalidade_pag', largura=(0, 180), rotulo_acima=True)
        self.campos['periodicidade'] = campoFixo(self.page, self.dados, 'periodicidade', largura=(0, 160), rotulo_acima=True)

        # Registrar dependências entre campos fixos (Observer) e monitorizar alterações
        for campo_nome, inst in self.campos.items():
            filtro = self.dados.get('campos_fixos', {}).get(campo_nome, {}).get('filtro')
            if filtro and filtro != 'id' and filtro in self.campos and filtro != campo_nome:
                self.campos[filtro].registar_dependente(inst)
                
            # Intercetar marcar_modificado para atualizar self.alterado
            def criar_intercetador(instancia):
                orig_metodo = instancia.marcar_modificado
                def novo_metodo():
                    self.alterado = True
                    orig_metodo()
                return novo_metodo
            inst.marcar_modificado = criar_intercetador(inst)
            
        linha1 = ft.Row([self.campos['nome'].campo_ui, self.campos['grupo_id'].campo_ui], spacing=20)
        linha2 = ft.Row([self.campos['ta_id'].campo_ui, self.campos['modalidade_pag'].campo_ui, self.campos['periodicidade'].campo_ui], spacing=10)

        # Carregar opções dos dropdowns via lazy load (chamado externamente após o layout estar na página)
        self._campos_a_carregar = [inst for inst in self.campos.values() if inst._precisa_carregar]
        
        # --- FINANCEIRO ---
        financeiro = self.dados.get("financeiro", {})
        
        meses_str = {
            1: "jan", 2: "fev", 3: "mar", 4: "abr", 5: "mai", 6: "jun",
            7: "jul", 8: "ago", 9: "set", 10: "out", 11: "nov", 12: "dez"
        }
        status_cores = STATUS_CORES
        status_dict = {}
        lista_status = financeiro.get("status_ultimos") or financeiro.get("status_ultimos_6") or []
        for item in lista_status:
            if isinstance(item, dict):
                for k, v in item.items():
                    status_dict[k] = v
                    if len(k) >= 7:
                        status_dict[k[:7]] = v

        hoje = datetime.now()
        mes_atual = hoje.month
        ano_atual = hoje.year
        
        ano = str(ano_atual)
        
        # Gera as 8 chaves (do mais antigo pro mais novo)
        datas_8_meses = []
        for i in range(7, -1, -1):
            m = mes_atual - i
            y = ano_atual
            if m <= 0:
                m += 12
                y -= 1
            dt_str = f"{y}-{m:02d}-01"
            datas_8_meses.append((y, m, dt_str))
            
        self.meses_widgets = []
        self.box_meses_map = {}

        # Verifica se Janeiro está na sequência de 8 meses
        tem_janeiro = any(m == 1 for _, m, _ in datas_8_meses)

        for idx, (y, m, dt_str) in enumerate(datas_8_meses):
            status = status_dict.get(dt_str) or status_dict.get(dt_str[:7], "ND")
            mes_texto = meses_str[m]
            
            # Exibe o ano uma única vez (em Janeiro se presente, ou no primeiro mês caso contrário)
            if tem_janeiro:
                mostrar_ano = (m == 1)
            else:
                mostrar_ano = (idx == 0)

            ano_texto = str(y) if mostrar_ano else ""

            txt_ano = ft.Text(ano_texto, size=12, weight="bold", color=ft.Colors.GREY_700)
            txt_mes = ft.Text(mes_texto, weight="bold", size=14)

            cor = status_cores.get(status, ft.Colors.TRANSPARENT)
            texto_box = "ND" if status not in status_cores else ""
            
            box = ft.Container(
                content=ft.Text(texto_box, color=ft.Colors.BLACK, weight="bold") if texto_box else None,
                width=50, height=40, bgcolor=cor,
                border=ft.border.all(1, ft.Colors.GREY_400), alignment=ft.alignment.center, border_radius=4
            )
            self.box_meses_map[dt_str] = box
            
            col_mes = ft.Column(
                [txt_ano, txt_mes, box], 
                spacing=3, 
                horizontal_alignment=ft.CrossAxisAlignment.CENTER
            )
            self.meses_widgets.append(col_mes)
                
        self.mensalidades_row = ft.Row(self.meses_widgets, alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
        
        ultimo_val = financeiro.get('ultimo_valor') or 0.0
        divida = financeiro.get('divida') or 0.0
        
        self.txt_ultimo_valor = ft.Text(f"R$ {ultimo_val:.2f}".replace(".", ","), size=15, weight="bold", color=ft.Colors.GREY_900)
        caixa_ultimo_valor = ft.Row([
            ft.Text("Mensalidade:", weight="bold", size=14, color=ft.Colors.GREY_700),
            ft.Container(
                content=self.txt_ultimo_valor,
                padding=ft.padding.symmetric(horizontal=10, vertical=4),
                bgcolor=ft.Colors.GREY_300, border_radius=6
            )
        ], vertical_alignment=ft.CrossAxisAlignment.CENTER, spacing=6)

        self.txt_divida = ft.Text(
            f"R$ {divida:.2f}".replace(".", ","), 
            size=15, weight="bold", 
            color=ft.Colors.RED_700 if divida > 0 else ft.Colors.GREY_900
        )
        caixa_divida = ft.Row([
            ft.Text("Dívida:", weight="bold", size=14, color=ft.Colors.GREY_700),
            ft.Container(
                content=self.txt_divida,
                padding=ft.padding.symmetric(horizontal=10, vertical=4),
                bgcolor=ft.Colors.GREY_300, border_radius=6
            )
        ], vertical_alignment=ft.CrossAxisAlignment.CENTER, spacing=6)
        
        valores_row = ft.Row(
            [caixa_ultimo_valor, caixa_divida], 
            alignment=ft.MainAxisAlignment.START, 
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=30
        )
        
        # BOTOES ACAO
        botoes = ft.Row(
            [
                ft.ElevatedButton("Pagar", disabled=False, width=110, on_click=self.abrir_pagamento),
                ft.ElevatedButton("Excluir", disabled=True, width=110),
                ft.ElevatedButton("Salvar", disabled=False, width=110, on_click=self.b_salvar),
                ft.ElevatedButton("Voltar", disabled=False, width=110, on_click=self.b_voltar),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN
        )
        
        self.conteudo = ft.Container(
            content=ft.Column([
                 ft.Text("Resumo da matrícula", size=24, weight="bold"),
                 ft.Divider(height=10),
                 linha1,
                 linha2,
                 ft.Container(height=40),  # Empurra todo o bloco de mensalidades para baixo
                 ft.Text("Mensalidades", size=20, weight="bold"),
                 valores_row,  # Valores de Mensalidade e Dívida posicionados entre o título e os blocos de meses (que contêm o ano no topo)
                 self.mensalidades_row,
                ft.Container(expand=True),
                ft.Divider(height=15),
                botoes
            ], spacing=8, expand=True),
            width=560, height=570, bgcolor=ft.Colors.GREY_200, border_radius=10, padding=20
        )
        
    def abrir_pagamento(self, e):
        id_matricula = self.dados.get('dados_fixos', {}).get('id') or self.page.session.get('id')
        janelaPagamento(self.page, id_matricula, ao_salvar=self.atualizar_financeiro)

    def atualizar_financeiro(self, novo_financeiro):
        if not novo_financeiro or not isinstance(novo_financeiro, dict):
            return

        self.dados["financeiro"] = novo_financeiro

        ultimo_val = float(novo_financeiro.get('ultimo_valor') or 0.0)
        divida = float(novo_financeiro.get('divida') or 0.0)

        self.txt_ultimo_valor.value = f"R$ {ultimo_val:.2f}".replace(".", ",")
        self.txt_divida.value = f"R$ {divida:.2f}".replace(".", ",")

        status_dict = {}
        lista_status = novo_financeiro.get("status_ultimos") or novo_financeiro.get("status_ultimos_6") or []
        for item in lista_status:
            if isinstance(item, dict):
                for k, v in item.items():
                    status_dict[k] = v
                    if len(k) >= 7:
                        status_dict[k[:7]] = v

        status_cores = STATUS_CORES

        for dt_str, box in self.box_meses_map.items():
            status = status_dict.get(dt_str) or status_dict.get(dt_str[:7], "ND")
            box.bgcolor = status_cores.get(status, ft.Colors.TRANSPARENT)
            texto_box = "ND" if status not in status_cores else ""
            box.content = ft.Text(texto_box, color=ft.Colors.BLACK, weight="bold") if texto_box else None

        self.txt_ultimo_valor.update()
        self.txt_divida.update()
        self.mensalidades_row.update()

    def marcar_alterado(self, e):
        self.alterado = True

    def marcar_campos_salvos(self):
        """Volta todos os campos da matrícula à cor normal após guardar."""
        for inst in self.campos.values():
            inst.marcar_salvo()
        self.alterado = False

    def iniciar_lazy_load(self):
        """Deve ser chamado após o layout já estar adicionado à página."""
        if self._campos_a_carregar:
            self.page.run_task(self._carregar_opcoes_sequencialmente, self._campos_a_carregar)

    async def _carregar_opcoes_sequencialmente(self, campos):
        import asyncio
        for campo in campos:
            await asyncio.to_thread(campo.carregar_opcoes_lazy)


class ColunaDireita:
    def __init__(self, page, dados_completos, id_matricula, ao_salvar_acontecimento=None):
        self.page = page
        self.dados = dados_completos
        self.id_matricula = id_matricula
        self.ao_salvar_acontecimento = ao_salvar_acontecimento
        self.montar_ui()
        
    def montar_ui(self):
        # ABA ASSOCIADOS
        lista_associados = []
        associados_dados = self.dados.get('associados', [])
        
        for assoc in associados_dados:
            nome_assoc = assoc.get('nome', '')
            cpf_assoc = MASCARA_CPF_CNPJ.aplicar_mascara(assoc.get('cpf', ''))
            whatsapp_assoc = MASCARA_TELEFONE.aplicar_mascara(assoc.get('whatsapp', '')) or "Sem WhatsApp"
            
            item_container = ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.PERSON_OUTLINE, color=ft.Colors.BLUE_900, size=28),
                    ft.Column([
                        ft.Text(nome_assoc, weight="bold", size=14, overflow=ft.TextOverflow.ELLIPSIS),
                        ft.Text(f"CPF/CNPJ: {cpf_assoc} | WhatsApp: {whatsapp_assoc}", size=12, color=ft.Colors.GREY_700),
                    ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.START, expand=True, spacing=3),
                ], alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.CENTER, spacing=12),
                bgcolor=ft.Colors.WHITE, border_radius=8, border=ft.border.all(1, ft.Colors.GREY_300), padding=ft.padding.all(10),
            )
            
            item = ft.GestureDetector(
                content=item_container,
                on_double_tap=lambda e, a_id=assoc.get('id'): self.ir_para_associado(a_id)
            )
            lista_associados.append(item)
            
        if not lista_associados:
            lista_associados = [ft.Container(content=ft.Text("Nenhum associado cadastrado", color=ft.Colors.GREY_600, italic=True), alignment=ft.alignment.center, padding=20)]
            
        aba_associados = ft.Tab(
            text="Associados",
            content=ft.Container(
                content=ft.Column([
                    ft.ListView(lista_associados, expand=True, spacing=5, padding=5),
                    ft.Row([
                        ft.ElevatedButton(
                            "Novo associado", 
                            disabled=str(self.id_matricula) == '0', 
                            on_click=self.novo_associado,
                            style=ft.ButtonStyle(padding=ft.padding.symmetric(horizontal=16, vertical=10))
                        )
                    ], alignment=ft.MainAxisAlignment.END)
                ], expand=True),
                padding=10,
                expand=True
            )
        )
        
        # ABA ACONTECIMENTOS
        self.acontecimentos_dados = self.dados.get("acontecimentos", [])
        
        # Obter combinações únicas de uprod e escopo
        combinacoes = set()
        for a in self.acontecimentos_dados:
            uprod = a.get("uprod") or ""
            escopo = a.get("escopo") or ""
            if escopo.strip(): # Ignora escopos vazios na lista do filtro
                combinacoes.add(f"{uprod} - {escopo}")
                
        opcoes_filtro = [ft.dropdown.Option("Todos")]
        for combo in sorted(list(combinacoes)):
            opcoes_filtro.append(ft.dropdown.Option(combo))
            
        self.dropdown_filtro_ac = ft.Dropdown(
            options=opcoes_filtro, 
            value="Todos", 
            width=280, 
            content_padding=10,
            on_change=self.filtrar_acontecimentos,
            text_style=ft.TextStyle(size=14)
        )
        
        btn_novo_ac = ft.ElevatedButton(
            "Novo acontecimento", 
            disabled=str(self.id_matricula) == '0',
            on_click=lambda e: self.abrir_dialog_acontecimento(0),
            style=ft.ButtonStyle(padding=ft.padding.symmetric(horizontal=16, vertical=10))
        )
        
        header_ac = ft.Row(
            [
                ft.Text("Filtrar:", weight="bold", size=13, color=ft.Colors.GREY_700),
                self.dropdown_filtro_ac
            ], 
            vertical_alignment=ft.CrossAxisAlignment.CENTER, spacing=8
        )
        
        # Larguras fixas das colunas para manter cabeçalho e corpo alinhados
        self._ac_larguras = [90, 160, 70, 180]
        self._ac_titulos = ["Data", "Und. produção", "Escopo", "Acontecimento"]
        
        # Cabeçalho fixo (Row manual fora da área de scroll)
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
        
        # Corpo com scroll (ListView de Rows com mesmas larguras)
        self.lista_acontecimentos = ft.ListView(expand=True, spacing=0, padding=0)
        self.filtrar_acontecimentos(None) # Inicializa as linhas
        
        tab_ac_container = ft.Container(
            content=ft.Column([
                cabecalho_ac_row,
                self.lista_acontecimentos,
            ], spacing=0, expand=True), 
            expand=True
        )
        
        aba_acontecimentos = ft.Tab(
            text="Acontecimentos",
            content=ft.Container(
                content=ft.Column([
                    header_ac, 
                    tab_ac_container,
                    ft.Row([btn_novo_ac], alignment=ft.MainAxisAlignment.END)
                ], spacing=10, expand=True),
                padding=10,
                expand=True
            )
        )
        
        self.conteudo = ft.Container(
            content=ft.Tabs(
                selected_index=0,
                animation_duration=300,
                tabs=[aba_associados, aba_acontecimentos],
                expand=1
            ),
            width=560, height=570, bgcolor=ft.Colors.GREY_200, border_radius=10, padding=10
        )
        
    def filtrar_acontecimentos(self, e):
        filtro = self.dropdown_filtro_ac.value
        self.lista_acontecimentos.controls.clear()
        idx = 0
        
        for a in self.acontecimentos_dados:
            uprod = a.get("uprod") or ""
            escopo = a.get("escopo") or ""
            
            mostrar = False
            if filtro == "Todos":
                mostrar = True
            elif not escopo.strip(): # Mostra sempre se escopo estiver vazio ou nulo
                mostrar = True
            elif f"{uprod} - {escopo}" == filtro:
                mostrar = True
                
            if mostrar:
                try:
                    dt_str = datetime.strptime(a.get("data", ""), "%Y-%m-%d").strftime("%d/%m/%Y")
                except:
                    dt_str = a.get("data", "")
                
                valores = [dt_str, uprod, escopo, a.get("tipo", "")]
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
                
        if e: # Atualiza a UI caso seja engatilhado por evento on_change
            self.lista_acontecimentos.update()

    def atualizar_acontecimentos(self, novos_acontecimentos):
        """Atualiza os dados de acontecimentos e reconstrói a lista e o filtro."""
        self.acontecimentos_dados = novos_acontecimentos
        self.dados["acontecimentos"] = novos_acontecimentos

        # Recalcular combinações únicas para o filtro
        combinacoes = set()
        for a in self.acontecimentos_dados:
            uprod = a.get("uprod") or ""
            escopo = a.get("escopo") or ""
            if escopo.strip():
                combinacoes.add(f"{uprod} - {escopo}")

        opcoes_filtro = [ft.dropdown.Option("Todos")]
        for combo in sorted(list(combinacoes)):
            opcoes_filtro.append(ft.dropdown.Option(combo))

        self.dropdown_filtro_ac.options = opcoes_filtro
        # Manter filtro atual se ainda existir, senão voltar a "Todos"
        valores_validos = {"Todos"} | combinacoes
        if self.dropdown_filtro_ac.value not in valores_validos:
            self.dropdown_filtro_ac.value = "Todos"

        self.filtrar_acontecimentos(None)
        self.dropdown_filtro_ac.update()
        self.lista_acontecimentos.update()

    def novo_associado(self, e):
        janelaNovoAssociado(self.page, self.id_matricula)
        
    def ir_para_associado(self, associado_id):
        self.page.voltar_dados['endereco'].append(self.page.route)
        self.page.voltar_dados['dados_pagina'].append({'id': self.id_matricula})
        self.page.session.set('tipo', 'associado')
        self.page.session.set('id', str(associado_id))
        self.page.go('/formulario')

    def abrir_dialog_acontecimento(self, id_acontecimento):
        janelaAcontecimento(self.page, self.id_matricula, id_acontecimento, ao_salvar=self.ao_salvar_acontecimento)


class MatriculaBase:
    def __init__(self, page):
        self.page = page
        self.page.title = "SPG ABIO: Matrícula"
        self.page.scroll = "auto"
        self.id = self.page.session.get('id')
        
        self.conteudo_principal = ft.Container(
            content=ft.ProgressRing(), 
            alignment=ft.alignment.center,
            expand=True
        )
        
        cabecalho = ft.Row([
            ft.PopupMenuButton(icon=ft.Icons.MENU, items=[]),
            ft.Text("SPG ABIO", size=24, weight="bold")
        ], alignment=ft.MainAxisAlignment.START, spacing=20)
        
        self.layout = ft.Column([
            cabecalho,
            self.conteudo_principal
        ], alignment=ft.MainAxisAlignment.START, horizontal_alignment=ft.CrossAxisAlignment.START, spacing=10)
        
        self.page.add(self.layout)
        self.page.run_task(self.carregar_dados)
        
    async def carregar_dados(self):
        data_atual = datetime.now().strftime('%Y-%m-%d')
        
        def fetch():
            return self.page.cliente.rpc('preencher_f_matricula', {'p_data': data_atual, 'p_matricula_id': int(self.id)}).execute().data
            
        try:
            self.dados_completos = await asyncio.to_thread(fetch)
        except Exception as e:
            self.conteudo_principal.content = ft.Text(f"Erro ao carregar dados: {e}")
            self.conteudo_principal.update()
            return
            
        self.montar_layout_completo()
        
    def recarregar(self):
        self.page.run_task(self.carregar_dados)

    def montar_layout_completo(self):
        self.coluna_esq = ColunaEsquerda(self.page, self.dados_completos, self.salvar, self.voltar)
        self.coluna_dir = ColunaDireita(self.page, self.dados_completos, self.id, ao_salvar_acontecimento=self.ao_acontecimento_salvo)
        
        self.conteudo_principal.content = ft.Row(
            [self.coluna_esq.conteudo, self.coluna_dir.conteudo],
            alignment=ft.MainAxisAlignment.CENTER,
            vertical_alignment=ft.CrossAxisAlignment.START,
            spacing=20
        )
        self.conteudo_principal.alignment = ft.alignment.top_left
        self.conteudo_principal.update()
        # Só agora os controles estão na página: podemos iniciar o lazy load dos dropdowns
        self.coluna_esq.iniciar_lazy_load()

    def ao_acontecimento_salvo(self, novos_acontecimentos):
        """Callback chamado após salvar acontecimento com sucesso via RPC.
        Atualiza dados_completos e a aba de acontecimentos sem recarregar a página."""
        self.dados_completos["acontecimentos"] = novos_acontecimentos
        self.coluna_dir.atualizar_acontecimentos(novos_acontecimentos)
        
    def salvar(self, e):
        """Guarda apenas os dados_fixos da matrícula via RPC."""
        dados_fixos = self.dados_completos.get('dados_fixos', {})

        try:
            resposta = self.page.cliente.rpc(
                'salvar_f_matricula',
                {'p_json': dados_fixos}
            ).execute()
        except Exception as ex:
            aviso(self.page, f"Erro de ligação ao servidor: {ex}")
            return

        novo_id = resposta.data if resposta and resposta.data else None

        if novo_id:
            # Atualizar id na estrutura de dados e na sessão
            self.dados_completos['dados_fixos']['id'] = novo_id
            self.page.session.set('id', novo_id)
            # Repor a cor normal em todos os campos
            self.coluna_esq.marcar_campos_salvos()
        else:
            aviso(self.page, "Erro ao salvar: sem resposta do servidor.")
        
    def voltar(self, e):
        endereco_lista = self.page.voltar_dados.get('endereco', [])
        dados_lista    = self.page.voltar_dados.get('dados_pagina', [])
        retorno     = endereco_lista[-1] if endereco_lista else '/dashboard'
        voltar_dados = dados_lista[-1] if dados_lista else None
        
        if voltar_dados:
            for chave, valor in voltar_dados.items():
                self.page.session.set(chave, valor)
                
        if endereco_lista:
            self.page.voltar_dados['endereco'].pop()
        if dados_lista:
            self.page.voltar_dados['dados_pagina'].pop()
            
        self.page.go(retorno)


class janelaPagamento:
    def __init__(self, page, id_matricula, ao_salvar=None):
        self.page = page
        self.id_matricula = id_matricula
        self.ao_salvar = ao_salvar
        self.total_com_desconto_atual = 0.0
        self.dados_mensalidades = self.obter_dados()

        if not self.dados_mensalidades:
            aviso(self.page, "Não existem mensalidades em aberto")
            return

        self.exibir_janela()

    def obter_dados(self):
        data_atual = datetime.now().strftime('%Y-%m-%d')
        try:
            matricula_id_val = int(self.id_matricula) if self.id_matricula else 0
        except (ValueError, TypeError):
            matricula_id_val = 0

        try:
            resposta = self.page.cliente.rpc(
                'mensalidades_pendentes_json',
                {'p_data': data_atual, 'p_matricula_id': matricula_id_val}
            ).execute()
            dados = resposta.data
            if isinstance(dados, str):
                import json
                dados = json.loads(dados)

            if dados and isinstance(dados, list):
                dados.sort(key=lambda x: str(x.get('vencimento') or x.get('competencia') or ''))

            return dados or []
        except Exception as err:
            print(f"Erro ao obter mensalidades pendentes: {err}")
            return []

    def recalcular_totais(self, e=None):
        subtotal = 0.0
        for item, chk in self.lista_controles:
            if chk.value:
                val = item.get('valor_atualizado', item.get('valor', 0.0))
                try:
                    subtotal += float(val)
                except (ValueError, TypeError):
                    pass

        desc_str = self.input_desconto.value or "0"
        desc_str = desc_str.replace('.', '').replace(',', '.') if ',' in desc_str else desc_str
        try:
            desconto = float(desc_str)
        except ValueError:
            desconto = 0.0

        desconto = max(0.0, desconto)
        total_com_desconto = max(0.0, subtotal - desconto)
        self.total_com_desconto_atual = total_com_desconto

        self.txt_total.value = f"R$ {subtotal:.2f}".replace('.', ',')
        self.txt_total_desconto.value = f"R$ {total_com_desconto:.2f}".replace('.', ',')

        if hasattr(self, 'btn_pagar') and self.btn_pagar:
            tem_selecionado = any(chk.value for _, chk in self.lista_controles)
            self.btn_pagar.disabled = not tem_selecionado

        if hasattr(self, 'janela') and self.janela:
            self.janela.update()

    def salvar_pagamento(self, e):
        vencimentos = []
        for item, chk in self.lista_controles:
            if chk.value:
                venc = item.get('vencimento') or item.get('competencia')
                if venc:
                    vencimentos.append(str(venc))

        if not vencimentos:
            aviso(self.page, "Selecione pelo menos uma mensalidade para pagar.")
            return

        data_atual = datetime.now().strftime('%Y-%m-%d')
        try:
            matricula_id_val = int(self.id_matricula) if self.id_matricula else 0
        except (ValueError, TypeError):
            matricula_id_val = 0

        valor_pago = round(float(self.total_com_desconto_atual), 2)

        try:
            resposta = self.page.cliente.rpc(
                'salvar_pagamento_mensalidades',
                {
                    'p_matricula_id': matricula_id_val,
                    'p_data': data_atual,
                    'p_vencimentos': vencimentos,
                    'p_valor_pago': valor_pago
                }
            ).execute()

            novo_financeiro = resposta.data
            if isinstance(novo_financeiro, str):
                import json
                novo_financeiro = json.loads(novo_financeiro)

            self.janela.open = False
            self.page.update()

            if self.ao_salvar and callable(self.ao_salvar):
                self.ao_salvar(novo_financeiro)

        except Exception as err:
            aviso(self.page, f"Erro ao salvar pagamento: {err}")

    @staticmethod
    def _formatar_data(data_str):
        if not data_str:
            return ""
        try:
            dt = datetime.strptime(str(data_str), '%Y-%m-%d')
            return dt.strftime('%d/%m/%Y')
        except (ValueError, TypeError):
            return str(data_str)

    def montar_janela(self):
        # Limitar a no máximo 5 linhas (mensalidades)
        itens = self.dados_mensalidades[:5]

        self.lista_controles = []
        rows_tabela = []

        for item in itens:
            venc_raw = item.get('vencimento', '')
            venc_fmt = self._formatar_data(venc_raw)
            val_num = item.get('valor_atualizado', item.get('valor', 0.0))
            try:
                val_float = float(val_num)
            except (ValueError, TypeError):
                val_float = 0.0
            val_fmt = f"R$ {val_float:.2f}".replace('.', ',')

            chk = ft.Checkbox(value=True, on_change=self.recalcular_totais)
            self.lista_controles.append((item, chk))

            rows_tabela.append(
                ft.DataRow(cells=[
                    ft.DataCell(ft.Text(venc_fmt)),
                    ft.DataCell(ft.Text(val_fmt)),
                    ft.DataCell(chk),
                ])
            )

        self.tabela = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Vencimento", weight="bold")),
                ft.DataColumn(ft.Text("Valor", weight="bold")),
                ft.DataColumn(ft.Text("Pagar", weight="bold")),
            ],
            rows=rows_tabela,
            heading_row_color=ft.Colors.GREY_300,
            data_row_min_height=38,
            data_row_max_height=42,
            column_spacing=35,
        )

        self.txt_total = ft.Text("R$ 0,00", weight="bold", size=14)
        self.input_desconto = ft.TextField(
            value="0,00",
            width=110,
            height=38,
            text_align=ft.TextAlign.RIGHT,
            content_padding=ft.padding.all(6),
            keyboard_type=ft.KeyboardType.NUMBER,
            on_change=self.recalcular_totais
        )
        self.txt_total_desconto = ft.Text("R$ 0,00", weight="bold", size=15, color=ft.Colors.GREEN_700)
        self.btn_pagar = ft.ElevatedButton("Pagar", on_click=self.salvar_pagamento)

        # Calcular totais iniciais
        self.recalcular_totais()

        conteudo_dialogo = ft.Container(
            width=480, height=400,
            content=ft.Column([
                ft.Container(
                    content=ft.Column([self.tabela], scroll=ft.ScrollMode.AUTO),
                    height=250
                ),
                ft.Divider(height=10),
                ft.Row([
                    ft.Text("Total:", weight="bold", size=14),
                    self.txt_total
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Row([
                    ft.Text("Desconto (R$):", size=14),
                    self.input_desconto
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                ft.Row([
                    ft.Text("Total com desconto:", weight="bold", size=15),
                    self.txt_total_desconto
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ], spacing=10, scroll=ft.ScrollMode.AUTO)
        )

        return ft.AlertDialog(
            title=ft.Text("Pagamento de Mensalidades"),
            content=conteudo_dialogo,
            actions=[
                self.btn_pagar,
                ft.ElevatedButton("Cancelar", on_click=self.fechar_janela)
            ]
        )

    def fechar_janela(self, e):
        self.janela.open = False
        self.page.update()

    def exibir_janela(self):
        self.janela = self.montar_janela()
        self.page.overlay.append(self.janela)
        self.janela.open = True
        self.page.update()


class janelaNovoAssociado:
    def __init__(self, page, matricula_id):
        self.page = page
        self.matricula_id = matricula_id
        self.exibir_janela()
        
    def exibir_janela(self):
        self.montar_janela()
        self.page.overlay.append(self.janela)
        self.janela.open = True
        self.page.update()

    def montar_janela(self):
        self.nome = ft.TextField(label="Nome")
        self.cpf = ft.TextField(
            label="CPF",
            on_change=MASCARA_CPF_CNPJ.on_change
        )
        self.mensagem = ft.Text("", color="red", size=12)

        self.janela = ft.AlertDialog(
            title=ft.Text("Novo associado"),
            content=ft.Container(
                width=350, height=140,
                content=ft.Column([self.nome, self.cpf, self.mensagem])
            ),
            actions=[
                ft.ElevatedButton("Ir", on_click=lambda e: self.ir()),
                ft.ElevatedButton("Cancelar", on_click=lambda e: self.cancelar())
            ]
        )

    def ir(self):
        cpf = MASCARA_CPF_CNPJ.salvar_limpo(self.cpf.value)
        if len(cpf) not in (11, 14):
            self.mensagem.value = "CPF/CNPJ inválido"
            self.janela.update()
            return
            
        self.mensagem.value = ""
        self.janela.update()

        try:
            resposta = self.page.cliente.rpc('vincular_associado', {
                'p_nome': self.nome.value,
                'p_cpf': cpf,
                'p_matricula': int(self.matricula_id)
            }).execute()
        except Exception as e:
            self.mensagem.value = f"Erro: {e}"
            self.janela.update()
            return

        self.janela.open = False
        self.page.update()

        self.page.voltar_dados['endereco'].append(self.page.route)
        self.page.voltar_dados['dados_pagina'].append({'id': self.matricula_id})

        self.page.session.set("tipo", "associado")
        self.page.session.set('id', resposta.data)
        self.page.go('/formulario')

    def cancelar(self):
        self.janela.open = False
        self.page.update()


class janelaAcontecimento:
    def __init__(self, page, id_matricula, id_acontecimento=0, ao_salvar=None, escopo=False, ao_fechar=None):
        self.page = page
        self.id_matricula = id_matricula
        self.id_acontecimento = id_acontecimento
        self.ao_salvar = ao_salvar
        self.escopo = escopo
        self.ao_fechar = ao_fechar
        
        self.dados_acontecimento = self.obter_dados()
        if not self.dados_acontecimento:
            aviso(self.page, "Erro ao carregar dados do acontecimento")
            return
            
        self.controles_dinamicos = {}
        self.exibir_janela()

    def obter_dados(self):
        try:
            resposta = self.page.cliente.rpc(
                'obter_acontecimento',
                {
                    'p_id': int(self.id_matricula),
                    'p_escopo': self.escopo,
                    'p_acontecimento_id': int(self.id_acontecimento)
                }
            ).execute()
            dados = resposta.data
            if isinstance(dados, str):
                import json
                dados = json.loads(dados)
            return dados
        except Exception as err:
            print(f"Erro ao obter acontecimento: {err}")
            return None

    def montar_janela(self):
        dados_basicos = self.dados_acontecimento.get('dados', {})
        data_inicial = dados_basicos.get('data') or ''
        
        mascara_data = aplicarMascara('data')
        data_formatada = mascara_data.aplicar_mascara(data_inicial)
        
        self.input_data = ft.TextField(
            label="Data", 
            value=data_formatada,
            width=150, 
            on_change=mascara_data.on_change
        )
        
        lista_tipos = self.dados_acontecimento.get('tipos') or []
        lista_tipos_ordenados = sorted(lista_tipos, key=lambda x: x.get('ordem', 0))
        
        opcoes_tipo = [
            ft.dropdown.Option(key=str(t['id']), text=t['nome'])
            for t in lista_tipos_ordenados
        ]
        
        tipo_inicial = str(dados_basicos.get('tipo') or '')
        self.dd_tipo = ft.Dropdown(
            options=opcoes_tipo,
            value=tipo_inicial if tipo_inicial else None,
            width=300,
            label="Tipo de acontecimento",
            on_change=self.tipo_alterado,
            disabled=(self.id_acontecimento != 0)
        )
        
        self.container_campos = ft.Column(spacing=10)
        self.txt_mensagem = ft.Text("", color=ft.Colors.RED_700, size=13)
        
        self.btn_eliminar = ft.ElevatedButton(
            "Eliminar", 
            color=ft.Colors.WHITE,
            bgcolor=ft.Colors.RED_700, 
            on_click=self.eliminar_acontecimento,
            visible=self.dados_acontecimento.get('permitido_eliminar', False)
        )
        
        self.btn_salvar = ft.ElevatedButton(
            "Salvar", 
            on_click=self.salvar_acontecimento
        )
        
        self.btn_cancelar = ft.ElevatedButton(
            "Cancelar", 
            on_click=self.fechar_janela
        )
        
        self.atualizar_campos_dinamicos()
        
        layout_conteudo = ft.Container(
            width=480,
            content=ft.Column([
                ft.Row([self.input_data, self.dd_tipo], spacing=10),
                ft.Divider(height=10),
                self.container_campos,
                self.txt_mensagem
            ], spacing=10, scroll=ft.ScrollMode.AUTO),
            padding=10
        )
        
        titulo_dialog = "Editar Acontecimento" if self.id_acontecimento != 0 else "Novo Acontecimento"
        
        self.janela = ft.AlertDialog(
            title=ft.Text(titulo_dialog),
            content=layout_conteudo,
            actions=[
                self.btn_eliminar,
                self.btn_salvar,
                self.btn_cancelar
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )
        return self.janela

    def tipo_alterado(self, e):
        self.atualizar_campos_dinamicos()

    def atualizar_campos_dinamicos(self):
        self.container_campos.controls.clear()
        self.controles_dinamicos.clear()
        
        tipo_selecionado = self.dd_tipo.value
        if not tipo_selecionado:
            if self.container_campos.page:
                self.container_campos.update()
            return
            
        detalhes_map = self.dados_acontecimento.get('detalhes') or {}
        campos_lista = detalhes_map.get(str(tipo_selecionado)) or []
        campos_lista_ordenados = sorted(campos_lista, key=lambda x: x.get('ordem', 999))
        
        tipos_lista = self.dados_acontecimento.get('tipos') or []
        tipo_info = next((t for t in tipos_lista if str(t['id']) == str(tipo_selecionado)), None)
        exige_verificacao = tipo_info.get('verificar', False) if tipo_info else False
        
        self.btn_salvar.text = "Verificar" if exige_verificacao else "Salvar"
        
        for field in campos_lista_ordenados:
            campo_name = field['campo']
            rotulo = field['rotulo']
            mascara = field.get('mascara')
            valor_inicial = field.get('valor')
            if valor_inicial is None:
                valor_inicial = ''
            else:
                valor_inicial = str(valor_inicial)
            
            if mascara:
                mask_inst = aplicarMascara(mascara)
                valor_inicial = mask_inst.aplicar_mascara(valor_inicial)
                on_change_cb = mask_inst.on_change
            else:
                mask_inst = None
                on_change_cb = None
                
            if campo_name == 'observacoes' and not mascara:
                tf = ft.TextField(
                    label=rotulo,
                    value=valor_inicial,
                    multiline=True,
                    min_lines=2,
                    max_lines=4,
                    width=460
                )
            else:
                tf = ft.TextField(
                    label=rotulo,
                    value=valor_inicial,
                    on_change=on_change_cb,
                    width=460
                )
            
            self.container_campos.controls.append(tf)
            self.controles_dinamicos[campo_name] = {
                'control': tf,
                'field_def': field,
                'mask_inst': mask_inst
            }
            
        if self.container_campos.page:
            self.container_campos.update()
            self.btn_salvar.update()

    def exibir_janela(self):
        self.janela = self.montar_janela()
        self.page.overlay.append(self.janela)
        self.janela.open = True
        self.page.update()

    def fechar_janela(self, e=None):
        self.janela.open = False
        self.page.update()
        if self.ao_fechar and callable(self.ao_fechar):
            self.ao_fechar()

    def eliminar_acontecimento(self, e):
        try:
            self.page.cliente.table('acontecimentos').delete().eq('id', self.id_acontecimento).execute()
            if self.ao_salvar:
                self.ao_salvar()
            self.fechar_janela()
        except Exception as ex:
            self.txt_mensagem.value = f"Erro ao eliminar: {ex}"
            self.txt_mensagem.update()

    def salvar_acontecimento(self, e):
        data_raw = self.input_data.value
        mask_data = aplicarMascara('data')
        data_limpa = mask_data.salvar_limpo(data_raw)
        
        try:
            dt = datetime.strptime(data_raw, '%d/%m/%Y')
            data_db = dt.strftime('%Y-%m-%d')
        except ValueError:
            self.txt_mensagem.value = "Por favor, insira uma data válida (DD/MM/YYYY)."
            self.txt_mensagem.update()
            return
            
        tipo_selecionado = self.dd_tipo.value
        if not tipo_selecionado:
            self.txt_mensagem.value = "Selecione um tipo de acontecimento."
            self.txt_mensagem.update()
            return
            
        # Atualizar valores na estrutura original (mesma que veio de obter_acontecimento)
        dados_basicos = self.dados_acontecimento.get('dados', {})
        dados_basicos['data'] = data_db
        dados_basicos['tipo'] = int(tipo_selecionado)

        # Atualizar valores dos detalhes na lista original
        detalhes_map = self.dados_acontecimento.get('detalhes') or {}
        campos_lista = detalhes_map.get(str(tipo_selecionado)) or []
        for field in campos_lista:
            campo_name = field['campo']
            if campo_name in self.controles_dinamicos:
                info = self.controles_dinamicos[campo_name]
                raw_val = info['control'].value or ""
                if info['mask_inst']:
                    field['valor'] = info['mask_inst'].salvar_limpo(raw_val)
                else:
                    field['valor'] = raw_val

        try:
            resposta = self.page.cliente.rpc(
                'salvar_acontecimento',
                {'p_json': self.dados_acontecimento}
            ).execute()

            resultado = resposta.data
            if isinstance(resultado, str):
                import json
                resultado = json.loads(resultado)

            if not resultado.get('ok'):
                self.txt_mensagem.value = resultado.get('erro', 'Erro desconhecido ao salvar.')
                self.txt_mensagem.update()
                return

            novos_dados = resultado.get('detalhes') or resultado.get('acontecimentos')
            if self.ao_salvar and callable(self.ao_salvar):
                self.ao_salvar(novos_dados)
            self.fechar_janela()
        except Exception as ex:
            self.txt_mensagem.value = f"Erro ao salvar: {ex}"
            self.txt_mensagem.update()


def iniciar_matricula(matricula = 7):
    def main(page: ft.Page):
        from escudo_supabase import login_supabase
        page.cliente = login_supabase()
        page.session.set("id", matricula)
        page.avancar_dados = {'endereco': [], 'dados_pagina': []}
        page.voltar_dados = {'endereco': [], 'dados_pagina': []}
        
        MatriculaBase(page)

    return main

if __name__ == "__main__":
    ft.app(target=iniciar_matricula(), view=ft.AppView.WEB_BROWSER)
