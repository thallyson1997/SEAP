
from flask import Flask, render_template, request, redirect, url_for

import json
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), 'funcoes'))
from funcoes.tabular import extrair_tabela_dados
from funcoes.unir_tabelas import unir_tabelas_html


app = Flask(__name__)

# Caminho do arquivo de dados
CAMINHO_DADOS = os.path.join(os.path.dirname(__file__), 'dados', 'lote1.json')


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
    erro = None
    sucesso = None
    dados = ler_dados()
    if request.method == 'POST':
        acao = request.form.get('acao')
        if acao == 'adicionar_editar':
            presidio = request.form.get('presidio')
            texto = request.form.get('texto')
            tabela = request.form.get('tabela')
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
                        encontrado = True
                        sucesso = f'Dado do presídio "{presidio}" atualizado com sucesso.'
                        break
                if not encontrado:
                    dados.append({'presidio': presidio, 'texto': texto, 'tabela_html': tabela_html, 'mes': mes, 'ano': ano})
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
    return render_template('lote1.html', dados=dados_filtrados, tabela_unica_html=tabela_unica_html, erro=erro, sucesso=sucesso, meses=meses, mes=mes, ano=ano)

if __name__ == '__main__':
    app.run(debug=True)