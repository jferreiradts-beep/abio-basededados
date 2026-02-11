from reportlab.pdfgen import canvas
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.lib.pagesizes import A4, landscape, portrait
from pypdf import PdfReader, PdfWriter
from io import BytesIO
from copy import deepcopy
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

from escudo_supabase import login_supabase
from formatar_campos import formatar_cpf_cnpj


class obterDados:
    def __init__(self, cliente, escopo_id):
        self.cliente = cliente
        self.escopo_id = escopo_id
        self.capa = self.obter_dados_capa()
        self.produtos = self.obter_produtos()
        self.linha_associados = self.obter_associados_por_escopo() 
        
    def obter_dados_capa(self):
        resposta = self.cliente.rpc('obter_dados_escopo', {'p_escopo_id': self.escopo_id}).execute()
        return resposta.data

    def obter_produtos(self):
        resposta = self.cliente.rpc('obter_produtos', {'p_escopo_id': self.escopo_id}).execute()
        return resposta.data[next(iter(resposta.data))]

    def obter_associados_por_escopo(self):
        resposta = self.capa['associados']
        # Se nenhum associado estiver vinculado, mostrar todos
        associados_vinculados = [v for v in resposta if v['vinculo']]
        if len(associados_vinculados) == 0:
            associados_vinculados = resposta

        texto = []
        for associado in associados_vinculados:
            texto.append(f"{associado['nome']} - {formatar_cpf_cnpj(associado['cpf'])}")

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
    def __init__(self, cliente, escopo_id):
        self.cliente = cliente
        self.escopo_id = escopo_id
        self.dados = obterDados(self.cliente, self.escopo_id)
    
    def criar_canvas_capa(self):
        buffer = BytesIO()
        can = canvas.Canvas(buffer, pagesize=landscape(A4))

        linha = CaixaTexto(self.dados.linha_associados, 700).fazer_caixa(can, 60, 380, 'centro')
        linha = CaixaTexto("Produtor(a)", 700, pontos=10).fazer_caixa(can, 60, linha+5, 'centro')
        linha = CaixaTexto(f"Matrícula: {self.dados.capa['matricula']}", 700, pontos=14).fazer_caixa(can, 60, linha-5, 'centro')
        linha = CaixaTexto(self.dados.capa['unidade_producao'], 700, fonte='Times-Bold').fazer_caixa(can, 60, linha-5, 'centro')
        linha = CaixaTexto("Unidade de produção", 700, pontos=10).fazer_caixa(can, 60, linha+5, 'centro')
        
        endereco = f"{self.dados.capa['endereco']} - {self.dados.capa['municipio']} - {self.dados.capa['estado']}"
        linha = CaixaTexto(endereco, 700, fonte='Times-Bold').fazer_caixa(can, 60, linha-10, 'centro')

        mensagem = f"A ABIO - ASSOCIAÇÃO DE AGRICULTORES BIOLÓGICOS DO ESTADO DO RIO DE JANEIRO - CERTIFICA O(S) PRODUTOR(ES) ACIMA NO ESCOPO DE {self.dados.capa['tipo_certificado'].upper()}, DE ACORDO COM A LEI 10.831 DE 23 DE DEZEMBRO DE 2003, COM O DECRETO 6.323 DE 27 DE DEZEMBRO DE 2007 E COM A PORTARIA 52 DE 15 DE MARÇO DE 2021, CONFORME A LISTAGEM NO VERSO."
        linha = CaixaTexto(mensagem, 700, fonte='Times-Bold', pontos=14).fazer_caixa(can, 60, linha-20, 'justificado')

        emissao = datetime.strptime(self.dados.capa['data_emissao'], '%Y-%m-%d')
        CaixaTexto(f"Data de Emissão: {emissao.strftime('%d/%m/%Y')}", 700, fonte='Times-Bold', pontos=14).fazer_caixa(can, 60, 80, 'esquerda')
        validade =  emissao + relativedelta(years=1) - timedelta(days=1)
        CaixaTexto(f"Data de Validade: {validade.strftime('%d/%m/%Y')}", 700, fonte='Times-Bold', pontos=14).fazer_caixa(can, 60, 80, 'direita')
        
        linha = CaixaTexto('WELLINGTON MARY', 700, fonte='Times-Bold', pontos=14).fazer_caixa(can, 60, 80, 'centro')
        linha = CaixaTexto('DIRECTOR TÉCNICO DA ABIO', 700, fonte='Times-Bold', pontos=10).fazer_caixa(can, 60, linha, 'centro')
        
        can.save()
        buffer.seek(0)
        return buffer

    def criar_caixas_produtos(self, altura = 400):
        lista_caixas = {}
        comprimento = 0
        pagina = 0
        lista_caixas[f'pagina_{pagina}'] = []
        for produto in self.dados.produtos:
            titulo = CaixaTexto(produto['grupo'], 700, fonte='Times-Bold')
            lista_produtos = ', '.join(produto['produtos']) + ' //-----------------//'
            lista_produtos = CaixaTexto(lista_produtos, 700)
            
            if comprimento + titulo.altura + lista_produtos.altura > altura:
                comprimento = 0
                pagina += 1
                lista_caixas[f'pagina_{pagina}'] = []

            lista_caixas[f'pagina_{pagina}'].append((titulo, lista_produtos))
            comprimento += titulo.altura + lista_produtos.altura + 20

        return lista_caixas

    def criar_canvas_produto(self, pagina):
        buffer = BytesIO()
        can = canvas.Canvas(buffer, pagesize=landscape(A4))
        
        # Dados à esquerda: matrícula e validade
        linha = CaixaTexto(f"Matrícula: {self.dados.capa['matricula']}", 700, pontos=10).fazer_caixa(can, 60, 520, 'esquerda')
        validade = datetime.strptime(self.dados.capa['data_emissao'], '%Y-%m-%d') + relativedelta(years=1) - timedelta(days=1)
        linha = CaixaTexto(f"Validade: {validade.strftime('%d/%m/%Y')}", 700, pontos=10).fazer_caixa(can, 60, linha, 'esquerda')

        # Dados à direita: produtores
        linha = 520
        caixas_produtores = [CaixaTexto(f"Produtor(es):", 700, fonte='Times-Bold', pontos=10)]
        for produtor in self.dados.capa['associados']:
            caixas_produtores.append(CaixaTexto(produtor['nome'], 700, pontos=10))

        posicao = 60 + 700 - max(caixa.largura_texto for caixa in caixas_produtores)
        for caixa in caixas_produtores:
            linha = caixa.fazer_caixa(can, posicao, linha, 'esquerda')        

        # Produtos
        linha = 460
        for titulo, lista_produtos in pagina:
            linha = titulo.fazer_caixa(can, 60, linha, 'esquerda')
            linha = lista_produtos.fazer_caixa(can, 60, linha, 'justificado')
            linha -= 20
        can.save()
        buffer.seek(0)
        return buffer

    def gerar_certificado(self):
        writer = PdfWriter()
        
        # Criar capa
        base_capa = PdfReader("mapa/certificado_capa.pdf")
        base_capa = base_capa.pages[0]
        base_capa = template_capa.pages[0]
        base_capa.merge_page(PdfReader(buffer).pages[0])
        writer.add_page(base_capa)

        # Criar produtos
        lista_caixas = self.criar_caixas_produtos()
        for i, pagina in enumerate(lista_caixas):
            base_produtos = PdfReader("mapa/certificado_produtos.pdf")
            base_produtos = base_produtos.pages[0]
            base_produtos = template_produtos.pages[0]
            base_produtos.merge_page(PdfReader(buffer).pages[0])
            writer.add_page(base_produtos)
        
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
        
        linha_ass = CaixaTexto('Associado(s):', 160, fonte='Times-Bold', pontos= 12).fazer_caixa(can, 40, linha - 30)
        linha_ass -= 5
        for associado in self.dados.capa['associados']:
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
        lista_produtos = sorted(lista_produtos)

        buffer_produtos = BytesIO()
        can = canvas.Canvas(buffer_produtos, pagesize=portrait(A4))
        coluna = 560 / 2 + 5
        i = 0

        linha = self.montar_cabecalho(can) - 20

        for i in range(0, len(lista_produtos), 2):
            produto1 = lista_produtos[i]
            produto2 = lista_produtos[i+1] if i+1 < len(lista_produtos) else None
            
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

            if linha < 100:
                can.showPage()
                linha = self.montar_cabecalho(can) - 20
            
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

if __name__ == "__main__":
    cliente = login_supabase()
    # montarCertificado(cliente, 111).imprimir_certificado()
    montarFRI(cliente, 111).imprimir_fri()
    
