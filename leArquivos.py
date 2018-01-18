#coding='utf-8'
# Imports
import requests, errno
from bs4 import BeautifulSoup
import pandas as pd
import os
import matplotlib.pyplot as plt

# Lê dados de parlamentares das páginas de dados abertos do Senado
# Retorna um dicionário com parlamentares atuais e afastados
# Documentação da API do Senado Federal:
# http://legis.senado.leg.br/dadosabertos/docs/resource_ListaSenadorService.html
#
def leParlamentares():
    print('Lendo dados de parlamentares...')
    # Abre uma sessão e define que aceita json
    sessao = requests.Session()
    sessao.headers.update({'Accept':'application/json'})

    # Recupera lista de senadores atuais
    atual = sessao.get('http://legis.senado.leg.br/dadosabertos/senador/lista/atual')
    # Recupera lista de senadores afastados
    afastados = sessao.get('http://legis.senado.leg.br/dadosabertos/senador/lista/afastados')

    # Converte os resultados para json
    listaExercicio = atual.json()
    listaAfastados = afastados.json()

    # E localiza a lista de parlamentares
    parlamentares = listaExercicio['ListaParlamentarEmExercicio']['Parlamentares']
    parlamentaresAfastados = listaAfastados['AfastamentoAtual']['Parlamentares']

    print('Fim leitura...')
    # retorna um dicionario com as listas de senadores atuais e afastados 
    return {'atuais': parlamentares['Parlamentar'], 'afastados': parlamentaresAfastados['Parlamentar']}

# Lista de anos de mandato para contabilização
anos = [2015, 2016, 2017]

dadosSenado = pd.read_csv('csv/senado.csv', encoding='utf-8')
top10 = pd.read_csv('csv/top10.csv', encoding='utf-8')
gastoPartidos = pd.read_csv('csv/gastoPartidos.csv', encoding='utf-8')
gastoEstados = pd.read_csv('csv/gastoEstados.csv', encoding='utf-8')
sexo = pd.read_csv('csv/sexo.csv', encoding='utf-8')
sexoT = pd.read_csv('csv/sexoT.csv', encoding='utf-8')


# Calcula dados importantes
totalSenadores = len(dadosSenado)
totalHomens = len(dadosSenado[dadosSenado.sexo == "Masculino"])
totalMulheres = len(dadosSenado[dadosSenado.sexo == "Feminino"])
totalExercicio = len(dadosSenado[dadosSenado.status == 'Exercicio'])
totalMulheresExercicio = dadosSenado.query('sexo == "Feminino" and status == "Exercicio"').count()[0]
totalAfastados = len(dadosSenado[dadosSenado.status == 'Afastado'])
totalGasto = dadosSenado['gastos'].sum()

# Não contabiliza parlamentares que ainda não efetuaram gastos no cálculo de médias
gastoMedioSenadores = dadosSenado.query('gastos != 0')['gastos'].mean()
mediaGastosHomensExercicio = dadosSenado.query('gastos != 0 and sexo == "Masculino" and status == "Exercicio"')['gastos'].mean()
mediaGastosMulheresExercicio = dadosSenado.query('gastos !=0 and sexo == "Feminino" and status == "Exercicio"')['gastos'].mean()
# 10 maiores gastadores
top10 = dadosSenado.sort_values(by=['gastos'], ascending=[False]).head(10)

# Dataframes de gastos por estado e por partidos
gastoEstados = dadosSenado.groupby('UF').sum().sort_values(by=['gastos'], ascending=[False])
gastoPartidos = dadosSenado.groupby('partido').sum().sort_values(by=['gastos'], ascending=[False])
sexo = dadosSenado.rename(columns={'Participacao':'(Sexo, Situação)'}).groupby(['sexo', 'status'])['(Sexo, Situação)'].count()
sexoT = dadosSenado[['Participacao', 'sexo']].groupby(['sexo']).count()

# Imprime algumas informações do senado, pelos dados coletados
print("Há no senado {:d} senadores, distribuidos entre {:d} homens e {:d} mulheres".format(totalSenadores, totalHomens, totalMulheres))
print("As mulheres representam {:.2f}% do total".format(totalMulheres/totalSenadores*100))
print("Há {:d} senadores em exercício, destes {:d} são mulheres".format(totalExercicio, totalMulheresExercicio))
print("As mulheres representam {:.2f}% deste total".format(totalMulheresExercicio/totalExercicio*100))
print("O gasto médio de senadores homens em exercício foi de R$ {:.2f}".format(mediaGastosHomensExercicio))
print("O gasto médio de senadores mulheres em exercício foi de R$ {:.2f}".format(mediaGastosMulheresExercicio))
print("O gasto médio dos senadores, em exercício e afastados, foi de R$ {:.2f}".format(gastoMedioSenadores))
print("O montante de despesas parlamentares em {:d} anos foi de R$ {:.2f}, com media anual de R$ {:.2f}".format(len(anos), totalGasto, totalGasto/len(anos)))


# Gera gráficos
if not os.path.exists('imagensT'):
    os.makedirs('imagensT')

gEstados = gastoEstados[['gastos', 'gastos2015', 'gastos2016', 'gastos2017']].plot(kind='bar', rot = 0, title ="Gastos por Estado", figsize=(15, 5), legend=True, fontsize=12, colormap="Paired")
gEstados.get_figure().savefig('imagensT/gastoEstados.png')
gPartidos=gastoPartidos[['gastos', 'gastos2015', 'gastos2016', 'gastos2017']].plot(kind='bar', rot = 0,title ="Gastos por Partido", figsize=(15, 5), legend=True, fontsize=10, colormap="Paired")
gPartidos.get_figure().savefig('imagensT/gastoPartidos.png')
gSexo = sexo.plot(kind='pie', figsize=(12,12), fontsize=12, subplots=True, legend=False, colormap='Paired')
gSexo[0].get_figure().savefig('imagensT/distSexo.png')
gSexoT = sexoT[['Participacao']].plot(kind='pie', figsize=(5,5), subplots=True, legend=False, fontsize=12, colormap="Paired")
gSexoT[0].get_figure().savefig('imagensT/distSexoT.png')
gTop10 = top10[['gastos', 'gastos2015', 'gastos2016', 'gastos2017']].plot(kind='bar', rot=20, title ="10 maiores gastadores", x = top10['nome'], figsize=(15,8), legend=True, fontsize=12, colormap="Paired")
gTop10.get_figure().savefig('imagensT/10maiores.png')