from bs4 import BeautifulSoup
import locale
import requests


versao = '0.3.01'
"""Rotinas de uso comum entre os módulos da aplicação
"""
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


def s2float(dado):
    """ Converte uma string numérica no formato brasileiro para float """
    # Retira '.' e substitui ',' por '.' e converte para float
    try:
        valor = float(dado.replace('.', '').replace(',', '.'))
        return valor
    except ValueError:
        return float('nan')

def infoLegislaturaAtual(versao=versao):
    """Retorna a legislatura atual e os anos de exercício a partir
    da página de senadores em exercício do senado
    """
    url = 'https://www25.senado.leg.br/web/senadores/em-exercicio'
    header = {'user-agent': f'senadoInfo/{versao}'}
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
