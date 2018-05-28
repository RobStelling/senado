# coding='utf-8'
# Imports
from bs4 import BeautifulSoup
from matplotlib.ticker import FuncFormatter
import argparse
import csv
import errno
import json
import locale
import matplotlib.pyplot as plt
import operator
import os
import pandas as pd
import re

import rotinas as rtn

"""Lê dados de parlamentares de arquivos CSV e
gera gráficos, texto e páginas com o conteúdo
"""

locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')

parser = argparse.ArgumentParser(
    description='Coleta dados de gastos de Senadores brasileiros.')

parser.add_argument('-G', '--nograph', dest='nograph', action='store_true',
                    help='Não gera gráficos')

parser.add_argument('-P', '--nopage', dest='nopage', action='store_true',
                    help='Não gera a página html')

args = parser.parse_args()

# Lê legislatura e Lista de anos de mandato para contabilização
with open('csv/anos.csv', newline='') as arquivoAnos:
    anosReader = csv.reader(arquivoAnos)
    for row in anosReader:
        # Ignora o header (se houver)
        if rtn.maiorQue(row[0]) and rtn.maiorQue(row[1]) and rtn.maiorQue(row[2]):
            legislaturaAtual = int(row[0])
            anos = list(range(int(row[1]), int(row[2]) + 1))
            # Quarto campo está no formato aaaa-mm-dd hh:mm:ss.dcmm
            # Primeiro separa data de hora
            dataColeta, horaColeta = row[3].split(' ')
            # Muda data coleta de aaaa-mm-dd para dd/mm/aaaa
            dataColeta = dataColeta.split('-')
            dataColeta = dataColeta[2] + '/' + \
                dataColeta[1] + '/' + dataColeta[0]
            # Descarta os décimos de segundo
            horaColeta = horaColeta.split('.')[0]
            break

# Lê créditos das fotos
with open('csv/creditos.csv', newline='') as creditos:
    creditosReader = csv.reader(creditos)
    header = next(creditosReader)
    listaCredito = {}
    for row in creditosReader:
        listaCredito[int(row[0].split('.')[0].replace('senador', ''))] = row[1]

# Lê DataFrames
dadosSenado = pd.read_csv('csv/senado.csv', encoding='utf-8', index_col=0)
top = pd.read_csv('csv/top.csv', encoding='utf-8')
gastoPartidos = pd.read_csv('csv/gastoPartidos.csv',
                            encoding='utf-8', index_col=0)
gastoEstados = pd.read_csv('csv/gastoEstados.csv',
                           encoding='utf-8', index_col=0)
#sexo = pd.read_csv('csv/sexo.csv', encoding='utf-8')
sexo = dadosSenado.rename(columns={'Participacao': '(Sexo, Situação)'}).groupby(
    ['sexo', 'status'])['(Sexo, Situação)'].count()
sexoT = pd.read_csv('csv/sexoT.csv', encoding='utf-8', index_col=0)

# Lê arquivo json
with open('json/gastosSenadores.json', 'r', encoding='utf-8') as entrada:
    gastosSenadores = json.load(entrada)

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
      rtn.reais(mediaGastosHomensExercicio))
print('O gasto médio de senadores mulheres em exercício foi de ' +
      rtn.reais(mediaGastosMulheresExercicio))
print('O gasto médio dos senadores, em exercício e fora de exercício, foi de ' +
      rtn.reais(gastoMedioSenadores))
print('O montante de despesas parlamentares em {:d} anos foi de {}, com media anual de {}\n'.format(
    len(anos), rtn.reais(totalGasto), rtn.reais(totalGasto / len(anos))))

# Totaliza os gastos do senado por tipo de gasto
gastosSenado = {}
for senador in gastosSenadores:
    for gastos in senador['gastos']:
        for caput in gastos['lista']:
            if not caput in gastosSenado:
                gastosSenado[caput] = gastos['lista'][caput]
            else:
                gastosSenado[caput] += gastos['lista'][caput]

for caput in gastosSenado:
    gastosSenado[caput] = round(gastosSenado[caput], 2)

print("Gastos do senado por tema:")
totalizacaoGastosSenado = 0.0
for caput in gastosSenado:
    totalizacaoGastosSenado += gastosSenado[caput]
    print('{}: {}'.format(caput, rtn.reais(round(gastosSenado[caput], 2))))

print('Total de gastos: {}'.format(rtn.reais(round(totalizacaoGastosSenado, 2))))

# Salva arquivo JSON com gastos totalizados
if not os.path.exists('json'):
    os.makedirs('json')

with open('json/gastosSenado.json', 'w', encoding='utf-8') as saida:
    json.dump(gastosSenado, saida, ensure_ascii=False,
              indent=2, separators=(',', ':'))

# Gera página HTML


def geraHTML(modeloHtml, saida):
    """Gera página HTML a partir de um modelo (modeloHtml)
    não retorna nenhum valor
    """
    def totalBeneficioMoradia(senador):
        """Calcula o total do beneficio moradia de um senador
        """
        am = 'Auxílio-Moradia-'
        im = 'Imóvel Funcional-'
        total = 0
        for ano in anos:
            total += senador[am + str(ano)] + senador[im + str(ano)]
        return total

    def htmlRowsSenado(senadores, anoConsulta):
        """Gera string com linhas da tabela html de uma lista de senadores
        na rotina a identação é "hardcoded"... Poderia não haver identação.
        """
        i = 1
        textoMes = {True: "mês", False: "meses"}
        html = ""
        for index, senador in senadores.iterrows():
            html += "{:<12}<tr>\n".format('')
            html += "{:<14}<td>{}</td>\n".format('', i)
            html += "{:<14}<td align='middle'><a href='{}' target='_blank'><img src='fotos/senador{}.jpg' height='51' width='42'><span class='fototip'>Crédito foto: {}</span></a></td>\n".format(
                '', f"http://www6g.senado.leg.br/transparencia/sen/{index}/?ano={anoConsulta}", index, listaCredito[index])
            html += "{:<14}<td align='left'>{}</td>\n".format(
                '', senador['nome'])
            html += "{:<14}<td align='left' class='gastos' name='{}'>{}</td>\n".format(
                '', index, rtn.reais(senador['gastos']))
            html += "{:<14}<td align='left'>{}</td>\n".format(
                '', senador['Participacao'])
            html += "{:<14}<td align='middle'>{}</td>\n".format(
                '', senador['UF'])
            html += "{:<14}<td align='left'>{}</td>\n".format(
                '', senador['partido'])
            html += "{:<14}<td align='right'>{} pessoas</td>\n".format(
                '', senador['TotalGabinete-{}'.format(anos[-1])])
            beneficioMoradia = totalBeneficioMoradia(senador)
            html += "{:<14}<td align='right'>{} {}</td>\n".format(
                '', beneficioMoradia, textoMes[beneficioMoradia == 1])
            html += "{:<12}</tr>\n".format('')
            i += 1
        return html

    def exercicio(_):
        """Lista de senadores em exercício, em ordem alfabética de nome
        """
        return htmlRowsSenado(dadosSenado.query('status == "Exercicio"').sort_values(by='nomeSort'), anos[-1])

    def foraExercicio(_):
        """Lista de senadores fora de exercício, em ordem alfabética de nome
        """
        return htmlRowsSenado(dadosSenado.query('status == "ForaExercicio"').sort_values(by='nomeSort'), anos[-1])

    def caption(mensagem):
        html = "{:<10}<caption>Senadores {} - {}/{}</caption>\n".format(
            '', mensagem, anos[0], anos[-1])
        return html

    def captionExercicio(_):
        return caption("em Exercício")

    def captionForaExercicio(_):
        return caption("fora de Exercício")

    def dataDaColeta(_):
        return dataColeta

    def horaDaColeta(_):
        return horaColeta

    def imagem(imgTxt):
        particao = imgTxt.split('-')
        return '<img src="imagens/{}.png" width="{}%"></img>\n'.format(particao[4], particao[6])

    def tituloLegislatura(_):
        html = '{:<6}<div class="row"><b class="SenadoTitle">BRASIL - {}ª Legislatura</b><br></div>\n'.format(
            '', legislaturaAtual)
        return html

    # Dicionário de padrões a encontrar e função que será chamada para cada padrão
    padrao = {"<!--Exercicio-->": exercicio,
              "<!--Imagem--[A-Za-z0-9]+--[0-9]+-->": imagem,
              "<!--ForaExercicio-->": foraExercicio,
              "<!--CaptionExercicio-->": captionExercicio,
              "<!--Data-->": dataDaColeta,
              "<!--Hora-->": horaDaColeta,
              "<!--CaptionForaExercicio-->": captionForaExercicio,
              "<!--TituloLegislatura-->": tituloLegislatura}

    # Le arquivo de entrada e inclui o texto gerado de acordo com o padrão encontrado
    for linha in modeloHtml:
        # a linha com o marcador de padrão é mantida (se assume que é um comentário html)
        saida.write(linha)
        linhaLimpa = linha.strip()
        for index, p in enumerate(padrao):
            if re.match(p, linhaLimpa):
                saida.write(f"{padrao[p](linhaLimpa)}")

    modeloHtml.close()
    saida.close()

if not args.nopage:
    # Abre os arquivos e gera a página HTML
    try:
        modeloHtml = open("index.tmpl", "r")
        try:
            # Se conseguiu abrir entrada, tenta abrir saída e gerar modelo
            saida = open("index.html", "w")
            geraHTML(modeloHtml, saida)
        except FileNotFoundError:
            # trata erros na abertura do arquivo de saída
            modeloHtml.close()
            print("Erro no nome do arquivo de saída")
        except IOError:
            modeloHtml.close()
            print("Não consigo criar index.html")
    except IOError:
        # Trata erro na abertura do arquivo de entrada
        print("Não consigo abrir index.tmpl")

def tickReais(x, pos=None):
    """Retorna uma string no formato <numero>M para ser usada
    em gráficos
    """
    if x == int(x):
        formato = '%d'
    else:
        formato = '%.1f'
    return locale.format(formato, x, grouping=True) + 'M'



if not args.nograph:
    # Gera gráficos
    imagens = 'imagens'
    if not os.path.exists(imagens):
        os.makedirs(imagens)

    # Ordena os tipos de gasto pelo montante e cria os vetores
    # de título (caput), dados
    gS = sorted(gastosSenado.items(), key=operator.itemgetter(1))
    caput = []
    y = []
    x = []
    i = 0
    for item in gS:
        caput.append(item[0])
        x.append(item[1] / 1000000)
        y.append(i)
        i += 1

    plt.style.use('seaborn-whitegrid')

    fig, ax = plt.subplots()
    ax.barh(y, x, tick_label=caput)
    ax.set(xlabel='Valores em milhões de reais',
           title='Gastos de Senadores por tipo de despesa')
    ax.xaxis.set_major_formatter(FuncFormatter(tickReais))
    fig.savefig(f"{imagens}/gastosSenado.png",
                transparent=False, bbox_inches="tight")
    plt.close()
    gSexo = sexo.plot(kind='pie', figsize=(13, 13), fontsize=12,
                      subplots=True, legend=False, colormap='Paired')
    gSexo[0].get_figure().savefig(f"{imagens}/distSexo.png")
    plt.close()
    gSexoT = sexoT[['Participacao']].plot(kind='pie', figsize=(
        5, 5), subplots=True, legend=False, fontsize=12, colormap='Paired')
    gSexoT[0].get_figure().savefig(f"{imagens}/distSexoT.png")
    plt.close()

    listaGastos = [
        x for x in gastoEstados.columns if re.match(r'gastos[0-9]*$', x)]

    gEstados = gastoEstados[listaGastos].plot(
        kind='bar', rot=0, title='Gastos por unidade da federação', figsize=(15, 5), legend=True, fontsize=12, colormap='Paired')
    gEstados.yaxis.set_major_formatter(FuncFormatter(rtn.reais))
    gEstados.get_figure().savefig(f"{imagens}/gastoEstados.png")
    plt.close()
    gabineteEstados = gastoEstados.sort_values(by=[f'TotalGabinete-{anos[-1]}'], ascending=False)[['TotalGabinete-{}'.format(anos[-1])]].plot(
        kind='bar', title=f'Tamanho do gabinete em {anos[-1]} por unidade da federação', figsize=(10, 10), fontsize=12, legend=False)
    gabineteEstados.get_figure().savefig(
        f"{imagens}/gastoGabineteEstados{anos[-1]}.png")
    plt.close()
    gPartidos = gastoPartidos[listaGastos].plot(
        kind='bar', rot=0, title='Gastos por Partido', figsize=(15, 5), legend=True, fontsize=10, colormap='Paired')
    gPartidos.yaxis.set_major_formatter(FuncFormatter(rtn.reais))
    gPartidos.get_figure().savefig(f"{imagens}/gastoPartidos.png")
    plt.close()
    gabinetePartidos = gastoPartidos.sort_values(by=[f'TotalGabinete-{anos[-1]}'], ascending=False)[[f'TotalGabinete-{anos[-1]}']].plot(
        kind='bar', title=f'Tamanho do gabinete em {anos[-1]} por partido', figsize=(10, 10), fontsize=12, legend=False)
    gabinetePartidos.get_figure().savefig(
        f"{imagens}/gastoGabinetePartidos{anos[-1]}.png")
    plt.close()
    gTop = top[listaGastos].plot(
        kind='bar', rot=20, title='Senadores com maiores gastos na legislatura atual', x=top['nome'], figsize=(18, 8), legend=True, fontsize=12, colormap='Paired')
    gTop.yaxis.set_major_formatter(FuncFormatter(rtn.reais))
    gTop.get_figure().savefig(f"{imagens}/maiores.png")
    plt.close()

    listaBeneficioMoradia = [x for x in gastoEstados.columns if re.match(
        r'(Auxílio-Moradia|Imóvel Funcional)-[0-9]+$', x)]
    beneficioMoradia = 0
    for beneficio in listaBeneficioMoradia:
        beneficioMoradia += gastoEstados[beneficio]
    beneficioMoradia /= len(anos)

    gBeneficio = beneficioMoradia.sort_values(ascending=False).plot(
        kind='bar', title='Média de meses anuais de uso de benefícios de moradia por unidade da federação', figsize=(10, 10), fontsize=(12), legend=False)
    gBeneficio.get_figure().savefig(f"{imagens}/moradiaEstado.png")
    plt.close()
