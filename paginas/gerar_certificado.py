from reportlab.pdfgen import canvas
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.lib.pagesizes import A4, landscape
from pypdf import PdfReader, PdfWriter
from io import BytesIO
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
        print(resposta.data)
        return next(iter(resposta.data))

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
        self.texto = texto
        self.largura = largura
        self.fonte = fonte
        self.pontos = pontos
        self.linhas, self.altura = self.quebrar_texto()

    def quebrar_texto(self):
        palavras = self.texto.split()
        linhas = []
        linha_atual = ''
        
        for palavra in palavras:
            if stringWidth(linha_atual + palavra, self.fonte, self.pontos) > self.largura:
                linhas.append(linha_atual)
                linha_atual = palavra
            else:
                linha_atual += ' ' + palavra
        linhas.append(linha_atual)

        return linhas, len(linhas) * self.pontos * 1.2

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

        linha = CaixaTexto(self.dados.linha_associados, 700).fazer_caixa(can, 60, 360, 'centro')
        linha = CaixaTexto("Produtor(a)", 700, pontos=10).fazer_caixa(can, 60, linha+5, 'centro')
        linha = CaixaTexto(self.dados.capa['matricula'], 700, fonte='Times-Bold').fazer_caixa(can, 60, linha-10, 'centro')
        linha = CaixaTexto("Matrícula", 700, pontos=10).fazer_caixa(can, 60, linha+5, 'centro')

        endereco = f"{self.dados.capa['endereco']} - {self.dados.capa['municipio']} - {self.dados.capa['estado']}"
        linha = CaixaTexto(endereco, 700, fonte='Times-Bold').fazer_caixa(can, 60, linha-20, 'centro')

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

    def gerar_capa(self):
        base = PdfReader("mapa/certificado_capa.pdf")
        pag_base = base.pages[0]
        buffer = self.criar_canvas_capa()
        pag_base.merge_page(PdfReader(buffer).pages[0])
        writer = PdfWriter()
        writer.add_page(pag_base)
        with open(f"certificado_capa_{self.escopo_id}.pdf", "wb") as f:
            writer.write(f)
    
    def criar_canvas_produto(self):
        print(self.dados.produtos)



if __name__ == "__main__":
    cliente = login_supabase()
    montarCertificado(cliente, 120).criar_canvas_produto()
    
