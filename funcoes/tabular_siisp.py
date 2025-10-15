import re

def tratar_siisp_texto(texto):
    """
    Recebe o texto do campo SIISP (um número por linha, ou separados por espaço/comma) e retorna uma lista de strings limpas.
    """
    if not texto:
        return []
    # Aceita números separados por espaço, vírgula ou nova linha
    partes = re.split(r'[\s,;]+', texto.strip())
    return [p for p in partes if p.isdigit()]
