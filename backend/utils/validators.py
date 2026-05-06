"""
Validadores de Documentos Brasileiros
CPF e CNPJ com dígito verificador
"""

import re

def validate_cpf(cpf: str) -> bool:
    """
    Valida CPF com dígito verificador
    """
    # Remover caracteres não numéricos
    cpf = re.sub(r'[^0-9]', '', cpf)
    
    # Verificar tamanho
    if len(cpf) != 11:
        return False
    
    # Verificar se todos dígitos são iguais (111.111.111-11)
    if cpf == cpf[0] * 11:
        return False
    
    # Calcular primeiro dígito verificador
    sum1 = 0
    for i in range(9):
        sum1 += int(cpf[i]) * (10 - i)
    
    remainder1 = sum1 % 11
    digit1 = 0 if remainder1 < 2 else 11 - remainder1
    
    # Verificar primeiro dígito
    if digit1 != int(cpf[9]):
        return False
    
    # Calcular segundo dígito verificador
    sum2 = 0
    for i in range(10):
        sum2 += int(cpf[i]) * (11 - i)
    
    remainder2 = sum2 % 11
    digit2 = 0 if remainder2 < 2 else 11 - remainder2
    
    # Verificar segundo dígito
    return digit2 == int(cpf[10])


def validate_cnpj(cnpj: str) -> bool:
    """
    Valida CNPJ com dígito verificador
    """
    # Remover caracteres não numéricos
    cnpj = re.sub(r'[^0-9]', '', cnpj)
    
    # Verificar tamanho
    if len(cnpj) != 14:
        return False
    
    # Verificar se todos dígitos são iguais
    if cnpj == cnpj[0] * 14:
        return False
    
    # Pesos para cálculo
    weights1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    weights2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    
    # Calcular primeiro dígito
    sum1 = sum(int(cnpj[i]) * weights1[i] for i in range(12))
    remainder1 = sum1 % 11
    digit1 = 0 if remainder1 < 2 else 11 - remainder1
    
    if digit1 != int(cnpj[12]):
        return False
    
    # Calcular segundo dígito
    sum2 = sum(int(cnpj[i]) * weights2[i] for i in range(13))
    remainder2 = sum2 % 11
    digit2 = 0 if remainder2 < 2 else 11 - remainder2
    
    return digit2 == int(cnpj[13])


def format_cpf(cpf: str) -> str:
    """Formata CPF: 12345678901 -> 123.456.789-01"""
    cpf = re.sub(r'[^0-9]', '', cpf)
    if len(cpf) != 11:
        return cpf
    return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"


def format_cnpj(cnpj: str) -> str:
    """Formata CNPJ: 12345678000190 -> 12.345.678/0001-90"""
    cnpj = re.sub(r'[^0-9]', '', cnpj)
    if len(cnpj) != 14:
        return cnpj
    return f"{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]}"
