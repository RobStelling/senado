# coding='utf-8'
# Imports
from bs4 import BeautifulSoup
from datetime import datetime
import argparse
import csv
import errno
import json
import locale
import matplotlib.pyplot as plt
import os
import pandas as pd
import re
import requests
import time

import rotinas as rtn

""" Versão da aplicação, baseado em https://semver.org
Dado um número de versão MAJOR.MINOR.PATCH, incremente:

MAJOR quando são feitas mudanças de API incompatíveis,
MINOR quando se acrescenta funcionalidade de uma maneira compatível com versões existentes, e
PATCH quando se corrige erros de forma compatível com versões anteriores.

Rótulos adicoinais, para pre-release e metadados de bluid estão disponíveis em extensões do formato
MAJOR.MINOR.PATCH.

MAJOR = 0 indica que o estado atual é de desenvolvimento inicial, qualquer funcionalidade pode mudar.
"""
"""
Lista de ideias a fazer:
- Gerar página HTML (já tempos todo o conteúdo)
  - Yattag? Django?
- Passar parâmetros para aplicação(Ex: número de legislatura, intervalo de polling, etc.)
- Armazenar dados em base de dados (Django ORM?)
- Gastos dos senadores com passagens aéreas são bem "interessantes", talvez valha a pena
  pensar em uma estrutura hieráquica para os dados e coletar alguns (senão todos) tipos de gastos
  e gerar visualizações
- Necessário melhorar gráficos!!
"""

locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')

parser = argparse.ArgumentParser(
    description='Coleta dados de gastos de Senadores brasileiros.')

parser.add_argument('-v', '--verbose', dest='verbose', action='store_true',
                    help='Informa estado da coleta enquanto o programa é executado')

parser.add_argument('-d', '--debug', dest='debug', action='store_true',
                    help='Mostra informações para depuração')

parser.add_argument('-i', '--intervalo', dest='intervalo', type=float, default=0.5,
                    help='Intervalo em segundos entre coletas de páginas, default: 0.5')

args = parser.parse_args()

versao = '0.2.29'


def leDadosParlamentares(legislatura=55):
    """Lê dados de parlamentares das páginas de dados abertos do Senado
    Retorna parlamentares em exercício e fora de exercício
    Documentação da API do Senado Federal:
    http://legis.senado.leg.br/dadosabertos/docs/resource_ListaSenadorService.html
    """
    if args.verbose:
        print('Lendo dados de parlamentares da legislatura {}...'.format(legislaturaAtual), flush=True)

    def ativo(parlamentar, data):
        """Verifica se um parlamentar está ativo em uma data
        Retorna True se estiver ativo, False se estiver inativo
        """

        # Um senador é eleito por 8 anos em duas legislaturas consecutivas
        # de 4 anos, com trocas de 1/3 do senado em uma eleição e 2/3 na seguinte.
        # Os testes de 'Terceira' em diante são para acomodar possíveis mudanças.
        ordemLegislatura = ['Primeira', 'Segunda', 'Terceira',
                            'Quarta', 'Quinta', 'Sexta', 'Setima', 'Oitava', 'Nona']
        for ordinal in ordemLegislatura:
            # Se não encontrou legislatura então não é senador atual
            if parlamentar['Mandatos']['Mandato'].get(f"{ordinal}LegislaturaDoMandato", '') == '':
                return False

            ordemLegislatura = parlamentar['Mandatos'][
                'Mandato'][f"{ordinal}LegislaturaDoMandato"]
            # Datas estão no formato aaaa-mm-dd
            inicio = [int(x)
                      for x in ordemLegislatura['DataInicio'].split('-')]
            fim = [int(x) for x in ordemLegislatura['DataFim'].split('-')]
            dataInicio = datetime(inicio[0], inicio[1], inicio[2])
            dataFim = datetime(fim[0], fim[1], fim[2])
            # Se o mandato é atual (inicio < data < fim)
            if dataInicio < data < dataFim:
                # Recupera os exercícios
                exercicios = parlamentar['Mandatos']['Mandato']['Exercicios']['Exercicio']
                # Se houve só um exercício o JSON retorna um dicionário e não uma lista de dicionários.
                # Nesse caso convertemos o dicionário para lista de dicionário, para facilitar o teste a seguir
                if not isinstance(exercicios, list):
                    exercicios = [exercicios]
                # Se entre os exercícios há um exercício sem DataFim, então esse é o exercício ativo
                for ex in exercicios:
                    if ex.get('DataFim', '') == '':
                        return True
        # Se não encontrou nenhum mandado ou exercício
        # então não está ativo
        return False

    # Define que aceita JSON
    # Resposta padrão da API é XML
    header = {'Accept': 'application/json',
              'user-agent': f"senadoInfo/{versao}"}
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

    Os tres parlamentares acima não aparecem nas listas de Vacantes do Senado, os senadores abaixo também
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
    listaNegada = ["Demóstenes Torres", "Gilvam Borges", "Itamar Franco", "João Ribeiro",
                   "Marinor Brito", "Vital do Rêgo", "Wellington Dias", "Wilson Santiago"]
    i = 0
    # Retira da lista os parlamentares que nunca exerceram mandato
    # ou que estão na "listaNegada"
    while i < len(parlamentares):
        if parlamentares[i]['Mandatos']['Mandato'].get('Exercicios', '') == '':
            parlamentares.pop(i)
        elif parlamentares[i]['IdentificacaoParlamentar']['NomeParlamentar'] in listaNegada:
            listaNegada.remove(
                parlamentares[i]['IdentificacaoParlamentar']['NomeParlamentar'])
            parlamentares.pop(i)
        else:
            i += 1

    hoje = datetime.today()
    # Se for ativo, é atual
    parlamentaresAtuais = [x for x in parlamentares if ativo(x, hoje)]
    # Se não for atual, está Fora de Exercício
    parlamentaresForaExercicio = [
        x for x in parlamentares if not x in parlamentaresAtuais]

    if args.verbose:
        print('Fim de leitura de dados de parlamentares...')

    return parlamentaresAtuais, parlamentaresForaExercicio


def adicionaDados(lista, parlamentar, status='Exercicio'):
    """Adiciona dados de parlametares, com os campos escolhidos, a uma lista
    Não retorna valor (a lista de entrada é modificada)
    Se status não for passado assume que parlamentar está em exercício
    """

    def limpaNome(nome):
        """Retorna o nome em minúsculas e com caracteres acentuados convertidos
        para caracteres sem acentos. Para ordenação do DataFrame pelo campo nome
        """
        p = {'a': re.compile('(á|â|à|ã|ä)'), 'e': re.compile('(é|ê|è|ë)'), 'i': re.compile('(í|î|ì|ï)'),
             'o': re.compile('(ó|ô|ò|õ|ö)'), 'u': re.compile('(ú|û|ù|ü)'), 'c': re.compile('(ç)')}
        nomeMinusculas = nome.lower()
        for letra in p:
            nomeMinusculas = p[letra].sub(letra, nomeMinusculas)
        return nomeMinusculas

    lista.append({'codigo': parlamentar['IdentificacaoParlamentar']['CodigoParlamentar'],
                  'nomeCompleto': parlamentar['IdentificacaoParlamentar']['NomeCompletoParlamentar'],
                  'nome': parlamentar['IdentificacaoParlamentar']['NomeParlamentar'],
                  'nomeSort': limpaNome(parlamentar['IdentificacaoParlamentar']['NomeParlamentar']),
                  # Alguns não tem email
                  'email': parlamentar['IdentificacaoParlamentar'].get('EmailParlamentar', ''),
                  'sexo': parlamentar['IdentificacaoParlamentar']['SexoParlamentar'],
                  # Se for falecido não há sigla do partito
                  'partido': parlamentar['IdentificacaoParlamentar'].get('SiglaPartidoParlamentar', ''),
                  'urlFoto': parlamentar['IdentificacaoParlamentar']['UrlFotoParlamentar'],
                  'urlPagina': parlamentar['IdentificacaoParlamentar']['UrlPaginaParlamentar'],
                  # Se for afastado então a UF está em Mandato
                  'UF': parlamentar['IdentificacaoParlamentar'].get('UfParlamentar', parlamentar['Mandatos']['Mandato']['UfParlamentar']),
                  'Participacao': parlamentar['Mandatos']['Mandato']['DescricaoParticipacao'],
                  'status': status})


def infoSenador(codigoSenador, ano=2017, intervalo=0, nascimento=False):
    """Coleta informações de um ano de legislatura de um senador pelo seu código
    Retorna o total de gastos de um parlamentar, uma lista de meses de utilização
    de auxílio moradia e apartamento funcional e uma lista de utilização de pessoal
    no gabinete e escritórios de apoio.
    Consulta as páginas de transparência do senado para efetuar a operação,
    se definido, espera "intervalo" segundos antes de fazer a requisição
    Página exemplo: Senador Itamar Franco, 2011
    http://www6g.senado.leg.br/transparencia/sen/1754/?ano=2011
    """
    if args.debug:
        print('Senador: {} Ano: {}'.format(codigoSenador, ano))
    if args.verbose:
        print('.', end='', flush=True)            # Indicador de atividade
    # Intervalo, em segundos, antes de carregar a página
    if intervalo > 0:
        time.sleep(intervalo)

    header = {'user-agent': f"senadoInfo/{versao}"}
    # Coleta a página
    url = f"http://www6g.senado.leg.br/transparencia/sen/{codigoSenador}/?ano={ano}"

    try:
        requisicao = requests.get(url, headers=header)
    except requests.exceptions.RequestException as erro:
        print(erro)
        sys.exit(1)

    total = 0
    infoAuxilio = []
    infoPessoal = []
    gastos = {'ano': ano, 'total': 0.0, 'lista': {}}
    sopaSenador = BeautifulSoup(requisicao.content, 'html.parser')
    if nascimento:
        dadosPessoais = sopaSenador.find(
            'div', {'class': 'dadosPessoais'}).find_all('dd')
        labelDadosPessoais = sopaSenador.find(
            'div', {'class': 'dadosPessoais'}).find_all('dt')

        dataNascimento, cidade, estado = ["", "", ""]

        for index, label in enumerate(labelDadosPessoais):
            if label.text == 'Data de Nascimento:':
                dataNascimento = dadosPessoais[index].text.strip()
            if label.text == 'Naturalidade:':
                cidadeEstado = dadosPessoais[index].text.strip().split('\n')
                cidade = cidadeEstado[0].strip()
                if len(cidadeEstado) == 2:
                    estado = cidadeEstado[1].strip()[1:3]

        if cidade == "":
            listaMunicipios = []
        elif estado == "":
            listaMunicipios = municipios.query(
                'NM_MUN_2016 == "{}"'.format(cidade.upper())).values
        else:
            listaMunicipios = municipios.query(
                'NM_MUN_2016 == "{}" and NM_UF_SIGLA == "{}"'.format(cidade.upper(), estado.upper())).values

        if len(listaMunicipios) != 1:
            codMunicipio = -1
            if args.debug:
                print("Senador {}, erro de municipio: {} {}".format(
                    codigoSenador, cidade, estado))
        else:
            codMunicipio = listaMunicipios[0][4]

        nascimentoSenador = [dataNascimento, codMunicipio]
    else:
        nascimentoSenador = None
    # Se houve um redirect então a página sobre aquele ano daquele senador não existe
    if requisicao.history:
        return total, infoAuxilio, infoPessoal, gastos, nascimentoSenador

    # E gera a sopa

    # Seleciona a área onde estão os dados desejados
    bloco = sopaSenador.find('div', {'class': 'sen-conteudo-interno'})
    tabelas = bloco.find_all('div', {'class': 'accordion-inner'})
    # tabelas[0]: Valores de Cotas para Exercício da Atividade Parlamentar
    # tabelas[1]: Valores de Outros Gastos
    # tabelas[2]: Uso de Outros Benefícios
    # tabelas[3]: Quantidade de funcionários por local e vínculo
    # tabelas[4]: Consulta de subsídios e aposentadoria

    # Primeiro computa o total de gastos do senador
    # Os totais de gastos estão nos dois rodapés das tabelas
    valores = bloco.find_all('tfoot')

    # Extrai apenas o valor em string (strip().split()[1]),
    # converte para float (rtn.s2float) e contabiliza o total
    for i in range(len(valores)):
        valores[i] = rtn.s2float(valores[i].text.strip().split()[1])
        # Só extrai os valores se a totalização for > 0
        if (valores[i] > 0):
            for linha in tabelas[i].find('tbody').find_all('tr', {'class': None}):
                colunas = linha.find_all('td')
                caput = colunas[0].text.strip().split('\xa0')[0]
                montante = rtn.s2float(colunas[1].text.strip())
                if montante > 0:
                    gastos['lista'][caput] = montante
                    gastos['total'] += gastos['lista'][caput]
                #print(linhas[campos].text.strip().split('\xa0')[0],'---', linhas[campos+1].text.strip())
        total += valores[i]

    # pega Correios em separado
    correios = tabelas[1].find('tbody').find_all(
        'tr', {'class': 'sen_tabela_linha_grupo'})[2].find_all('td')
    correiosCaput = correios[0].text.strip()
    correiosMontante = rtn.s2float(correios[1].text.strip())
    if correiosMontante > 0:
        gastos['lista'][correiosCaput] = correiosMontante
        gastos['total'] += gastos['lista'][correiosCaput]
    gastos['total'] = round(gastos['total'], 2)
    # Depois recupera utilização de auxílio-moradia e imóvel funcional
    # Auxílios estão em #accordion-outros
    outros = bloco.find('div', {'id': 'accordion-outros'})
    # e os dados estão em td's
    tdOutros = outros.find_all('td')

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
            if not re.match(r'Informações disponíveis.*', uso) and not re.match(r'Informações não disponíveis.*', uso):
                meses = int(uso.replace('Utilizou (', '').replace(
                    ' meses)', '').replace(' mês)', ''))

        infoAuxilio.append({'beneficio': auxilio, 'meses': meses})

    # Ao fim, recupera as informações de uso de pessoal

    # Recupera dados de pessoal
    # bloco->div(#accordion-pessoal)->tbody->ALL tr(.sen_tabela_linha_grupo)
    quantidades = bloco.find('div', {'id': 'accordion-pessoal'}).find(
        'tbody').find_all('tr', {'class': 'sen_tabela_linha_grupo'})

    # O título da utilização de pessoal está no elemento <span> e quantidades no elemento <a>
    for i in range(len(quantidades)):
        infoPessoal.append(
            {'titulo': quantidades[i].find('span').text.strip(),
             'quantidade': int(quantidades[i].find('a').text.strip().split()[0])})

    # print(bloco)
    # Retorna o gasto total do senador para o ano pedido
    return round(total, 2), infoAuxilio, infoPessoal, gastos, nascimentoSenador


def infoLegislaturaAtual():
    if args.verbose:
        print("Verificando legislatura atual...")
    """Retorna a legislatura atual e os anos de exercício a partir
    da página de senadores em exercício do senado
    """
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

    # Recupera as strings dos anos iniciais e finais
    anos = textoLegislatura.split('(')[1].split(')')[0].split('-')
    # Converte os anos para inteiro
    for i in range(len(anos)):
        anos[i] = int(anos[i].strip())
    # Reconstroi a lista como um range do ano inicial para o final
    anos = list(range(anos[0], anos[1] + 1))

    return numeroLegislatura, anos

legislaturaAtual, anos = infoLegislaturaAtual()
anoAtual = datetime.today().year
""" Só contabiliza até o ano anterior
Devemos incluir ano atual se for parcial?
Por exemplo, se estivermos em julho de 2018, devemos incluir também os dados de 2018?
Resposta: É preciso esperar um pouco para ver em quanto tempo o senado atualiza as inforamções
de gastos do ano corrente, dependendo da frequência pode ser interessante incluir o ano corrente ou não.
Por outro lado verificamos que o senado atualiza e inclui novos gastos do ano anterio até pelo menos
fevereiro do ano seguinte.
"""
i = 0
while i < len(anos):
    if anos[i] >= anoAtual:
        anos.pop(i)
    else:
        i += 1

parlamentares, parlamentaresForaExercicio = leDadosParlamentares(
    legislaturaAtual)

dados = []
if args.verbose:
    print('Organizando informações de parlamentares...')
# Adiciona informações dos parlamentares em exercício e fora de exercício
# à lista 'dados'
for senador in parlamentares:
    adicionaDados(dados, senador, status='Exercicio')

for senador in parlamentaresForaExercicio:
    adicionaDados(dados, senador, status='ForaExercicio')

if args.verbose:
    print('Fim de organização de informações...')
    print('Recuperando informações de gastos parlamentares...')

# Lê o arquivo de gastos de combustível a partir de 2016


def leGastosCombustiveis(anos):
    # Senado passou a contabilizar gastos de combustíveis em separado
    # a partir de 2016
    anoInicial = max(2016, anos[0])
    anoFinal = anos[len(anos) - 1] + 1
    dadosGastosCombustiveis = {}
    # Formato arquivos:
    # senador(nome),codigo(inteiro),gastos(reais/float)
    for ano in range(anoInicial, anoFinal):
        dadosGastosCombustiveis[ano] = {}
        arquivo = f"csv/{ano}C.csv"
        with open(arquivo, newline='') as gCombustiveis:
            gCReader = csv.reader(gCombustiveis)
            header = next(gCReader)
            for registro in gCReader:
                dadosGastosCombustiveis[ano][registro[1]] = float(registro[2])
    return dadosGastosCombustiveis


combustiveis = leGastosCombustiveis(anos)

# Para cada senador coleta os gastos de cada ano da legislatura
# e soma os gastos em 'gastos'
colunaInteiro = set()
gastosSenadores = []
# Abre o arquivo de municípios, para inclusão do código do município de nascimento
# do senador
municipios = pd.read_csv('csv/AR_BR_MUN_2016.csv',
                         encoding='utf-8')
# A variável senador serve de índice para dados e para gastosSenadores,
# porque sempre aponta para o senador atual.
for senador in range(len(dados)):
    gastosSenadores.append({'senador': dados[senador]['codigo'], 'gastos': []})
    dados[senador]['gastos'] = 0
    # Para cada ano, recupera as informações do senador
    # Guarda o total daquele ano (dados[senador][gastos{ano}]) e soma no total
    # de gastos (gastos).
    # Cria uma coluna para cada tipo de uso de
    # pessoal
    for ano in anos:
        # Total gasto, utilização de auxílio moradia e apartamento funcional e uso de pessoal
        total, auxilio, pessoal, gastos, nascimento = infoSenador(
            dados[senador]['codigo'], ano=ano, intervalo=args.intervalo, nascimento=ano == anos[0])
        if nascimento != None:
            dados[senador]['nascimentoData'] = nascimento[0]
            dados[senador]['naturalMunicipio'] = nascimento[1]
        gastosSenadores[senador]['gastos'].append(gastos)
        if total != gastos['total']:
            print(
                f"Erro de totalização: {dados[senador]['codigo']} - {ano} - {total} - {gastos['total']}")
        dados[senador][f"gastos{ano}"] = total
        dados[senador]['gastos'] += total
        dados[senador][f"TotalGabinete-{ano}"] = 0
        for tipo in range(len(pessoal)):
            coluna = f"{pessoal[tipo]['titulo']}-{ano}"
            colunaInteiro.add(coluna)
            quantidade = pessoal[tipo]['quantidade']
            dados[senador][coluna] = quantidade
            dados[senador][f"TotalGabinete-{ano}"] += quantidade
        for beneficio in range(len(auxilio)):
            coluna = f"{auxilio[beneficio]['beneficio']}-{ano}"
            colunaInteiro.add(coluna)
            meses = auxilio[beneficio]['meses']
            dados[senador][coluna] = meses


def gastosCombustiveis(listaGastos, senador, ano):
    """ Retorna o gasto de combustíveis de um senador
    """
    try:
        return listaGastos[ano][senador]
    except KeyError:
        return 0.0


def consolidaGastosCombustiveis(senadores, combustiveis):
    """ Consolida o total gasto em combustíveis nos gastos dos senadores
    dados serão salvos em JSON
    """
    caputCombustiveis = "Combustíveis"
    for senador in range(len(senadores)):
        for gastos in range(len(senadores[senador]['gastos'])):
            gastosCSenador = gastosCombustiveis(
                combustiveis, senadores[senador]['senador'], senadores[senador]['gastos'][gastos]['ano'])
            if gastosCSenador > 0:
                if caputCombustiveis in senadores[senador]['gastos'][gastos]['lista']:
                    senadores[senador]['gastos'][gastos]['lista'][caputCombustiveis] += gastosCSenador
                else:
                    senadores[senador]['gastos'][gastos]['lista'][caputCombustiveis] = gastosCSenador
                senadores[senador]['gastos'][gastos]['total'] += gastosCSenador
    return


def consolidaDadosCombustiveisSenadores(dados, combustiveis):
    """ Consolida o total gasto em combustível no dataframe dados
    """
    for senador in range(len(dados)):
        codigo = dados[senador]['codigo']
        anoInicial = max(2016, anos[0])
        anoFinal = anos[len(anos) - 1] + 1
        for ano in range(anoInicial, anoFinal):
            gastosCombustiveisSenador = gastosCombustiveis(
                combustiveis, codigo, ano)
            if gastosCombustiveisSenador > 0:
                dados[senador]['gastos'] += gastosCombustiveisSenador
                dados[senador][f"gastos{ano}"] += gastosCombustiveisSenador
    return


consolidaGastosCombustiveis(gastosSenadores, combustiveis)
consolidaDadosCombustiveisSenadores(dados, combustiveis)

# Salva arquivo json
if not os.path.exists('json'):
    os.makedirs('json')

with open('json/gastosSenadores.json', 'w', encoding='utf-8') as saida:
    json.dump(gastosSenadores, saida, ensure_ascii=False,
              indent=2, separators=(',', ':'))

# Acrescenta zeros (int) em colunas que não existem para alguns senadores
# Por exemplo: um determinado senador não possui informação de Gabinete em 2015
for coluna in colunaInteiro:
    for senador in range(len(dados)):
        if dados[senador].get(coluna, 'Não tem') == 'Não tem':
            dados[senador][coluna] = 0
if args.verbose:
    print('\nFim de recuperação de informações de gastos parlamentares...\n')


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
top = dadosSenado.sort_values(by=['gastos'], ascending=[False]).head(15)

# Dataframes de gastos por estado e por partidos
listaColunas = list(dadosSenado.columns)
# Exclui a coluna naturalMunicipio, que é inteira mas não entra no cálculo de soma
listaColunas.remove('naturalMunicipio')
gastoEstados = dadosSenado.groupby('UF')[listaColunas].sum().sort_values(
    by=['gastos'], ascending=[False])
gastoPartidos = dadosSenado.groupby('partido')[listaColunas].sum().sort_values(
    by=['gastos'], ascending=[False])
sexo = dadosSenado.rename(columns={'Participacao': '(Sexo, Situação)'}).groupby(
    ['sexo', 'status'])['(Sexo, Situação)'].count()
sexoT = dadosSenado[['Participacao', 'sexo']].groupby(['sexo']).count()

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
print('O montante de despesas parlamentares em {:d} anos foi de '.format(len(anos)) + rtn.reais(
    totalGasto) + ', com media anual de ' + rtn.reais(totalGasto / len(anos)))

if args.verbose:
    print("Gravando arquivos...")
# Salva arquivos
if not os.path.exists('csv'):
    os.makedirs('csv')

dadosSenado.to_csv('csv/senado.csv', na_rep='', header=True, index=False,
                   mode='w', encoding='utf-8', line_terminator='\n', decimal='.', float_format='%.2f')
top.to_csv('csv/top.csv', na_rep='', header=True, index=False,
           mode='w', encoding='utf-8', line_terminator='\n', decimal='.', float_format='%.2f')
gastoPartidos.to_csv('csv/gastoPartidos.csv', na_rep='', header=True,
                     index=True, mode='w', encoding='utf-8', line_terminator='\n', decimal='.', float_format='%.2f')
gastoEstados.to_csv('csv/gastoEstados.csv', na_rep='', header=True, index=True,
                    mode='w', encoding='utf-8', line_terminator='\n', decimal='.', float_format='%.2f')
sexo.to_csv('csv/sexo.csv', index=True, na_rep='', header=True,
            index_label=None, mode='w', encoding='utf-8', decimal='.')
sexoT.to_csv('csv/sexoT.csv', index=True, na_rep='', header=True,
             index_label=None, mode='w', encoding='utf-8', decimal='.')

with open('csv/anos.csv', 'w') as arquivoAnos:
    anosWriter = csv.writer(arquivoAnos)
    anosWriter.writerow(["Legislatura", "Inicial", "Final", "Coleta"])
    anosWriter.writerow(
        [legislaturaAtual, anos[0], anos[-1], datetime.today()])
    arquivoAnos.close()

if args.verbose:
    print("Verificando fotos...")
# Coleta fotos que estejam faltando
# Créditos devem ser extraídos do
# EXIF de cada foto
dirFotos = 'fotos'
if not os.path.exists(dirFotos):
    os.makedirs(dirFotos)

for url in dadosSenado['urlFoto']:
    nomeArquivo = f"{dirFotos}/{url.split('/')[-1]}"
    if not os.path.exists(nomeArquivo):
        header = {'user-agent': f"senadoInfo/{versao}", 'Accept': 'image/jpeg'}
        try:
            requisicao = requests.get(url, headers=header, stream=True)
        except requests.exceptions.RequestException as erro:
            print(erro)
            sys.exit(1)
        if requisicao.status_code == 200:
            print(f"Criando arquivo {nomeArquivo}...")
            arquivo = open(nomeArquivo, 'wb')
            arquivo.write(requisicao.content)
            arquivo.close()
        else:
            print(f"Erro {requisicao.status_code} na recuperação de {url}")