import locale

def reais(x, pos=None):
    """Retorna o valor formatado em reais, o parâmetro pos é necessário
    apenas quando a função é chamada pelo FuncFormatter do matplotlib.ticker
    """
    return 'R$ ' + locale.format('%.2f', x, grouping=True)