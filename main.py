
from flask import Flask, render_template, request, redirect, url_for, jsonify

import json
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), 'funcoes'))

from funcoes.tabular import extrair_tabela_dados
from funcoes.unir_tabelas import unir_tabelas_html
from funcoes.tabular_siisp import tratar_siisp_texto
from bs4 import BeautifulSoup



app = Flask(__name__)

# Caminho do arquivo de dados
CAMINHO_DADOS = os.path.join(os.path.dirname(__file__), 'dados', 'lote1.json')

# Endpoint para alternar anotação de célula (persistente)
@app.route('/anotar_celula', methods=['POST'])
def anotar_celula():
    data = request.get_json()
    presidio = data.get('presidio')
    mes = int(data.get('mes'))
    ano = int(data.get('ano'))
    linha = str(data.get('linha'))
    coluna = str(data.get('coluna'))
    key = f'{linha}|{coluna}'
    dados = ler_dados()
    item = next((d for d in dados if d['presidio'] == presidio and d.get('mes') == mes and d.get('ano') == ano), None)
    if not item:
        return jsonify({'ok': False, 'msg': 'Presídio não encontrado'}), 404
    if 'anotacoes' not in item:
        item['anotacoes'] = {}
    if key in item['anotacoes']:
        del item['anotacoes'][key]
        marcado = False
    else:
        item['anotacoes'][key] = True
        marcado = True
    salvar_dados(dados)
    return jsonify({'ok': True, 'marcado': marcado})


def ler_dados():
    if not os.path.exists(CAMINHO_DADOS):
        return []
    with open(CAMINHO_DADOS, 'r', encoding='utf-8') as f:
        try:
            return json.load(f)
        except Exception:
            return []



def salvar_dados(lista):
    with open(CAMINHO_DADOS, 'w', encoding='utf-8') as f:
        json.dump(lista, f, ensure_ascii=False, indent=2)


@app.route('/')
def index():
    from datetime import datetime
    now = datetime.now()
    mes_atual = now.month
    meses = list(range(1, mes_atual))  # Janeiro (1) até mês anterior ao atual
    # Seleciona mês do filtro se vier por GET, senão o mais recente
    mes = request.args.get('mes', type=int) or (mes_atual-1)
    ano = 2025
    return render_template('index.html', meses=meses, mes=mes, ano=ano)







@app.route('/lote1', methods=['GET', 'POST'])
def lote1():
    import calendar
    erro = None
    sucesso = None
    dados = ler_dados()
    # Descobre mês e ano selecionados
    mes = request.args.get('mes', type=int) or request.form.get('mes', type=int) or 1
    ano = request.args.get('ano', type=int) or request.form.get('ano', type=int) or 2025
    try:
        dias_no_mes = calendar.monthrange(ano, mes)[1]
    except Exception:
        dias_no_mes = 31
    if request.method == 'POST':
        acao = request.form.get('acao')
        # Novo: Adicionar SIISP
        if 'siisp_presidio' in request.form and 'siisp_texto' in request.form:
            presidio = request.form.get('siisp_presidio')
            texto_siisp = request.form.get('siisp_texto')
            mes_post = request.form.get('mes', type=int)
            ano_post = request.form.get('ano', type=int)
            from datetime import datetime
            mes = mes_post or request.args.get('mes', type=int) or (datetime.now().month - 1)
            ano = ano_post or request.args.get('ano', type=int) or 2025
            # Busca o item do presídio e mês/ano
            item = next((d for d in dados if d['presidio'] == presidio and d.get('mes') == mes and d.get('ano') == ano), None)
            if not item:
                erro = f"Mapa do presídio '{presidio}' para {mes:02d}/{ano} não encontrado. Adicione o mapa antes de inserir SIISP."
            else:
                # Trata SIISP
                siisp_lista = tratar_siisp_texto(texto_siisp)
                # Carrega tabela HTML existente
                tabela_html = item.get('tabela_html')
                if not tabela_html:
                    erro = f"Mapa do presídio '{presidio}' não possui tabela para preencher SIISP."
                else:
                    soup = BeautifulSoup(tabela_html, 'html.parser')
                    tbody = soup.find('tbody')
                    linhas = tbody.find_all('tr') if tbody else []
                    if len(linhas) != len(siisp_lista):
                        erro = f"Quantidade de números SIISP ({len(siisp_lista)}) não corresponde ao número de dias do mês ({len(linhas)})."
                    else:
                        # Descobre índice da coluna n° SIISP
                        thead = soup.find('thead')
                        ths = thead.find_all('th') if thead else []
                        idx_siisp = next((i for i, th in enumerate(ths) if 'siisp' in th.text.lower()), None)
                        if idx_siisp is None:
                            erro = "Tabela não possui coluna 'n° SIISP'."
                        else:
                            # Descobre índices das colunas Interno e x SIISP
                            colunas = [th.text.strip().lower() for th in ths]
                            idxs = {col: i for i, col in enumerate(colunas)}
                            col_map = {
                                'café interno': 'café interno x siisp',
                                'almoço interno': 'almoço interno x siisp',
                                'lanche interno': 'lanche interno x siisp',
                                'jantar interno': 'jantar interno x siisp',
                            }
                            # Preenche cada linha
                            for i, tr in enumerate(linhas):
                                tds = tr.find_all(['td', 'th'])
                                if len(tds) > idx_siisp:
                                    tds[idx_siisp].string = siisp_lista[i]
                                # Para cada coluna Interno, calcula diferença e preenche coluna x SIISP
                                for col_interno, col_xsiisp in col_map.items():
                                    idx_interno = idxs.get(col_interno)
                                    idx_xsiisp = idxs.get(col_xsiisp)
                                    if idx_interno is not None and idx_xsiisp is not None:
                                        try:
                                            val_interno = int(tds[idx_interno].text.strip())
                                            val_siisp = int(siisp_lista[i])
                                            val_xsiisp = val_interno - val_siisp
                                        except Exception:
                                            val_xsiisp = ''
                                        tds[idx_xsiisp].string = str(val_xsiisp)
                            # Atualiza tabela_html
                            item['tabela_html'] = str(soup)
                            item['siisp'] = ' '.join(siisp_lista)
                            salvar_dados(dados)
                            sucesso = f"SIISP preenchido para '{presidio}' ({mes:02d}/{ano})."
                            return redirect(url_for('lote1', mes=mes, ano=ano))

        elif acao == 'adicionar_editar':
            presidio = request.form.get('presidio')
            texto = request.form.get('texto')
            tabela = request.form.get('tabela')
            siisp = request.form.get('siisp')
            # Novo: mês e ano podem vir do POST (form), senão do filtro (GET)
            mes_post = request.form.get('mes', type=int)
            ano_post = request.form.get('ano', type=int)
            mes = mes_post or request.args.get('mes', type=int) or (datetime.now().month - 1)
            ano = ano_post or request.args.get('ano', type=int) or 2025
            tabela_html = None
            if not tabela or not tabela.strip():
                erro = 'O campo Tabela é obrigatório.'
            if not erro:
                try:
                    # Passa siisp via request.form (já está disponível para extrair_tabela_dados)
                    df = extrair_tabela_dados(tabela)
                    tabela_html = df.to_html(index=False, classes='tabela-extraida')
                except Exception as e:
                    erro = f'Erro ao processar tabela: {e}'
            if not erro and presidio:
                encontrado = False
                for item in dados:
                    if item['presidio'] == presidio and item.get('mes') == mes and item.get('ano') == ano:
                        item['texto'] = texto
                        item['tabela_html'] = tabela_html
                        item['siisp'] = siisp
                        encontrado = True
                        sucesso = f'Dado do presídio "{presidio}" atualizado com sucesso.'
                        break
                if not encontrado:
                    dados.append({'presidio': presidio, 'texto': texto, 'tabela_html': tabela_html, 'mes': mes, 'ano': ano, 'siisp': siisp})
                    sucesso = f'Dado do presídio "{presidio}" adicionado com sucesso.'
                salvar_dados(dados)
                return redirect(url_for('lote1', mes=mes, ano=ano))
        elif acao == 'excluir':
            presidio = request.form.get('presidio_excluir')
            if presidio:
                novos_dados = [item for item in dados if item['presidio'] != presidio]
                if len(novos_dados) != len(dados):
                    salvar_dados(novos_dados)
                    sucesso = f'Dado do presídio "{presidio}" excluído com sucesso.'
                else:
                    erro = f'Presídio não encontrado para exclusão.'
                return redirect(url_for('lote1'))

    from datetime import datetime
    now = datetime.now()
    mes_atual = now.month
    meses = list(range(1, mes_atual))
    # Seleciona mês do filtro se vier por GET, senão o mais recente
    mes = request.args.get('mes', type=int) or (mes_atual-1)
    ano = 2025
    # Filtra os dados para exibir apenas os do mês/ano selecionados
    dados_filtrados = [item for item in ler_dados() if item.get('mes') == mes and item.get('ano') == ano]
    tabelas_html = [item['tabela_html'] for item in dados_filtrados if item.get('tabela_html')]
    tabela_unica_html = unir_tabelas_html(tabelas_html)

    # Realça as células das colunas x SIISP e aplica anotação amarela
    # Aplica anotação por presídio individualmente
    if tabela_unica_html:
        soup = BeautifulSoup(tabela_unica_html, 'html.parser')
        ths = [th.text.strip().lower() for th in soup.find_all('th')]
        # Apenas colunas "Interno x SIISP" recebem cor padrão
        nomes_interno_xsiisp = [
            'café interno x siisp',
            'almoço interno x siisp',
            'lanche interno x siisp',
            'jantar interno x siisp',
        ]
        nomes_funcionario_xsiisp = [
            'café funcionário x siisp',
            'almoço funcionário x siisp',
            'lanche funcionário x siisp',
            'jantar funcionário x siisp',
        ]
        idxs_xsiisp_interno = [i for i, col in enumerate(ths) if col in nomes_interno_xsiisp]
        idxs_xsiisp_funcionario = [i for i, col in enumerate(ths) if col in nomes_funcionario_xsiisp]
        # Para funcionário, precisamos também do índice SIISP correspondente
        idxs_siisp = {}
        for nome_func, nome_interno in zip(nomes_funcionario_xsiisp, nomes_interno_xsiisp):
            # Ex: 'café funcionário x siisp' -> 'café interno x siisp'
            idx_func = ths.index(nome_func) if nome_func in ths else None
            idx_siisp = ths.index('n° siisp') if 'n° siisp' in ths else None
            idxs_siisp[nome_func] = idx_siisp
        # Mapeia presídio para suas anotações
        anotacoes_map = {item['presidio']: item.get('anotacoes', {}) for item in dados_filtrados}
        for tr in soup.find_all('tr'):
            tds = tr.find_all(['td', 'th'])
            # Descobre presídio da linha (se existir coluna Presídio)
            idx_presidio = next((i for i, th in enumerate(ths) if th == 'presídio'), None)
            pres = tds[idx_presidio].text.strip() if idx_presidio is not None and idx_presidio < len(tds) else None
            anotacoes = anotacoes_map.get(pres, {}) if pres else {}
            row_idx = tr.parent.find_all('tr').index(tr)
            for col_idx, td in enumerate(tds):
                key = f'{row_idx}|{col_idx}'
                if anotacoes.get(key):
                    td['class'] = td.get('class', []) + ['celula-anotada']
            # INTERNOS: cor padrão
            for idx in idxs_xsiisp_interno:
                if idx < len(tds):
                    try:
                        val = int(tds[idx].text.strip())
                        if val <= 0:
                            tds[idx]['class'] = tds[idx].get('class', []) + ['xsiisp-verde']
                        elif 1 <= val <= 5:
                            tds[idx]['class'] = tds[idx].get('class', []) + ['xsiisp-azul']
                        elif val > 5:
                            tds[idx]['class'] = tds[idx].get('class', []) + ['xsiisp-vermelho']
                    except Exception:
                        pass
            # FUNCIONÁRIOS: verde se número de funcionários < SIISP, vermelho se >= SIISP
            for idx in idxs_xsiisp_funcionario:
                if idx < len(tds):
                    nome_col = ths[idx]
                    idx_siisp = idxs_siisp.get(nome_col)
                    try:
                        val_func = int(tds[idx].text.strip())
                        val_siisp = int(tds[idx_siisp].text.strip()) if idx_siisp is not None and idx_siisp < len(tds) else None
                        if val_siisp is not None:
                            if val_func < val_siisp:
                                tds[idx]['class'] = tds[idx].get('class', []) + ['xsiisp-verde']
                            else:
                                tds[idx]['class'] = tds[idx].get('class', []) + ['xsiisp-vermelho']
                    except Exception:
                        pass
        tabela_unica_html = str(soup)
    # Carrega preços do lote1
    precos_lote1 = {}
    try:
        with open(os.path.join(os.path.dirname(__file__), 'dados', 'precos_lotes.json'), encoding='utf-8') as f:
            precos_json = json.load(f)
            if isinstance(precos_json, dict):
                precos_lote1 = precos_json.get('lote1') or {}
            else:
                precos_lote1 = {}
    except Exception:
        precos_lote1 = {}
    if not isinstance(precos_lote1, dict):
        precos_lote1 = {}
    return render_template('lote1.html', dados=dados_filtrados, tabela_unica_html=tabela_unica_html, erro=erro, sucesso=sucesso, meses=meses, mes=mes, ano=ano, precos_lote1=precos_lote1, dias_no_mes=dias_no_mes)

if __name__ == '__main__':
    app.run(debug=True)