# coding='utf-8'
# Imports
from bs4 import BeautifulSoup
import errno
import locale
import matplotlib.pyplot as plt
import os
import pandas as pd

"""Lê dados de parlamentares de arquivos CSV e
gera gráficos, texto e páginas com o conteúdo
"""

locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')

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

# Calcula dados importantes
totalSenadores = len(dadosSenado)
totalHomens = len(dadosSenado[dadosSenado.sexo == 'Masculino'])
totalMulheres = len(dadosSenado[dadosSenado.sexo == 'Feminino'])
totalExercicio = len(dadosSenado[dadosSenado.status == 'Exercicio'])
totalMulheresExercicio = dadosSenado.query(
    'sexo == "Feminino" and status == "Exercicio"').count()[0]
totalForaExercicio = len(dadosSenado[dadosSenado.status == 'ForaExercicio'])
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
print('As mulheres representam ' + locale.format('%.2f',
                                                 totalMulheres / totalSenadores * 100) + '% do total')
print('Há {:d} senadores em exercício, destes {:d} são mulheres'.format(
    totalExercicio, totalMulheresExercicio))
print('As mulheres representam ' + locale.format('%.2f',
                                                 totalMulheresExercicio / totalExercicio * 100) + '% deste total')
print('O gasto médio de senadores homens em exercício foi de R$ ' +
      locale.format('%.2f', mediaGastosHomensExercicio, grouping=True))
print('O gasto médio de senadores mulheres em exercício foi de R$ ' +
      locale.format('%.2f', mediaGastosMulheresExercicio, grouping=True))
print('O gasto médio dos senadores, em exercício e fora de exercício, foi de R$ ' +
      locale.format('%.2f', gastoMedioSenadores, grouping=True))
print('O montante de despesas parlamentares em {:d} anos foi de R$ '.format(len(anos)) + locale.format(
    '%.2f', totalGasto, grouping=True) + ', com media anual de R$ ' + locale.format('%.2f', totalGasto / len(anos), grouping=True))

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

beneficioMoradia = (gastoEstados['Auxílio-Moradia-2015'] + gastoEstados['Auxílio-Moradia-2016'] + gastoEstados['Auxílio-Moradia-2017'] + \
    gastoEstados['Imóvel Funcional-2015'] + \
    gastoEstados['Imóvel Funcional-2016'] + \
    gastoEstados['Imóvel Funcional-2017']) / len(anos)
gBeneficio = beneficioMoradia.sort_values(ascending=False).plot(
    kind='bar', title='Média de meses anuais de uso de benefícios de moradia por unidade da federação', figsize=(10, 10), fontsize=(12), legend=False)
gBeneficio.get_figure().savefig('imagensV2/moradiaEstado.png')