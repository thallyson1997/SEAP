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
    idx_presidio = -1
    idx_data = -1
    for html in lista_tabelas:
        soup = BeautifulSoup(html, 'html.parser')
        if thead is None:
            thead_tag = soup.find('thead')
            if thead_tag:
                ths = thead_tag.find_all('th')
                idx_presidio = next((i for i, th in enumerate(ths) if 'presídio' in th.text.lower()), -1)
                idx_data = next((i for i, th in enumerate(ths) if 'data' in th.text.lower()), -1)
                if idx_presidio != -1 and idx_data != -1 and idx_data > idx_presidio:
                    novo_th = soup.new_tag('th')
                    novo_th.string = 'n° SIISP'
                    ths[idx_presidio].insert_after(novo_th)
                thead = str(thead_tag)
        tbody = soup.find('tbody')
        if tbody:
            for tr in tbody.find_all('tr'):
                tds = tr.find_all(['td', 'th'])
                # Garante que a linha tem o mesmo número de colunas do cabeçalho
                if idx_presidio != -1 and idx_data != -1 and idx_data > idx_presidio:
                    novo_td = soup.new_tag('td')
                    # Se já existe, mantém, senão coloca 'Não Informado'
                    if len(tds) > idx_presidio+1 and tds[idx_presidio+1].text.strip() and tds[idx_presidio+1].text.strip().lower() != 'não informado':
                        novo_td.string = tds[idx_presidio+1].text.strip()
                    else:
                        novo_td.string = 'Não Informado'
                    tds[idx_presidio].insert_after(novo_td)
                trs.append(str(tr))

    if not thead or not trs:
        return ''

    tabela_unica = f'<table border="1" class="dataframe tabela-extraida">{thead}<tbody>' + ''.join(trs) + '</tbody></table>'
    return tabela_unica
