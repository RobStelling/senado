# coding='utf-8'
# Imports
from bs4 import BeautifulSoup
from datetime import datetime
import errno
import matplotlib.pyplot as plt
import os
import pandas as pd
import re
import requests
import time

""" Versão da aplicação, baseado em https://semver.org
Dado um número de versão MAJOR.MINOR.PATCH, incremente:

MAJOR quando são feitas mudanças de API incompatíveis,
MINOR quando se acrescenta funcionalidade de uma maneira compatível com versões existentes, e
PATCH quando se corrige erros de forma compatível com versões anteriores.

Rótulos adicoinais, para pre-release e metadados de bluid estão disponíveis em extensões do formato
MAJOR.MINOR.PATCH.

MAJOR = 0 indica que o estado atual é de desenvolvimento inicial, qualquer funcionalidade pode mudar.
"""
versao = '0.2.14'

def leParlamentares(legislatura=55):
    """Lê dados de parlamentares das páginas de dados abertos do Senado
    Retorna um dicionário com parlamentares ativos e inativos
    Documentação da API do Senado Federal:
    http://legis.senado.leg.br/dadosabertos/docs/resource_ListaSenadorService.html
    """

    def ativo(parlamentar, data):
        """Verifica se um parlamentar está ativo no momento
        """

        # Teoricamente pode haver múltiplas legislaturas de um mandato
        # mas nos exemplos encontrados só vimos casos até segunda.
        ordemLegislatura = ['Primeira', 'Segunda', 'Terceira', 'Quarta', 'Quinta', 'Sexta', 'Setima', 'Oitava', 'Nona']
        for ordinal in ordemLegislatura:
            # Se não encontrou legislatura então não é senador atual
            if parlamentar['Mandatos']['Mandato'].get(f"{ordinal}LegislaturaDoMandato", '') == '':
                return False
            ordemLegislatura = parlamentar['Mandatos']['Mandato'][f"{ordinal}LegislaturaDoMandato"]
            inicio =  [int(x) for x in ordemLegislatura['DataInicio'].split('-')]
            fim = [int(x) for x in ordemLegislatura['DataFim'].split('-')]
            dataInicio = datetime(inicio[0], inicio[1], inicio[2])
            dataFim = datetime(fim[0], fim[1], fim[2])
            # Se o mandato é atual (inicio < data < fim)
            if dataInicio < data < dataFim:
                # Recupera os exercícios
                exercicios = parlamentar['Mandatos']['Mandato']['Exercicios']['Exercicio']
                # Se houve só um exercício o JSON retorna um dicionário, que convertemos para lista
                if not isinstance(exercicios, list):
                    exercicios = [exercicios]
                # Se entre os exercícios há um sem DataFim, então é ativo
                for ex in exercicios:
                    if ex.get('DataFim', '') == '':
                        return True
        return False

    # Define no header que aceita JSON
    # Resposta padrão da API é XML
    header = {'Accept': 'application/json', 'user-agent': f"senadoInfo/{versao}"}
    url = f"http://legis.senado.leg.br/dadosabertos/senador/lista/legislatura/{legislatura}"

    try:
        senadores = requests.get(url, headers=header)
    except requests.exceptions.RequestException as erro:
        print(erro)
        sys.exit(1)

    listaSenadores = senadores.json()
    parlamentares = listaSenadores['ListaParlamentarLegislatura']['Parlamentares']['Parlamentar']
    """
    A lista de senadores retornada pela consulta inclui 3 senadores com legislatura suspensa pelo
    STF antes da legislatura atual:
    - Gilvan Borges: Mandato da 54 legislatura suspenso pelo STF (volta de João Capiberibe)
    - Marinor Brito: Mandato da 54 legislatura suspenso pelo STF (volta de Jader Barbalho)
    - Wilson Santiago: Mandato da 54 legislatura suspenso pelo STF
    AP,30,gilvamborges@senador.leg.br,Gilvam Borges,Gilvam Pinheiro Borges,PMDB,Masculino
    PA,4998,marinorbrito@senadora.leg.br,Marinor Brito,Marinor Jorge Brito,PSOL,Feminino
    PB,3811,wilson.santiago@senador.leg.br,Wilson Santiago,José Wilson Santiago,PMDB,Masculino
    Os parlamentares acima não aparecem nas listas de Vacantes do Senado, os senadores abaixo também
    não foram eleitos na legislatura atual mas aparecem na lista de vacantes do senado:
    Demóstenes Torres, que teve seu mandato cassado pelo Senado por quebra de decoro parlamentar:
    - Demóstenes Torres:
    GO,3399,demostenes.torres@senador.leg.br,Demóstenes Torres,Demóstenes Lazaro Xavier Torres,S/Partido,Masculino
    2 senadores que faleceram antes da legislatura atual
    - Itamar Franco: 02/07/2011
    - João Ribeiro: 18/12/2013
    MG,1754,itamar.franco@senador.leg.br,Itamar Franco,Itamar Augusto Cautiero Franco,,Masculino
    TO,916,joaoribeiro@senador.leg.br,João Ribeiro,João Batista de Jesus Ribeiro,PR,Masculino
    E os que renunciaram em legislatura anterior:
    - Vital do Rego
    - Wellington Dias
    PB,4645,vital.rego@senador.leg.br,Vital do Rêgo,Vital do Rêgo Filho,PMDB,Masculino
    PI,5016,wellington.dias@senador.leg.br,Wellington Dias,José Wellington Barroso de Araujo Dias,PT,Masculino
    Os dados destes senadores não serão incluídos nos cálculos de estatísticas
    """
    listaNegada = ["Demóstenes Torres", "Gilvam Borges", "Itamar Franco", "João Ribeiro", "Marinor Brito", "Vital do Rêgo", "Wellington Dias", "Wilson Santiago"]
    i = 0
    # Retira da lista os parlamentares que nunca exerceram mandato
    while i < len(parlamentares):
        if parlamentares[i]['Mandatos']['Mandato'].get('Exercicios', '') == '':
            parlamentares.pop(i)
        elif parlamentares[i]['IdentificacaoParlamentar']['NomeParlamentar'] in listaNegada:
            listaNegada.remove(parlamentares[i]['IdentificacaoParlamentar']['NomeParlamentar'])
            parlamentares.pop(i)
        else:
            i = i + 1

    parlamentaresAtuais = []
    parlamentaresForaExercicio = []

    agora = datetime.now()
    for parlamentar in parlamentares:
        if ativo(parlamentar, agora):
            parlamentaresAtuais.append(parlamentar)
        else:
            parlamentaresForaExercicio.append(parlamentar)

    return {'atuais': parlamentaresAtuais, 'foraExercicio': parlamentaresForaExercicio}

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
                  'UF': parlamentar['IdentificacaoParlamentar'].get('UfParlamentar', parlamentar['Mandatos']['Mandato']['UfParlamentar']),
                  'Participacao': parlamentar['Mandatos']['Mandato']['DescricaoParticipacao'],
                  'status': status})


def s2float(dado):
    """ Converte uma string numérica no formato brasileiro para float """
    # Retira '.' e substitui ',' por '.' e converte para float
    return float(dado.replace('.', '').replace(',', '.'))


def infoSenador(codigoSenador, ano=2017, intervalo=0):
    """Coleta informações de um ano de legislatura de um senador pelo seu código
    Retorna um dicionário com o total de gastos (escalar) de um parlamentar e
    uma lista de dicionário com informações de utilização de pessoal.
    Consulta as páginas de transparência do senado para efetuar a operação,
    se definido, espera "intervalo" segundos antes de fazer a requisição
    Página exemplo: Senador Itamar Franco, 2011
    http://www6g.senado.leg.br/transparencia/sen/1754/?ano=2011
    """
    print('.', end='', flush=True)            # Indicador de atividade
    # Espera, em segundos, antes de carregar a página
    time.sleep(intervalo)

    header = {'user-agent': f"senadoInfo/{versao}"}
    # Coleta a página
    url = f"http://www6g.senado.leg.br/transparencia/sen/{codigoSenador}/?ano={ano}"

    try:
        requisicao = requests.get(url, headers=header)
    except requests.exceptions.RequestException as erro:
        print(erro)
        sys.exit(1)

    # Se houve um redirect então a página sobre aquele ano não existe
    if requisicao.history:
        return {'total': 0, 'auxilio': [], 'pessoal': []}

    # E gera a sopa
    sopaSenador = BeautifulSoup(requisicao.content, 'html.parser')

    # Seleciona a área onde estão os dados desejados
    bloco = sopaSenador.find('div', {'class': 'sen-conteudo-interno'})

    # Primeiro computa o total de gastos do senador
    # Os totais de gastos estão nos dois rodapés das tabelas
    valores = bloco.find_all('tfoot')

    # Extrai apenas o valor em string (strip().split()[1]),
    # converte para float (s2float) e contabiliza o total
    total = 0
    for i in range(len(valores)):
        valores[i] = s2float(valores[i].text.strip().split()[1])
        total += valores[i]

    # Depois recupera utilização de auxílio-moradia e imóvel funcional
    # Auxílios estão em #accordion-outros
    outros = bloco.find('div', {'id': 'accordion-outros'})
    # e os dados estão em td's
    tdOutros = outros.find_all('td')

    infoAuxilio = []
    # Se tudo estiver correto, no td[i] teremos o nome do auxício
    # e no td[i+1] sua utilização em meses
    for i in range(0, len(tdOutros), 2):
        auxilio = tdOutros[i].text.strip()
        uso = tdOutros[i + 1].text.strip()
        # Uso pode ser "Não utilizou", "Informações disponíveis depois..." ou
        # "Utilizou (X) meses" ou "Utilizou (1) mês", calcula o uso em meses
        # em função destes valores
        meses = 0
        if (uso != 'Não utilizou'):
            if not re.match(r'Informações disponíveis.*', uso):
                meses = int(uso.replace('Utilizou (', '').replace(
                    ' meses)', '').replace(' mês)', ''))

        infoAuxilio.append({'beneficio': auxilio, 'meses': meses})

    # Ao fim, recupera as informações de uso de pessoal

    # Recupera dados de pessoal
    # bloco->div(#accordion-pessoal)->tbody->ALL tr(.sen_tabela_linha_grupo)
    quantidades = bloco.find('div', {'id': 'accordion-pessoal'}).find(
        'tbody').find_all('tr', {'class': 'sen_tabela_linha_grupo'})

    infoPessoal = []

    # O título da utilização de pessoal está no elemento <span> e quantidades no elemento <a>
    for i in range(len(quantidades)):
        infoPessoal.append(
            {'titulo': quantidades[i].find('span').text.strip(),
             'valor': int(quantidades[i].find('a').text.strip().split()[0])})

    # Retorna o gasto total do senador para o ano pedido
    return {'total': total, 'auxilio': infoAuxilio, 'pessoal': infoPessoal}

def recuperaLegislaturaAtual():
    url = "https://www25.senado.leg.br/web/senadores/em-exercicio"
    header = {'user-agent': f"senadoInfo/{versao}"}
    try:
        requisicao = requests.get(url, headers=header)
    except requests.exceptions.RequestException as erro:
        print(erro)
        sys.exit(1)
    sopa = BeautifulSoup(requisicao.content, 'html.parser')
    textoLegislatura = sopa.find('h2').text.strip()
    # Exemplo de texto:
    # 55ª Legislatura (2015 - 2019)
    numeroLegislatura = int(textoLegislatura.split('ª')[0])
    return numeroLegislatura

# Lista de anos de mandato para contabilização
anos = [2015, 2016, 2017]

legislaturaAtual = recuperaLegislaturaAtual()

print('Lendo dados de parlamentares da legislatura {}...'.format(legislaturaAtual))
listaParlamentares = leParlamentares(legislaturaAtual)
print('Fim de leitura...')

parlamentares = listaParlamentares['atuais']
parlamentaresForaExercicio = listaParlamentares['foraExercicio']


dados = []
print('Organizando informações de parlamentares...')
# Adiciona informações dos parlamentares em exercício e fora de exercício
# à lista 'dados'
for senador in parlamentares:
    adicionaDados(dados, senador, status='Exercicio')

for senador in parlamentaresForaExercicio:
    adicionaDados(dados, senador, status='ForaExercicio')

print('Fim de organização de informações...')

print('Recuperando informações de gastos parlamentares...')

# Para cada senador coleta os gastos de cada ano da legislatura
# e soma os gastos em 'gastos'
for senador in range(len(dados)):
    dados[senador]['gastos'] = 0
    # Para cada ano, recupera as informações do senador
    # Guarda o total daquele ano (gastos{ano}) e soma no total
    # de gastos (gastos).
    # Cria uma coluna para cada tipo de uso de
    # pessoal (info['pessoal'].keys())
    for ano in anos:
        info = infoSenador(dados[senador]['codigo'], ano=ano, intervalo=0.5)
        dados[senador][f"gastos{ano}"] = info['total']
        dados[senador]['gastos'] += dados[senador][f"gastos{ano}"]
        dados[senador][f"TotalGabinete-{ano}"] = 0
        for tipo in range(len(info['pessoal'])):
            coluna = f"{info['pessoal'][tipo]['titulo']}-{ano}"
            valor = info['pessoal'][tipo]['valor']
            dados[senador][coluna] = valor
            dados[senador][f"TotalGabinete-{ano}"] += valor
        for beneficio in range(len(info['auxilio'])):
            coluna = f"{info['auxilio'][beneficio]['beneficio']}-{ano}"
            valor = info['auxilio'][beneficio]['meses']
            dados[senador][coluna] = valor

print('\nFim de recuperação de informações de gastos parlamentares...')


# Cria DataFrame dos dados do senado
dadosSenado = pd.DataFrame(dados)

# Exclui quem tem gastos == 0 e status == 'Afastado'
#dadosSenado = dadosSenado.query('gastos != 0 or status != "Afastado"')

# Calcula dados importantes
totalSenadores = len(dadosSenado)
totalHomens = len(dadosSenado[dadosSenado.sexo == 'Masculino'])
totalMulheres = len(dadosSenado[dadosSenado.sexo == 'Feminino'])
totalExercicio = len(dadosSenado[dadosSenado.status == 'Exercicio'])
totalMulheresExercicio = dadosSenado.query(
    'sexo == "Feminino" and status == "Exercicio"').count()[0]
totalforaExercicio = len(dadosSenado[dadosSenado.status == 'ForaExercicio'])
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
print('O gasto médio dos senadores, em exercício e fora de exercício, foi de R$ {:.2f}'.format(
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
