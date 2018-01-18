#coding='utf-8'
import requests

# Lê dados de parlamentares das páginas de dados abertos do Senado
# Retorna um dicionário com parlamentares atuais e afastados
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

listaParlamentares = leParlamentares()

parlamentares = listaParlamentares['atuais']
parlamentaresAfastados = listaParlamentares['afastados']

# Adiciona dados de parlametares a uma lista
# Não retorna valor algum (a lista de entrada é modificada)
# Se statos não for passado assume que parlamentar está em exercício
def adicionaDados(lista, parlamentar, status='Exercicio'):
    lista.append({'codigo': parlamentar['IdentificacaoParlamentar']['CodigoParlamentar'],
                  'nomeCompleto': parlamentar['IdentificacaoParlamentar']['NomeCompletoParlamentar'],
                  'nome': parlamentar['IdentificacaoParlamentar']['NomeParlamentar'],
                  'email': parlamentar['IdentificacaoParlamentar'].get('EmailParlamentar', ''), # Alguns não tem email
                  'sexo': parlamentar['IdentificacaoParlamentar']['SexoParlamentar'],
                  # Se for falecido não há sigla do partito
                  'partido': parlamentar['IdentificacaoParlamentar'].get('SiglaPartidoParlamentar', ''),
                  'urlFoto': parlamentar['IdentificacaoParlamentar']['UrlFotoParlamentar'],
                  'urlPagina': parlamentar['IdentificacaoParlamentar']['UrlPaginaParlamentar'],
                  # Se for afastado então o campo a adicionar está em Mandato
                  'UF': parlamentar['IdentificacaoParlamentar'].get('UfParlamentar', parlamentar['Mandato']['UfParlamentar']),
                  'Participacao': parlamentar['Mandato']['DescricaoParticipacao'],
                  'status': status})

dados = []
print('Organizando informações de parlamentares...')
for senador in parlamentares:
    #print(senador['IdentificacaoParlamentar']['NomeCompletoParlamentar'])
    adicionaDados(dados, senador, 'Exercicio')

for senador in parlamentaresAfastados:
    #print(senador['IdentificacaoParlamentar']['NomeCompletoParlamentar'])
    adicionaDados(dados, senador, 'Afastado')
print('Fim de organização de operações...')
#dados = sorted(dados, key=lambda k: k['nome'])

from bs4 import BeautifulSoup

# Retira '.' e substitui ',' por '.' e converte para float
def s2float(dado):
    return float(dado.replace('.', '').replace(',', '.'))

# Retorna o total de gastos de um parlamentar, pelo seu código
# em um ano determinado
# Consulta as páginas de transparência do senado para efetuar a operação
def totalGastos(codigoSenador, ano=2017):
    #print(codigoSenador, ano)
    print('.', end='')
    requisicao = requests.get(f"http://www6g.senado.leg.br/transparencia/sen/{codigoSenador}/?ano={ano}")
    sopaSenador = BeautifulSoup(requisicao.content, 'html.parser')
    bloco = sopaSenador.find('div', {'class':'sen-conteudo-interno'})
    valores = bloco.find_all('tfoot')
    # Extrai apenas o valor em string (strip().split()[1])
    # e converte para float
    for i in range(0, len(valores)):
        valores[i] = s2float(valores[i].text.strip().split()[1])

    heading = bloco.find_all('a', {'class':'accordion-toggle'})
    for i in range(0, len(heading)):
        heading[i] = heading[i].text.strip()

    total = 0
    for i in range(0, len(valores)):
        #print(f"{heading[i]}: {valores[i]}")
        total += valores[i]
    #print(f"Total de gastos: {total}")
    return total

print('Recuperando informações de gastos parlamentares...')
for senador in range(0, len(dados)):
    dados[senador]['gastos'] = 0
    for ano in anos:
        dados[senador][f'gastos{ano}'] = totalGastos(dados[senador]['codigo'], ano)
        dados[senador]['gastos'] += dados[senador][f'gastos{ano}']

print('\nFim de recuperação de informações de gastos parlamentares...')

import pandas as pd

# Cria DataFrame dos dados do senado
dadosSenado = pd.DataFrame(dados)

# Exclui quem tem gastos == 0 e status == "Afastado"
dadosSenado = dadosSenado.query('gastos != 0 or status != "Afastado"')

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
gastosPartidos = dadosSenado.groupby('partido').sum().sort_values(by=['gastos'], ascending=[False])
sexo = dadosSenado.groupby(['sexo', 'status']).count()
sexoT = dadosSenado[['Participacao', 'sexo']].groupby(['sexo']).count()

print("Há no senado {:d} senadores, distribuidos entre {:d} homens e {:d} mulheres".format(totalSenadores, totalHomens, totalMulheres))
print("As mulheres representam {:.2f}% do total".format(totalMulheres/totalSenadores*100))
print("Há {:d} senadores em exercício, destes {:d} são mulheres".format(totalExercicio, totalMulheresExercicio))
print("As mulheres representam {:.2f}% deste total".format(totalMulheresExercicio/totalExercicio*100))
print("O gasto médio de senadores homens em exercício foi de R$ {:.2f}".format(mediaGastosHomensExercicio))
print("O gasto médio de senadores mulheres em exercício foi de R$ {:.2f}".format(mediaGastosMulheresExercicio))
print("O gasto médio dos senadores, em exercício e afastados, foi de R$ {:.2f}".format(gastoMedioSenadores))
print("O montante de despesas parlamentares em 3 anos foi de R$ {:.2f}, com media anual de R$ {:.2f}".format(totalGasto, totalGasto/3))

# Gera gráficos
gEstados = gastoEstados[['gastos', 'gastos2015', 'gastos2016', 'gastos2017']].plot(kind='bar', rot = 0, title ="Gastos por Estado", figsize=(15,5), legend=True, fontsize=12, colormap="Paired")
gEstados.get_figure().savefig('gastoEstados.png')
gPartidos=gastosPartidos[['gastos', 'gastos2015', 'gastos2016', 'gastos2017']].plot(kind='bar', rot = 0,title ="Gastos por Partido", figsize=(15,5), legend=True, fontsize=10, colormap="Paired")
gPartidos.get_figure().savefig('gastoPartidos.png')
gSexo = sexo[['Participacao']].plot(kind='pie', figsize=(5,5), subplots=True, legend=False, fontsize=12, colormap="Paired")
gSexo[0].get_figure().savefig('distSexo.png')
gSexoT = sexoT[['Participacao']].plot(kind='pie', figsize=(5,5), subplots=True, legend=False, fontsize=12, colormap="Paired")
gSexoT[0].get_figure().savefig('distSexoT.png')
gTop10 = top10[['gastos', 'gastos2015', 'gastos2016', 'gastos2017']].plot(kind='bar', rot=20, title ="10 maiores gastadores", x = top10['nome'], figsize=(15,8), legend=True, fontsize=12, colormap="Paired")
gTop10.get_figure().savefig('10maiores.png')