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