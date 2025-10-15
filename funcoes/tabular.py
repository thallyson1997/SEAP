import pandas as pd
import re
from io import StringIO
from tabulate import tabulate

def extrair_tabela_dados(text_pdf: str):
  linhas = [re.sub(r'\s+', '\t', linha.strip()) for linha in text_pdf.splitlines() if linha.strip()]
  texto_formatado = '\n'.join(linhas)
  df = pd.read_csv(StringIO(texto_formatado), sep='\t', header=None)

  df = df.iloc[:, 1:]

  if df.shape[1] > 8:
    df = df.iloc[:, :-1]

  nomes_colunas = [
      "Café Interno",
      "Café Funcionário",
      "Almoço Interno",
      "Almoço Funcionário",
      "Lanche Interno",
      "Lanche Funcionário",
      "Jantar Interno",
      "Jantar Funcionário"
  ]

  df.columns = nomes_colunas[:df.shape[1]]

  # Adiciona coluna Data baseada no mês e ano
  import calendar
  import flask
  # Tenta obter mes/ano do request (POST ou GET)
  mes = flask.request.form.get('mes', type=int) or flask.request.args.get('mes', type=int)
  ano = flask.request.form.get('ano', type=int) or flask.request.args.get('ano', type=int)
  presidio = flask.request.form.get('presidio') or flask.request.args.get('presidio')
  siisp = flask.request.form.get('siisp') or flask.request.args.get('siisp')
  if not mes or not ano:
    raise ValueError('Mês e ano não informados para gerar coluna Data.')
  dias_mes = calendar.monthrange(ano, mes)[1]
  if len(df) != dias_mes:
    raise ValueError(f'O número de linhas ({len(df)}) não corresponde ao número de dias do mês selecionado ({dias_mes}).')
  df.insert(0, 'Data', [f"{str(dia).zfill(2)}/{str(mes).zfill(2)}/{ano}" for dia in range(1, dias_mes+1)])
  # Adiciona coluna Presídio como segunda coluna
  if not presidio:
    raise ValueError('Presídio não informado para gerar coluna Presídio.')
  df.insert(1, 'Presídio', [presidio] * dias_mes)
  # Adiciona coluna n° SIISP como terceira coluna (preenche vazio ou "Não Informado")
  if not siisp:
    siisp = ''
  df.insert(2, 'n° SIISP', [siisp if siisp else '0'] * dias_mes)

  # Adiciona 8 colunas extras para SIISP de cada refeição
  colunas_refeicao = [
      "Café Interno",
      "Café Funcionário",
      "Almoço Interno",
      "Almoço Funcionário",
      "Lanche Interno",
      "Lanche Funcionário",
      "Jantar Interno",
      "Jantar Funcionário"
  ]
  # Adiciona as colunas extras ao final
  nomes_siisp = []
  for col in colunas_refeicao:
    nome_siisp = f"{col} x SIISP"
    nomes_siisp.append(nome_siisp)
    df[nome_siisp] = '0'
  # Reordena para garantir que as colunas x SIISP fiquem no final
  cols_ordem = [c for c in df.columns if c not in nomes_siisp] + nomes_siisp
  df = df[cols_ordem]
  return df