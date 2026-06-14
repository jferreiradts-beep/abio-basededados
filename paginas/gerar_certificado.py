from reportlab.pdfgen import canvas
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.lib.pagesizes import A4, landscape, portrait
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from pypdf import PdfReader, PdfWriter
from io import BytesIO
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import unicodedata

from escudo_supabase import login_supabase
from formatar_campos import formatar_cpf_cnpj


class obterDados:
    def __init__(self, cliente, escopo_id):
        self.cliente = cliente
        self.escopo_id = escopo_id
        self.capa = self.obter_dados_capa()
        self.validar_dados_capa()
        self.produtos = self.obter_produtos()
        self.linha_associados = self.obter_associados_por_escopo() 
        
    def obter_dados_capa(self):
        resposta = self.cliente.rpc('obter_dados_escopo', {'p_escopo_id': self.escopo_id}).execute()
        return resposta.data

    def validar_dados_capa(self):
        if not self.capa:
            raise ValueError("Não foi possível obter os dados do escopo.")
        
        campos_obrigatorios = {
            'matricula': 'Matrícula',
            'unidade_producao': 'Unidade de Produção',
            'endereco': 'Endereço',
            'municipio': 'Município',
            'estado': 'Estado',
            'tipo_certificado': 'Tipo de Certificado',
            'data_emissao': 'Data de Emissão'
        }
        
        faltando = []
        for chave, nome in campos_obrigatorios.items():
            if not self.capa.get(chave):
                faltando.append(nome)
                
        if faltando:
            raise ValueError(f"Faltam dados obrigatórios para gerar o documento: {', '.join(faltando)}")

    def obter_produtos(self):
        resposta = self.cliente.rpc('obter_produtos', {'p_escopo_id': self.escopo_id}).execute()
        if not resposta.data:
            raise ValueError("Faltam dados obrigatórios para gerar o documento: Produtos")
        try:
            return resposta.data[next(iter(resposta.data))]
        except StopIteration:
            raise ValueError("Faltam dados obrigatórios para gerar o documento: Produtos")

    def obter_associados_por_escopo(self):
        resposta = self.capa.get('associados')
        if not resposta:
            raise ValueError("Faltam dados obrigatórios para gerar o documento: Associados")
            
        # Se nenhum associado estiver vinculado, mostrar todos
        self.associados_vinculados = [v for v in resposta if v.get('vinculo', False)]
        if len(self.associados_vinculados) == 0:
            self.associados_vinculados = resposta

        texto = []
        for associado in self.associados_vinculados:
            texto.append(f"{associado.get('nome') or ''} - {formatar_cpf_cnpj(associado.get('cpf') or '')}")

        return ', '.join(texto)


class CaixaTexto:
    def __init__(self, texto, largura, fonte='Times-Roman', pontos = 16):
        self.texto = texto.strip()
        self.largura = largura
        self.fonte = fonte
        self.pontos = pontos
        self.linhas, self.altura, self.largura_texto = self.quebrar_texto()

    def quebrar_texto(self):
        palavras = self.texto.split()
        linhas = []
        linha_atual = ''
        largura_texto = 0
        
        for palavra in palavras:
            largura = stringWidth(linha_atual + palavra, self.fonte, self.pontos)
            if largura > self.largura:
                linhas.append(linha_atual)
                linha_atual = palavra
                
            else:
                linha_atual += ' ' + palavra
                largura_texto = largura if largura > largura_texto else largura_texto
        
        linhas.append(linha_atual)

        return linhas, len(linhas) * self.pontos * 1.2, int(largura_texto) + 1

    def fazer_caixa(self, can, x, y, alinhamento = 'esquerda'):
        can.setFont(self.fonte, self.pontos)
        if alinhamento == 'justificado':
            for i, linha in enumerate(self.linhas):
                if i < len(self.linhas) - 1:
                    self.desenhar_justificado(can, linha, x, y)
                else:
                    can.drawString(x, y, linha)
                y -= self.pontos * 1.2
        else:
            for linha in self.linhas:
                if alinhamento == 'esquerda':
                    can.drawString(x, y, linha)
                elif alinhamento == 'centro':
                    can.drawCentredString(x + self.largura / 2, y, linha)
                elif alinhamento == 'direita':
                    can.drawRightString(x + self.largura, y, linha)
                y -= self.pontos * 1.2
        return y
    
    def desenhar_justificado(self, can, linha, x, y):
        palavras = linha.split()
            
        # Caso só haja uma palavra, alinhar à direita
        if len(palavras) == 1:
            can.drawString(x, y, linha)
            return
                
        # Caso haja mais de uma palavra, justificar
        total_palavras = sum(stringWidth(p, self.fonte, self.pontos) for p in palavras)
        espacos = len(palavras) - 1
        extra = (self.largura - total_palavras) / espacos
        
        # Escrever a linha
        cursor = x
        for i, palavra in enumerate(palavras):
            can.drawString(cursor, y, palavra)
            cursor += stringWidth(palavra, self.fonte, self.pontos) 
            if i < espacos:
                cursor += extra
    
class montarCertificado():
    def __init__(self, cliente, escopo_id, nome_assinante="WELLINGTON MARY", cargo_assinante="DIRETOR TÉCNICO DA ABIO"):
        self.cliente = cliente
        self.escopo_id = escopo_id
        self.nome_assinante = nome_assinante
        self.cargo_assinante = cargo_assinante
        self.dados = obterDados(self.cliente, self.escopo_id)
    
    def criar_canvas_capa(self, can):
        linha = CaixaTexto(self.dados.linha_associados, 700).fazer_caixa(can, 60, 380, 'centro')
        linha = CaixaTexto("Produtor(a)", 700, pontos=10).fazer_caixa(can, 60, linha+5, 'centro')
        linha = CaixaTexto(f"Matrícula: {self.dados.capa['matricula']}", 700, pontos=14).fazer_caixa(can, 60, linha-5, 'centro')
        linha = CaixaTexto(self.dados.capa['unidade_producao'], 700, fonte='Times-Bold').fazer_caixa(can, 60, linha-5, 'centro')
        linha = CaixaTexto("Unidade de produção", 700, pontos=10).fazer_caixa(can, 60, linha+5, 'centro')
        
        endereco = f"{self.dados.capa['endereco']} - {self.dados.capa['municipio']} - {self.dados.capa['estado']}"
        linha = CaixaTexto(endereco, 700, fonte='Times-Bold').fazer_caixa(can, 60, linha-10, 'centro')
        linha = CaixaTexto(self.dados.capa['mensagem'], 700, fonte='Times-Bold', pontos=14).fazer_caixa(can, 60, linha-20, 'justificado')

        emissao = datetime.strptime(self.dados.capa['data_emissao'], '%Y-%m-%d')
        CaixaTexto(f"Data de Emissão: {emissao.strftime('%d/%m/%Y')}", 700, fonte='Times-Bold', pontos=14).fazer_caixa(can, 60, 80, 'esquerda')
        validade =  emissao + relativedelta(years=1) - timedelta(days=1)
        CaixaTexto(f"Data de Validade: {validade.strftime('%d/%m/%Y')}", 700, fonte='Times-Bold', pontos=14).fazer_caixa(can, 60, 80, 'direita')
        
        linha = CaixaTexto(self.nome_assinante, 700, fonte='Times-Bold', pontos=14).fazer_caixa(can, 60, 80, 'centro')
        linha = CaixaTexto(self.cargo_assinante, 700, fonte='Times-Bold', pontos=10).fazer_caixa(can, 60, linha, 'centro')

    def criar_canvas_cab_produtos(self, can):
        # Dados à esquerda: matrícula e validade
        linha = CaixaTexto(f"Matrícula: {self.dados.capa['matricula']}", 700, pontos=10).fazer_caixa(can, 60, 520, 'esquerda')
        validade = datetime.strptime(self.dados.capa['data_emissao'], '%Y-%m-%d') + relativedelta(years=1) - timedelta(days=1)
        linha = CaixaTexto(f"Validade: {validade.strftime('%d/%m/%Y')}", 700, pontos=10).fazer_caixa(can, 60, linha, 'esquerda')

        # Dados à direita: id
        ano_emissao = self.dados.capa['data_emissao'][:4]
        certificado_id = f"{ano_emissao}{int(self.escopo_id):05d}"
        linha = CaixaTexto(f"ID: {certificado_id}", 700, pontos=10).fazer_caixa(can, 60, 520, 'direita')       

    def criar_canvas_completo(self):
        buffer = BytesIO()
        can = canvas.Canvas(buffer, pagesize=landscape(A4))
        
        # Criar a capa
        self.criar_canvas_capa(can)
        can.showPage()

        # Criar os produtos
        self.criar_canvas_cab_produtos(can)
        linha = 460
        for produto in sorted(self.dados.produtos, key=lambda x: (x['grupo'] == 'Outros', unicodedata.normalize('NFD', x['grupo']))):
            titulo = CaixaTexto(produto['grupo'], 700, fonte='Times-Bold')
            lista_produtos = ', '.join(produto['produtos'])
            lista_produtos = CaixaTexto(lista_produtos, 700)

            if linha - titulo.altura - lista_produtos.altura < 60:
                can.showPage()
                self.criar_canvas_cab_produtos(can)
                linha = 460

            linha = titulo.fazer_caixa(can, 60, linha, 'esquerda')
            linha = lista_produtos.fazer_caixa(can, 60, linha, 'justificado')
            linha -= 20

        can.save()
        buffer.seek(0)
        return buffer

    def gerar_certificado(self):
        writer = PdfWriter()

        # Criar produtos
        pdf_canvas = PdfReader(self.criar_canvas_completo())
        for i, pagina in enumerate(pdf_canvas.pages):
            if i == 0:
                # Criar capa
                base = PdfReader("mapa/certificado_capa.pdf")
                base = base.pages[0]
            else:
                base = PdfReader("mapa/certificado_produtos.pdf")
                base = base.pages[0]

            base.merge_page(pagina)
            writer.add_page(base)
        
        # Salvar
        buffer_final = BytesIO()
        writer.write(buffer_final)
        buffer_final.seek(0)
        return buffer_final.getvalue()

    def imprimir_certificado(self):
        with open(f"Outros/certificado_produto_{self.escopo_id}.pdf", "wb") as f:
            f.write(self.gerar_certificado())


class montarFRI():
    def __init__(self, cliente, escopo_id):
        self.cliente = cliente
        self.escopo_id = escopo_id
        self.dados = obterDados(self.cliente, self.escopo_id)

    def montar_cabecalho(self, can):
        linha = CaixaTexto(self.dados.capa['unidade_producao'], 410, fonte='Times-Bold').fazer_caixa(can, 130, 750, 'centro')
        endereco = f"{self.dados.capa['endereco']} - {self.dados.capa['municipio']} - {self.dados.capa['estado']}"
        linha = CaixaTexto(endereco, 410, pontos=12).fazer_caixa(can, 130, linha)

        linha, largura = linha, 130
        caixa_mat_rotulo = CaixaTexto('Matrícula:', 410, fonte ='Times-Bold', pontos=12)
        caixa_mat_rotulo.fazer_caixa(can, largura, linha)
        largura += caixa_mat_rotulo.largura_texto + 5
        caixa_mat = CaixaTexto(self.dados.capa['matricula'], 410, pontos=12)
        caixa_mat.fazer_caixa(can, largura, linha)
        largura += caixa_mat.largura_texto + 20

        caixa_escopo_rotulo = CaixaTexto('Escopo:', 410, fonte='Times-Bold', pontos=12)
        caixa_escopo_rotulo.fazer_caixa(can, largura, linha)
        largura += caixa_escopo_rotulo.largura_texto + 5
        caixa_escopo = CaixaTexto(self.dados.capa['tipo_certificado'], 410, pontos=12)
        caixa_escopo.fazer_caixa(can, largura, linha)
        largura += caixa_escopo.largura_texto + 20

        emissao = datetime.strptime(self.dados.capa['data_emissao'], '%Y-%m-%d')
        validade =  emissao + relativedelta(years=1) - timedelta(days=1)
        caixa_validade_rotulo = CaixaTexto('Validade:', 410, fonte='Times-Bold', pontos=12)
        caixa_validade_rotulo.fazer_caixa(can, largura, linha)
        largura += caixa_validade_rotulo.largura_texto + 5
        caixa_validade = CaixaTexto(validade.strftime('%d/%m/%Y'), 410, pontos=12)
        caixa_validade.fazer_caixa(can, largura, linha)


        linha_ass = CaixaTexto('Associado(s):', 160, fonte='Times-Bold', pontos= 12).fazer_caixa(can, 40, linha - 30)
        linha_ass -= 5
        for associado in self.dados.associados_vinculados:
            linha_ass = CaixaTexto(associado['nome'], 160, pontos=12).fazer_caixa(can, 40, linha_ass)

        linha_gc = CaixaTexto('Grupo de Comercialização:', 200, fonte='Times-Bold', pontos=12).fazer_caixa(can, 200, linha-30)
        CaixaTexto('Data:', 100, fonte='Times-Bold', pontos=12).fazer_caixa(can, 460, linha-30)

        can.roundRect(200, linha_gc - 20, 240, 25, 5, stroke=1, fill=0)
        can.roundRect(460, linha_gc - 20, 100, 25, 5, stroke=1, fill=0)

        linha = min(linha_ass + 12 * 1.2, linha_gc) - 20
        can.line(40, linha, 560, linha)
        can.line(40, linha-2, 560, linha-2)

        linha = linha - 20
        CaixaTexto('Produtos', 100, fonte='Times-Bold', pontos=12).fazer_caixa(can, 40, linha)
        CaixaTexto('Und.', 100, fonte='Times-Bold', pontos=12).fazer_caixa(can, 200, linha)
        CaixaTexto('Qtd', 100, fonte='Times-Bold', pontos=12).fazer_caixa(can, 240, linha)

        coluna = 560 / 2 + 5
        CaixaTexto('Produtos', 100, fonte='Times-Bold', pontos=12).fazer_caixa(can, coluna + 5, linha)
        CaixaTexto('Und.', 100, fonte='Times-Bold', pontos=12).fazer_caixa(can, coluna + 200, linha)
        CaixaTexto('Qtd', 100, fonte='Times-Bold', pontos=12).fazer_caixa(can, coluna + 240, linha)

        return linha


    def gerar_pdf_produtos(self):
        lista_produtos = []
        for produto in self.dados.produtos:
            lista_produtos.extend(produto['produtos'])
        lista_produtos = sorted(lista_produtos, key=lambda s: unicodedata.normalize('NFD', s))

        buffer_produtos = BytesIO()
        can = canvas.Canvas(buffer_produtos, pagesize=portrait(A4))
        coluna = 560 / 2 + 5

        linha = self.montar_cabecalho(can) - 20

        for i in range(0, len(lista_produtos), 2):
            produto1 = lista_produtos[i]
            produto2 = lista_produtos[i+1] if i+1 < len(lista_produtos) else None

            # Calcula a altura que a linha vai ocupar ANTES de desenhar
            altura_linha = CaixaTexto(produto1, 145, pontos=12).altura
            if produto2:
                altura_linha = max(altura_linha, CaixaTexto(produto2, 145, pontos=12).altura)

            # Verifica quebra de página ANTES de desenhar (evita página em branco no final)
            if linha - altura_linha < 100:
                can.showPage()
                linha = self.montar_cabecalho(can) - 20

            p1_dados = CaixaTexto(produto1, 145, pontos=12)
            linha1 = linha2 = p1_dados.fazer_caixa(can, 40, linha)
            can.roundRect(200, linha -2, 30, 15, 5, stroke=1, fill=0)
            can.roundRect(240, linha -2, 35, 15, 5, stroke=1, fill=0)

            if produto2:
                p2_dados = CaixaTexto(produto2, 145, pontos=12)
                linha2 = p2_dados.fazer_caixa(can, coluna +5, linha)
                can.roundRect(coluna + 200, linha -2, 30, 15, 5, stroke=1, fill=0)
                can.roundRect(coluna + 240, linha -2, 35, 15, 5, stroke=1, fill=0)

            linha = min(linha1, linha2) - 5

        can.save()
        buffer_produtos.seek(0)
        return buffer_produtos


    def gerar_fri(self):
        pdf_produtos = PdfReader(self.gerar_pdf_produtos())

        # Preparar numeração de páginas
        buffer_num = BytesIO()
        can_num = canvas.Canvas(buffer_num, pagesize=portrait(A4))
        
        total_paginas = len(pdf_produtos.pages)
        for i in range(total_paginas):
            can_num.drawString(500, 40, f"p. {i+1} / {total_paginas}")
            if i < total_paginas - 1:
                can_num.showPage()

        can_num.save()
        buffer_num.seek(0)
        pdf_num = PdfReader(buffer_num)

        writer = PdfWriter()
        for i, produto in enumerate(pdf_produtos.pages):
            base_fri = PdfReader("mapa/modelo_FRI.pdf").pages[0]
            base_fri.merge_page(produto)
            base_fri.merge_page(pdf_num.pages[i])
            writer.add_page(base_fri)

        # Montar arquivo final
        buffer_final = BytesIO()
        writer.write(buffer_final)
        buffer_final.seek(0)
        return buffer_final.getvalue()

    def imprimir_fri(self):
        with open(f"Outros/fri_{self.escopo_id}.pdf", "wb") as f:
            f.write(self.gerar_fri())

class montarFichaGrupos():
    def __init__(self, cliente, dados_gerais, dados_tabela):
        self.cliente = cliente
        self.dados_gerais = dados_gerais
        self.dados_tabela = dados_tabela

    def gerar_pdf(self):
        from reportlab.lib.enums import TA_CENTER
        
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
        elementos = []
        
        styles = getSampleStyleSheet()
        estilo_titulo = styles['Heading1']
        estilo_normal = styles['Normal']
        
        estilo_celula = styles['Normal'].clone('estilo_celula')
        estilo_celula.alignment = TA_CENTER
        estilo_celula.fontSize = 10
        estilo_celula.leading = 12
        
        # Cabeçalho
        elementos.append(Paragraph(f"<b>Grupo:</b> {self.dados_gerais.get('nome') or ''}", estilo_titulo))
        elementos.append(Paragraph(f"<b>Núcleo:</b> {self.dados_gerais.get('nucleo') or ''}   |   <b>Coordenador:</b> {self.dados_gerais.get('coordenador') or ''}", estilo_normal))
        elementos.append(Spacer(1, 20))
        
        # Tabela
        dados_tabela_pdf = [['Matrícula', 'Primeiro Associado', 'Escopo', 'Validade', 'Últ. Movimento', 'Observações']]
        
        for item in self.dados_tabela:
            validade = item.get('validade') or ''
            if validade:
                validade = datetime.strptime(validade, '%Y-%m-%d').strftime('%d/%m/%Y')
            
            ultimo_movimento = item.get('ultimo_movimento') or ''
            if ultimo_movimento:
                # O último movimento costuma vir no formato DD/MM/AAAA ou YYYY-MM-DD dependendo do BD. Se falhar o parse, usa o texto puro.
                try:
                    if '-' in ultimo_movimento:
                        ultimo_movimento = datetime.strptime(ultimo_movimento, '%Y-%m-%d').strftime('%d/%m/%Y')
                except ValueError:
                    pass

            linha = [
                str(item.get('matricula') or ''),
                Paragraph(str(item.get('primeiro_associado') or ''), estilo_celula),
                Paragraph(str(item.get('escopo') or ''), estilo_celula),
                str(validade or ''),
                Paragraph(str(ultimo_movimento or ''), estilo_celula),
                '' # Observações em branco
            ]
            dados_tabela_pdf.append(linha)
            
        tabela = Table(dados_tabela_pdf, colWidths=[60, 200, 150, 70, 80, 220])
        tabela.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.grey),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,0), 10),
            ('BOTTOMPADDING', (0,0), (-1,0), 12),
            ('BACKGROUND', (0,1), (-1,-1), colors.white),
            ('GRID', (0,0), (-1,-1), 1, colors.black),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]))
        
        elementos.append(tabela)
        doc.build(elementos)
        
        buffer.seek(0)
        return buffer.getvalue()

    def imprimir_ficha(self, grupo_id):
        import time, os
        nome_arquivo = f"ficha_grupo_{grupo_id}_{int(time.time())}.pdf"
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
        with open(caminho_arquivo, "wb") as f:
            f.write(self.gerar_pdf())
            
        return f"/certificados/{nome_arquivo}"

if __name__ == "__main__":
    cliente = login_supabase()
    montarCertificado(cliente, 66).imprimir_certificado()
    # montarFRI(cliente, 111).imprimir_fri()
    
