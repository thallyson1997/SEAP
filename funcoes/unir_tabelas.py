from bs4 import BeautifulSoup
from typing import List

def unir_tabelas_html(lista_tabelas: List[str]) -> str:
    """
    Recebe uma lista de strings HTML de tabelas (com thead e tbody) e retorna uma única tabela HTML
    contendo apenas um thead e todos os <tr> de todos os tbodys juntos em um único tbody.
    """
    if not lista_tabelas:
        return ''

    thead = None
    trs = []
    for html in lista_tabelas:
        soup = BeautifulSoup(html, 'html.parser')
        if thead is None:
            thead = str(soup.find('thead'))
        tbody = soup.find('tbody')
        if tbody:
            trs.extend([str(tr) for tr in tbody.find_all('tr')])

    if not thead or not trs:
        return ''

    tabela_unica = f'<table border="1" class="dataframe tabela-extraida">{thead}<tbody>' + ''.join(trs) + '</tbody></table>'
    return tabela_unica
