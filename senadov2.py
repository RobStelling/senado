# coding='utf-8'
# Imports
import requests
import errno
from bs4 import BeautifulSoup
import pandas as pd
import os
import matplotlib.pyplot as plt


def leParlamentares():
    """Lê dados de parlamentares das páginas de dados abertos do Senado
    Retorna um dicionário com parlamentares atuais e afastados
    Documentação da API do Senado Federal:
    http://legis.senado.leg.br/dadosabertos/docs/resource_ListaSenadorService.html
    """
    print('Lendo dados de parlamentares...')
    # Abre uma sessão e define que aceita json
    sessao = requests.Session()
    sessao.headers.update({'Accept': 'application/json'})

    # Recupera lista de senadores atuais
    atual = sessao.get(
        'http://legis.senado.leg.br/dadosabertos/senador/lista/atual')
    # Recupera lista de senadores afastados
    afastados = sessao.get(
        'http://legis.senado.leg.br/dadosabertos/senador/lista/afastados')

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


def adicionaDados(lista, parlamentar, status='Exercicio'):
    """Adiciona dados de parlametares, com os campos escolhidos, a uma lista
    Não retorna valor (a lista de entrada é modificada)
    Se status não for passado assume que parlamentar está em exercício
    """
    lista.append({'codigo': parlamentar['IdentificacaoParlamentar']['CodigoParlamentar'],
                  'nomeCompleto': parlamentar['IdentificacaoParlamentar']['NomeCompletoParlamentar'],
                  'nome': parlamentar['IdentificacaoParlamentar']['NomeParlamentar'],
                  # Alguns não tem email
                  'email': parlamentar['IdentificacaoParlamentar'].get('EmailParlamentar', ''),
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
# Adiciona informações dos parlamentares em exercício e afastados
# à lista 'dados'
for senador in parlamentares:
    adicionaDados(dados, senador, status='Exercicio')

for senador in parlamentaresAfastados:
    adicionaDados(dados, senador, status='Afastado')
print('Fim de organização de operações...')

#dados = sorted(dados, key=lambda k: k['nome'])

def s2float(dado):
    """ Converte uma string numérica no formato brasileiro para float """
    # Retira '.' e substitui ',' por '.' e converte para float
    return float(dado.replace('.', '').replace(',', '.'))

def infoSenador(codigoSenador, ano=2017):
    """Coleta informações de um ano de legislatura de um senador pelo seu código
    Retorna um dicionário com o total de gastos (escalar) de um parlamentar e
    informações de utilização de pessoal (dicionario).
    Consulta as páginas de transparência do senado para efetuar a operação
    Página exemplo: Senador Itamar Franco, 2011
    http://www6g.senado.leg.br/transparencia/sen/1754/?ano=2011
    """
    print('.', end='', flush=True)            # Indicador de atividade

    # Coleta a página
    requisicao = requests.get(
        f'http://www6g.senado.leg.br/transparencia/sen/{codigoSenador}/?ano={ano}')

    # E gera a sopa
    sopaSenador = BeautifulSoup(requisicao.content, 'html.parser')

    # Seleciona a área onde estão os dados desejados
    bloco = sopaSenador.find('div', {'class': 'sen-conteudo-interno'})

    # Recupera dados de pessoal
    # bloco->div(#accordion-pessoal)->tbody->ALL tr(.sen_tabela_linha_grupo)
    quantidades = bloco.find('div', {'id': 'accordion-pessoal'}).find(
        'tbody').find_all('tr', {'class': 'sen_tabela_linha_grupo'})
    infoPessoal = {}

    # Texto está no elemento <span> e valores no elemento <a>
    for i in range(0, len(quantidades)):
        infoPessoal[quantidades[i].find('span').text.strip()] = int(
            quantidades[i].find('a').text.strip().split()[0])

    # Os totais de gastos estão nos dois rodapés das páginas
    valores = bloco.find_all('tfoot')

    # Extrai apenas o valor em string (strip().split()[1])
    # e converte para float (s2float)
    for i in range(0, len(valores)):
        valores[i] = s2float(valores[i].text.strip().split()[1])

    # Recupera o heading - Não é necessário nesta versão
    # Mas deverá ser no futuro
    #heading = bloco.find_all('a', {'class':'accordion-toggle'})
    # for i in range(0, len(heading)):
    #    heading[i] = heading[i].text.strip()

    # Contabiliza o total de gastos
    total = 0
    for i in range(0, len(valores)):
        total += valores[i]

    # Retorna o gasto total do senador para o ano pedido
    return {'total': total, 'pessoal': infoPessoal}


print('Recuperando informações de gastos parlamentares...')

# Para cada senador coleta os gastos de cada ano da legislatura
# e soma os gastos em 'gastos'
for senador in range(0, len(dados)):
    dados[senador]['gastos'] = 0
    # Para cada ano, recupera as informações do senador
    # Guarda o total daquele ano (gastos{ano}) e soma no total
    # de gastos (gastos).
    # Cria uma coluna para cada tipo de uso de
    # pessoal (info['pessoal'].keys())
    for ano in anos:
        info = infoSenador(dados[senador]['codigo'], ano=ano)
        dados[senador][f'gastos{ano}'] = info['total']
        dados[senador]['gastos'] += dados[senador][f'gastos{ano}']
        for key in info['pessoal'].keys():
            dados[senador][f'{key}-{ano}'] = info['pessoal'][key]

print('\nFim de recuperação de informações de gastos parlamentares...')


# Cria DataFrame dos dados do senado
dadosSenado = pd.DataFrame(dados)

# Exclui quem tem gastos == 0 e status == 'Afastado'
dadosSenado = dadosSenado.query('gastos != 0 or status != "Afastado"')

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
# 10 maiores gastadores
top10 = dadosSenado.sort_values(by=['gastos'], ascending=[False]).head(10)

# Dataframes de gastos por estado e por partidos
gastoEstados = dadosSenado.groupby('UF').sum().sort_values(by=[
    'gastos'], ascending=[False])
gastoPartidos = dadosSenado.groupby('partido').sum(
).sort_values(by=['gastos'], ascending=[False])
sexo = dadosSenado.rename(columns={'Participacao': '(Sexo, Situação)'}).groupby(
    ['sexo', 'status'])['(Sexo, Situação)'].count()
sexoT = dadosSenado[['Participacao', 'sexo']].groupby(['sexo']).count()

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

# Salva arquivos
if not os.path.exists('csv'):
    os.makedirs('csv')

dadosSenado.to_csv('csv/senado.csv', na_rep='', header=True, index=False,
                   mode='w', encoding='utf-8', line_terminator='\n', decimal='.')
top10.to_csv('csv/top10.csv', na_rep='', header=True, index=False,
             mode='w', encoding='utf-8', line_terminator='\n', decimal='.')
gastoPartidos.to_csv('csv/gastoPartidos.csv', na_rep='', header=True,
                     index=True, mode='w', encoding='utf-8', line_terminator='\n', decimal='.')
gastoEstados.to_csv('csv/gastoEstados.csv', na_rep='', header=True, index=True,
                    mode='w', encoding='utf-8', line_terminator='\n', decimal='.')
sexo.to_csv('csv/sexo.csv', index=True, na_rep='', header=True,
            index_label=None, mode='w', encoding='utf-8', decimal='.')
sexoT.to_csv('csv/sexoT.csv', index=True, na_rep='', header=True,
             index_label=None, mode='w', encoding='utf-8', decimal='.')


# Gera gráficos
if not os.path.exists('imagensV2'):
    os.makedirs('imagensV2')

gEstados = gastoEstados[['gastos', 'gastos2015', 'gastos2016', 'gastos2017']].plot(
    kind='bar', rot=0, title='Gastos por Estado', figsize=(15, 5), legend=True, fontsize=12, colormap='Paired')
gEstados.get_figure().savefig('imagensV2/gastoEstados.png')
gPartidos = gastoPartidos[['gastos', 'gastos2015', 'gastos2016', 'gastos2017']].plot(
    kind='bar', rot=0, title='Gastos por Partido', figsize=(15, 5), legend=True, fontsize=10, colormap='Paired')
gPartidos.get_figure().savefig('imagensV2/gastoPartidos.png')
gSexo = sexo.plot(kind='pie', figsize=(12, 12), fontsize=12,
                  subplots=True, legend=False, colormap='Paired')
gSexo[0].get_figure().savefig('imagensV2/distSexo.png')
gSexoT = sexoT[['Participacao']].plot(kind='pie', figsize=(
    5, 5), subplots=True, legend=False, fontsize=12, colormap='Paired')
gSexoT[0].get_figure().savefig('imagensV2/distSexoT.png')
gTop10 = top10[['gastos', 'gastos2015', 'gastos2016', 'gastos2017']].plot(
    kind='bar', rot=20, title='10 maiores gastadores', x=top10['nome'], figsize=(15, 8), legend=True, fontsize=12, colormap='Paired')
gTop10.get_figure().savefig('imagensV2/10maiores.png')
