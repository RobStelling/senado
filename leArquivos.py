# coding='utf-8'
# Imports
from bs4 import BeautifulSoup
from matplotlib.ticker import FuncFormatter
import csv
import errno
import locale
import matplotlib.pyplot as plt
import os
import pandas as pd

"""Lê dados de parlamentares de arquivos CSV e
gera gráficos, texto e páginas com o conteúdo
"""

locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')

def reais(x, pos=None):
    """Retorna o valor formatado em reais, o parâmetro pos é necessário
    apenas quando a função é chamada pelo FuncFormatter do matplotlib.ticker
    """
    return 'R$ ' + locale.format('%.2f', x, grouping=True)

def maiorQue(numero, menor=0):
    """Retorna True se numero é um inteiro maior que 0
    False caso contrário. O valor mínimo de referência 
    pode ser alterado passando menor=<novoValor>
    numero pode ser string ou qualquer outro tipo aceito
    por int() 
    """
    try:
        valor = int(str(numero))
        return valor > menor
    except ValueError:
        return False

# Lista de anos de mandato para contabilização
with open('csv/anos.csv', newline='') as arquivoAnos:
    anosReader = csv.reader(arquivoAnos)
    for row in anosReader:
        # Ignora o header (se houver)
        if maiorQue(row[0]) and maiorQue(row[1]):
            anos = list(range(int(row[0]), int(row[1])+1))
            break

# Lê créditos das fotos
# Ao fim, listaCredito[codigo] = credito para senador[codigo]
with open('csv/creditos.csv', newline='') as creditos:
    creditosReader = csv.reader(creditos)
    header = next(creditosReader)
    listaCredito = {}
    for row in creditosReader:
        listaCredito[int(row[0].split('.')[0].replace('senador', ''))] = row[1]

dadosSenado = pd.read_csv('csv/senado.csv', encoding='utf-8')
top = pd.read_csv('csv/top.csv', encoding='utf-8')
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
print('O gasto médio de senadores homens em exercício foi de ' +
      reais(mediaGastosHomensExercicio))
print('O gasto médio de senadores mulheres em exercício foi de ' +
      reais(mediaGastosMulheresExercicio))
print('O gasto médio dos senadores, em exercício e fora de exercício, foi de ' +
      reais(gastoMedioSenadores))
print('O montante de despesas parlamentares em {:d} anos foi de '.format(len(anos)) + reais(
    totalGasto) + ', com media anual de ' + reais(totalGasto / len(anos)))

# Gera gráficos
imagens = 'imagensV2'
if not os.path.exists(imagens):
    os.makedirs(imagens)

plt.style.use('seaborn-whitegrid')

gSexo = sexo.plot(kind='pie', figsize=(13, 13), fontsize=12,
                  subplots=True, legend=False, colormap='Paired')
gSexo[0].get_figure().savefig(f"{imagens}/distSexo.png")

gSexoT = sexoT[['Participacao']].plot(kind='pie', figsize=(
    5, 5), subplots=True, legend=False, fontsize=12, colormap='Paired')
gSexoT[0].get_figure().savefig(f"{imagens}/distSexoT.png")

gEstados = gastoEstados[['gastos', 'gastos2015', 'gastos2016', 'gastos2017']].plot(
    kind='bar', rot=0, title='Gastos por unidade da federação', figsize=(15, 5), legend=True, fontsize=12, colormap='Paired')
gEstados.yaxis.set_major_formatter(FuncFormatter(reais))
gEstados.get_figure().savefig(f"{imagens}/gastoEstados.png")

gabineteEstados = gastoEstados.sort_values(by=['TotalGabinete-2017'], ascending=False)[['TotalGabinete-2017']].plot(
    kind='bar', title='Tamanho do gabinete em 2017 por unidade da federação', figsize=(10, 10), fontsize=12, legend=False)
gabineteEstados.get_figure().savefig(f"{imagens}/gastoGabineteEstados-2017.png")

gPartidos = gastoPartidos[['gastos', 'gastos2015', 'gastos2016', 'gastos2017']].plot(
    kind='bar', rot=0, title='Gastos por Partido', figsize=(15, 5), legend=True, fontsize=10, colormap='Paired')
gPartidos.yaxis.set_major_formatter(FuncFormatter(reais))
gPartidos.get_figure().savefig(f"{imagens}/gastoPartidos.png")

gabinetePartidos = gastoPartidos.sort_values(by=['TotalGabinete-2017'], ascending=False)[['TotalGabinete-2017']].plot(
    kind='bar', title='Tamanho do gabinete em 2017 por partido', figsize=(10, 10), fontsize=12, legend=False)
gabinetePartidos.get_figure().savefig(f"{imagens}/gastoGabinetePartidos-2017.png")

gTop = top[['gastos', 'gastos2015', 'gastos2016', 'gastos2017']].plot(
    kind='bar', rot=20, title='Senadores com maiores gastos', x=top['nome'], figsize=(18, 8), legend=True, fontsize=12, colormap='Paired')
gTop.yaxis.set_major_formatter(FuncFormatter(reais))
gTop.get_figure().savefig(f"{imagens}/maiores.png")

beneficioMoradia = (gastoEstados['Auxílio-Moradia-2015'] + gastoEstados['Auxílio-Moradia-2016'] + gastoEstados['Auxílio-Moradia-2017'] + \
    gastoEstados['Imóvel Funcional-2015'] + \
    gastoEstados['Imóvel Funcional-2016'] + \
    gastoEstados['Imóvel Funcional-2017']) / len(anos)
gBeneficio = beneficioMoradia.sort_values(ascending=False).plot(
    kind='bar', title='Média de meses anuais de uso de benefícios de moradia por unidade da federação', figsize=(10, 10), fontsize=(12), legend=False)
gBeneficio.get_figure().savefig(f"{imagens}/moradiaEstado.png")