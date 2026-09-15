import re

class aplicarMascara():
    """Aplica uma máscara de formatação a um valor.
    Se mascaras=None, o método aplicar_mascara devolve o valor inalterado (no-op).
    """
    def __init__(self, mascaras: str | None):
        if mascaras == 'data':
            self.aplicar_mascara = self._aplicar_mascara_data
            self.salvar_limpo = self._salvar_limpo_data
            self.on_change = self._on_change_data
        elif mascaras:
            self.mascaras = sorted(mascaras.split('; '), key=lambda x: x.count('#'))
            self.c_mascaras = [x.count('#') for x in self.mascaras]
            self.aplicar_mascara = self._aplicar_mascara_texto
            self.salvar_limpo = self._salvar_limpo_texto
            self.on_change = self._on_change_texto   # formata o display em tempo real
        else:
            self.aplicar_mascara = lambda valor: valor  # no-op
            self.salvar_limpo = lambda valor: valor
            self.on_change = lambda e: None             # no-op

    def _aplicar_mascara_texto(self, valor):
        if not valor:
            return ''
        valor_limpo = re.sub(r'[^0-9]', '', str(valor))
        if len(valor_limpo) == 0:
            return ''

        # Decidir máscara aplicável
        c = len(valor_limpo)
        id_mascara = next((i for i, limite in enumerate(self.c_mascaras) if c <= limite), -1)
        mascara = self.mascaras[id_mascara] if id_mascara != -1 else self.mascaras[-1]

        # Aplicar máscara
        i = 0
        valor_final = ''
        for m in mascara:
            if m == '#':
                if i >= c:
                    break
                valor_final += valor_limpo[i]
                i += 1
            else:
                valor_final += m

        return valor_final

    def _salvar_limpo_texto(self, valor):
        if not valor:
            return ''
        return re.sub(r'[^0-9]', '', str(valor))

    def _on_change_texto(self, e):
        """Formata o valor enquanto o utilizador digita, actualizando o controlo."""
        e.control.value = self._aplicar_mascara_texto(e.control.value)
        e.control.update()

    def _aplicar_mascara_data(self, valor):
        if not valor:
            return ''
        valor_str = str(valor).strip()
        match = re.match(r'^(\d{4})[-/](\d{2})[-/](\d{2})', valor_str)
        if match:
            aaaa, mm, dd = match.groups()
            return f"{dd}/{mm}/{aaaa}"
        return self._formatar_data_slash(valor_str)

    def _salvar_limpo_data(self, valor):
        if not valor:
            return ''
        valor_str = str(valor).strip()
        if re.match(r'^\d{4}[-/]\d{2}[-/]\d{2}$', valor_str):
            return valor_str.replace('-', '/')
        digitos = re.sub(r'[^0-9]', '', valor_str)
        if len(digitos) == 8:
            dd = digitos[:2]
            mm = digitos[2:4]
            aaaa = digitos[4:]
            return f"{aaaa}/{mm}/{dd}"
        return valor_str

    def _on_change_data(self, e):
        e.control.value = self._formatar_data_slash(e.control.value)
        e.control.update()

    def _formatar_data_slash(self, valor_bruto):
        if not valor_bruto:
            return ''
        data = re.sub(r'[^0-9]', '', str(valor_bruto))
        data = data[:8]
        
        if len(data) <= 2:
            valor = data
        elif len(data) == 2 and data[0] > '3':
            valor = f"0{data[0]}/{data[1:]}"
        elif len(data) == 3 and data[2] > '2':
            valor = f"{data[:2]}/0{data[2]}"
        elif len(data) == 3:
            valor = f"{data[:2]}/{data[2]}"
        elif len(data) == 4:
            valor = f"{data[:2]}/{data[2:]}"
        else:
            valor = f"{data[:2]}/{data[2:4]}/{data[4:]}"
        
        return valor



def formatar_data(valor_bruto):
    data = re.sub(r'[^0-9]', '', valor_bruto)
    data = data[:8]
    
    if len(data) <= 2:
        valor = data
    elif len(data) == 2 and data[0] > '3':
        valor = f"0{data[0]}-{data[1:]}"
    elif len(data) == 3 and data[2] > '2':
        valor = f"{data[:2]}-0{data[2]}"
    elif len(data) == 3:
        valor = f"{data[:2]}-{data[2]}"
    elif len(data) == 4:
        valor = f"{data[:2]}-{data[2:]}"
    else:
        valor = f"{data[:2]}-{data[2:4]}-{data[4:]}"
    
    return valor