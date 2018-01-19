# coding='utf-8'
# Imports
import errno
from bs4 import BeautifulSoup
import pandas as pd
import os
import matplotlib.pyplot as plt

"""Lê dados de parlamentares de arquivos CSV e
gera gráficos, texto e páginas com o conteúdo
"""

# Lista de anos de mandato para contabilização
anos = [2015, 2016, 2017]

dadosSenado = pd.read_csv('csv/senado.csv', encoding='utf-8')
top10 = pd.read_csv('csv/top10.csv', encoding='utf-8')
gastoPartidos = pd.read_csv('csv/gastoPartidos.csv',
                            encoding='utf-8', index_col=0)
gastoEstados = pd.read_csv('csv/gastoEstados.csv',
                           encoding='utf-8', index_col=0)
#sexo = pd.read_csv('csv/sexo.csv', encoding='utf-8')
sexo = dadosSenado.rename(columns={'Participacao': '(Sexo, Situação)'}).groupby(
    ['sexo', 'status'])['(Sexo, Situação)'].count()
sexoT = pd.read_csv('csv/sexoT.csv', encoding='utf-8', index_col=0)

# Agrega dados do gabinete
def agregaGabinete(df, anos=[2015, 2016, 2017]):
    Gabinete = 'Gabinete-'
    Escritorio = 'Escritório(s) de Apoio-'
    for ano in anos:
        df[f'TotalGabinete-{ano}'] = df[f'{Gabinete}{ano}'] + \
            df[f'{Escritorio}{ano}']


agregaGabinete(dadosSenado)
agregaGabinete(top10)
agregaGabinete(gastoPartidos)
agregaGabinete(gastoEstados)


# Calcula dados importantes
totalSenadores = len(dadosSenado)
totalHomens = len(dadosSenado[dadosSenado.sexo == 'Masculino'])
totalMulheres = len(dadosSenado[dadosSenado.sexo == 'Feminino'])
totalExercicio = len(dadosSenado[dadosSenado.status == 'Exercicio'])
totalMulheresExercicio = dadosSenado.query(
    'sexo == "Feminino" and status == "Exercicio"').count()[0]
totalAfastados = len(dadosSenado[dadosSenado.status == 'Afastado'])
totalGasto = dadosSenado['gastos'].sum()

# Não contabiliza parlamentares que ainda não efetuaram gastos no cálculo de médias
gastoMedioSenadores = dadosSenado.query('gastos != 0')['gastos'].mean()
mediaGastosHomensExercicio = dadosSenado.query(
    'gastos != 0 and sexo == "Masculino" and status == "Exercicio"')['gastos'].mean()
mediaGastosMulheresExercicio = dadosSenado.query(
    'gastos !=0 and sexo == "Feminino" and status == "Exercicio"')['gastos'].mean()


# Imprime algumas informações do senado, pelos dados coletados
print('Há no senado {:d} senadores, distribuidos entre {:d} homens e {:d} mulheres'.format(
    totalSenadores, totalHomens, totalMulheres))
print('As mulheres representam {:.2f}% do total'.format(
    totalMulheres / totalSenadores * 100))
print('Há {:d} senadores em exercício, destes {:d} são mulheres'.format(
    totalExercicio, totalMulheresExercicio))
print('As mulheres representam {:.2f}% deste total'.format(
    totalMulheresExercicio / totalExercicio * 100))
print('O gasto médio de senadores homens em exercício foi de R$ {:.2f}'.format(
    mediaGastosHomensExercicio))
print('O gasto médio de senadores mulheres em exercício foi de R$ {:.2f}'.format(
    mediaGastosMulheresExercicio))
print('O gasto médio dos senadores, em exercício e afastados, foi de R$ {:.2f}'.format(
    gastoMedioSenadores))
print('O montante de despesas parlamentares em {:d} anos foi de R$ {:.2f}, com media anual de R$ {:.2f}'.format(
    len(anos), totalGasto, totalGasto / len(anos)))


# Gera gráficos
if not os.path.exists('imagensV2'):
    os.makedirs('imagensV2')

gSexo = sexo.plot(kind='pie', figsize=(13, 13), fontsize=12,
                  subplots=True, legend=False, colormap='Paired')
gSexo[0].get_figure().savefig('imagensV2/distSexo.png')

gSexoT = sexoT[['Participacao']].plot(kind='pie', figsize=(
    5, 5), subplots=True, legend=False, fontsize=12, colormap='Paired')
gSexoT[0].get_figure().savefig('imagensV2/distSexoT.png')

gEstados = gastoEstados[['gastos', 'gastos2015', 'gastos2016', 'gastos2017']].plot(
    kind='bar', rot=0, title='Gastos por Estado', figsize=(15, 5), legend=True, fontsize=12, colormap='Paired')
gEstados.get_figure().savefig('imagensV2/gastoEstados.png')

gabineteEstados = gastoEstados.sort_values(by=['TotalGabinete-2017'], ascending=False)[['TotalGabinete-2017']].plot(
    kind='bar', title='Tamanho do gabinete em 2017 por unidade da federação', figsize=(10, 10), fontsize=12, legend=False)
gabineteEstados.get_figure().savefig('imagensV2/gastoGabineteEstados-2017.png')

gPartidos = gastoPartidos[['gastos', 'gastos2015', 'gastos2016', 'gastos2017']].plot(
    kind='bar', rot=0, title='Gastos por Partido', figsize=(15, 5), legend=True, fontsize=10, colormap='Paired')
gPartidos.get_figure().savefig('imagensV2/gastoPartidos.png')

gabinetePartidos = gastoPartidos.sort_values(by=['TotalGabinete-2017'], ascending=False)[['TotalGabinete-2017']].plot(
    kind='bar', title='Tamanho do gabinete em 2017 por partido', figsize=(10, 10), fontsize=12, legend=False)
gabinetePartidos.get_figure().savefig('imagensV2/gastoGabinetePartidos-2017.png')

gTop10 = top10[['gastos', 'gastos2015', 'gastos2016', 'gastos2017']].plot(
    kind='bar', rot=20, title='10 maiores gastadores', x=top10['nome'], figsize=(15, 8), legend=True, fontsize=12, colormap='Paired')
gTop10.get_figure().savefig('imagensV2/10maiores.png')
