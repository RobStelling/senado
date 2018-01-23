# coding='utf-8'
# Imports
from bs4 import BeautifulSoup
from datetime import datetime
import errno
import locale
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
"""
Lista de ideias a fazer:
- Gerar página HTML (já tempos todo o conteúdo)
  - Yattag? Django?
- Incluir tratamento de locale (tratamento de valores numéricos, moeda e ordenação) (Feito)
- Passar parâmetros para aplicação(Ex: número de legislatura, intervalo de polling, etc.)
- Armazenar dados em base de dados (Django ORM?)
"""

locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
versao = '0.2.17'


def reais(x, pos=None):
    """Retorna o valor formatado em reais, o parâmetro pos é necessário
    apenas quando a função é chamada pelo FuncFormatter do matplotlib.ticker
    """
    return 'R$ ' + locale.format('%.2f', x, grouping=True)


def leDadosParlamentares(legislatura=55):
    """Lê dados de parlamentares das páginas de dados abertos do Senado
    Retorna parlamentares em exercício e fora de exercício
    Documentação da API do Senado Federal:
    http://legis.senado.leg.br/dadosabertos/docs/resource_ListaSenadorService.html
    """

    def ativo(parlamentar, data):
        """Verifica se um parlamentar está ativo no momento
        Retorna True se estiver ativo, False se estiver inativo

        """

        # Teoricamente pode haver múltiplas legislaturas de um mandato
        # mas nos exemplos encontrados só vimos casos até segunda.
        ordemLegislatura = ['Primeira', 'Segunda', 'Terceira',
                            'Quarta', 'Quinta', 'Sexta', 'Setima', 'Oitava', 'Nona']
        for ordinal in ordemLegislatura:
            # Se não encontrou legislatura então não é senador atual
            if parlamentar['Mandatos']['Mandato'].get(f"{ordinal}LegislaturaDoMandato", '') == '':
                return False
            ordemLegislatura = parlamentar['Mandatos'][
                'Mandato'][f"{ordinal}LegislaturaDoMandato"]
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
                # Convertemos o dicionário para lista de dicionário, para facilitar o código a seguir
                if not isinstance(exercicios, list):
                    exercicios = [exercicios]
                # Se entre os exercícios há um sem DataFim, então é ativo
                for ex in exercicios:
                    if ex.get('DataFim', '') == '':
                        return True
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
    listaNegada = ["Demóstenes Torres", "Gilvam Borges", "Itamar Franco", "João Ribeiro",
                   "Marinor Brito", "Vital do Rêgo", "Wellington Dias", "Wilson Santiago"]
    i = 0
    # Retira da lista os parlamentares que nunca exerceram mandato
    while i < len(parlamentares):
        if parlamentares[i]['Mandatos']['Mandato'].get('Exercicios', '') == '':
            parlamentares.pop(i)
        elif parlamentares[i]['IdentificacaoParlamentar']['NomeParlamentar'] in listaNegada:
            listaNegada.remove(
                parlamentares[i]['IdentificacaoParlamentar']['NomeParlamentar'])
            parlamentares.pop(i)
        else:
            i = i + 1

    parlamentaresAtuais = []
    parlamentaresForaExercicio = []

    hoje = datetime.today()
    for parlamentar in parlamentares:
        if ativo(parlamentar, hoje):
            parlamentaresAtuais.append(parlamentar)
        else:
            parlamentaresForaExercicio.append(parlamentar)

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


def s2float(dado):
    """ Converte uma string numérica no formato brasileiro para float """
    # Retira '.' e substitui ',' por '.' e converte para float
    return float(dado.replace('.', '').replace(',', '.'))


def infoSenador(codigoSenador, ano=2017, intervalo=0):
    """Coleta informações de um ano de legislatura de um senador pelo seu código
    Retorna o total de gastos de um parlamentar, uma lista de meses de utilização
    de auxílio moradia e apartamento funcional e uma lista de utilização de pessoal
    no gabinete e escritórios de apoio.
    Consulta as páginas de transparência do senado para efetuar a operação,
    se definido, espera "intervalo" segundos antes de fazer a requisição
    Página exemplo: Senador Itamar Franco, 2011
    http://www6g.senado.leg.br/transparencia/sen/1754/?ano=2011
    """
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

    # Se houve um redirect então a página sobre aquele ano daquele senador não existe
    if requisicao.history:
        return total, infoAuxilio, infoPessoal

    # E gera a sopa
    sopaSenador = BeautifulSoup(requisicao.content, 'html.parser')

    # Seleciona a área onde estão os dados desejados
    bloco = sopaSenador.find('div', {'class': 'sen-conteudo-interno'})

    # Primeiro computa o total de gastos do senador
    # Os totais de gastos estão nos dois rodapés das tabelas
    valores = bloco.find_all('tfoot')

    # Extrai apenas o valor em string (strip().split()[1]),
    # converte para float (s2float) e contabiliza o total
    for i in range(len(valores)):
        valores[i] = s2float(valores[i].text.strip().split()[1])
        total += valores[i]

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
            if not re.match(r'Informações disponíveis.*', uso):
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

    # Retorna o gasto total do senador para o ano pedido
    return total, infoAuxilio, infoPessoal


def infoLegislaturaAtual():
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

    anos = textoLegislatura.split('(')[1].split(')')[0].split('-')
    for i in range(len(anos)):
        anos[i] = int(anos[i].strip())

    anos = list(range(anos[0], anos[1] + 1))

    return numeroLegislatura, anos


legislaturaAtual, anos = infoLegislaturaAtual()
anoAtual = datetime.today().year
# Só contabiliza até o ano anterior
# Incluir ano atual se for parcial?
# Por exemplo, se estivermos em julho de 2018, devemos incluir também os dados de 2018?
# Resposta: É preciso esperar um pouco para ver em quanto tempo o senado atualiza as inforamções
# de gastos do ano corrente, dependendo da frequência pode ser interessante incluir o ano atual
i = 0
while i < len(anos):
    if anos[i] >= anoAtual:
        anos.pop(i)
    else:
        i += 1

print('Lendo dados de parlamentares da legislatura {}...'.format(legislaturaAtual))
parlamentares, parlamentaresForaExercicio = leDadosParlamentares(
    legislaturaAtual)
print('Fim de leitura...')

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
colunaInteiro = set()
for senador in range(len(dados)):
    dados[senador]['gastos'] = 0
    # Para cada ano, recupera as informações do senador
    # Guarda o total daquele ano (dados[senador][gastos{ano}]) e soma no total
    # de gastos (gastos).
    # Cria uma coluna para cada tipo de uso de
    # pessoal
    for ano in anos:
        # Total gasto, utilização de auxílio moradia e apartamento funcional e uso de pessoal
        total, auxilio, pessoal = infoSenador(
            dados[senador]['codigo'], ano=ano, intervalo=0.5)
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

# Acrescenta zeros (int) em colunas que não existem para alguns senadores
# Por exemplo: um determinado senador não possui informação de Gabinete em 2015
for coluna in colunaInteiro:
    for senador in range(len(dados)):
        if dados[senador].get(coluna, 'Não tem') == 'Não tem':
            dados[senador][coluna] = 0

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
top = dadosSenado.sort_values(by=['gastos'], ascending=[False]).head(15)

# Dataframes de gastos por estado e por partidos
gastoEstados = dadosSenado.groupby('UF').sum().sort_values(
    by=['gastos'], ascending=[False])
gastoPartidos = dadosSenado.groupby('partido').sum().sort_values(
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
      reais(mediaGastosHomensExercicio))
print('O gasto médio de senadores mulheres em exercício foi de ' +
      reais(mediaGastosMulheresExercicio))
print('O gasto médio dos senadores, em exercício e fora de exercício, foi de ' +
      reais(gastoMedioSenadores))
print('O montante de despesas parlamentares em {:d} anos foi de '.format(len(anos)) + reais(
    totalGasto) + ', com media anual de ' + reais(totalGasto / len(anos)))

# Salva arquivos
if not os.path.exists('csv'):
    os.makedirs('csv')

dadosSenado.to_csv('csv/senado.csv', na_rep='', header=True, index=False,
                   mode='w', encoding='utf-8', line_terminator='\n', decimal='.')
top.to_csv('csv/top.csv', na_rep='', header=True, index=False,
           mode='w', encoding='utf-8', line_terminator='\n', decimal='.')
gastoPartidos.to_csv('csv/gastoPartidos.csv', na_rep='', header=True,
                     index=True, mode='w', encoding='utf-8', line_terminator='\n', decimal='.')
gastoEstados.to_csv('csv/gastoEstados.csv', na_rep='', header=True, index=True,
                    mode='w', encoding='utf-8', line_terminator='\n', decimal='.')
sexo.to_csv('csv/sexo.csv', index=True, na_rep='', header=True,
            index_label=None, mode='w', encoding='utf-8', decimal='.')
sexoT.to_csv('csv/sexoT.csv', index=True, na_rep='', header=True,
             index_label=None, mode='w', encoding='utf-8', decimal='.')

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
