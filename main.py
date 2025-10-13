
from flask import Flask, render_template, request, redirect, url_for

import json
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), 'funcoes'))
from tabular import extrair_tabela_dados


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
    return render_template('index.html')







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
                    if item['presidio'] == presidio:
                        item['texto'] = texto
                        item['tabela_html'] = tabela_html
                        encontrado = True
                        sucesso = f'Dado do presídio "{presidio}" atualizado com sucesso.'
                        break
                if not encontrado:
                    dados.append({'presidio': presidio, 'texto': texto, 'tabela_html': tabela_html})
                    sucesso = f'Dado do presídio "{presidio}" adicionado com sucesso.'
                salvar_dados(dados)
                return redirect(url_for('lote1'))
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

    return render_template('lote1.html', dados=ler_dados(), erro=erro, sucesso=sucesso)

if __name__ == '__main__':
    app.run(debug=True)