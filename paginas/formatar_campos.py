import re

def formatar_cpf_cnpj(valor_bruto):
    cpf_cnpj = re.sub(r'[^0-9]', '', valor_bruto)
    cpf_cnpj = cpf_cnpj[:14]

    if len(cpf_cnpj) <= 3:
        valor = cpf_cnpj
    elif len(cpf_cnpj) <= 6:
        valor = f"{cpf_cnpj[:3]}.{cpf_cnpj[3:]}"
    elif len(cpf_cnpj) <= 9:
        valor = f"{cpf_cnpj[:3]}.{cpf_cnpj[3:6]}.{cpf_cnpj[6:]}"
    elif len(cpf_cnpj) <= 11:
        valor = f"{cpf_cnpj[:3]}.{cpf_cnpj[3:6]}.{cpf_cnpj[6:9]}-{cpf_cnpj[9:]}"
    elif len(cpf_cnpj) <= 12:
        valor = f"{cpf_cnpj[:2]}.{cpf_cnpj[2:5]}.{cpf_cnpj[5:8]}/{cpf_cnpj[8:]}"
    else:
        valor = (
            f"{cpf_cnpj[:2]}."
            f"{cpf_cnpj[2:5]}."
            f"{cpf_cnpj[5:8]}/"
            f"{cpf_cnpj[8:12]}-"
            f"{cpf_cnpj[12:]}"
        )
    
    return valor

def formatar_data(valor_bruto):
    data = re.sub(r'[^0-9]', '', valor_bruto)
    data = data[:8]
    
    if len(data) <= 4:
        valor = data
    elif len(data) == 5 and data[4] > '1':
        valor = f"{data[:4]}-0{data[4]}"
    elif len(data) == 6 and int(data[4:]) > 12:
        valor = f"{data[:4]}-0{data[4]}-{data[5]}"
    elif len(data) <= 6:
        valor = f"{data[:4]}-{data[4:]}"
    else:
        valor = f"{data[:4]}-{data[4:6]}-{data[6:]}"
    
    return valor