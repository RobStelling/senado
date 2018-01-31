Arquivos baixados da página de [Despesas de Combustíveis](https://www12.senado.leg.br/transparencia/sen/gastos-com-combustivel) do Senado Federal.

Testamos várias alternativas para raspar os dados dos arquivos PDF. A melhor opção, até o momento, é [PDF to XLS](http://pdftoxls.com/), um serviço online de conversão de PDF para XLS. Os arquivos são convertidos para XLS e depois de baixados são convertidos para CSV.

Estamos investigando outras alternativas para automatizar o processo, como o uso do [pdfquery](https://pypi.python.org/pypi/pdfquery) ou [tabula](https://github.com/tabulapdf/tabula), mas como os arquivos são publicados com uma frequência baixa é possível manter por um tempo a conversão manual. Além disso as outras alternativas testadas não converteram as tabelas corretamente.

### Atualização em 31/01/2018
A solução a adotar, provavelmente, será uma mescla de processo manual com automático, caso queiramos incluir as despesas de combustíveis aos gastos dos senadores(e queremos!).

Dificuldades: Os dados estão em arquivos .pdf separados por mês. Em alguns meses as colunas das tabelas não possuem o mesmo nome, em outras o formato dos dados não coincide com tabelas anteriores e ainda encontramos erros de grafia em alguns campos. O modelo proposto é então:

1. Baixar automaticamente os arquivos .pdf do Senado para pastas correspondentes ao ano da despesa (pdf/C2016, por exemplo).
2. Converter, em um processo interativo, as tabelas dos PDFs para CSV utilizando o Tabula (ver acima).
3. Massagear os arquivos gerados (utilizando sed, provavelmente), para modificar nomes de colunas e retirar alguns erros já identificados no processo de conversão (por exemplo, linhas que começam com '__"",__' ou terminam com '__,__', '__GAB SEN__' quando deveria ser '__GAB SEN.__', etc).
4. Agregar os valores de todos os meses utilizando uma aplicação python que irá gerar um *.csv* para o ano em questão (por exemplo *2016C.csv*).
5. O programa de leitura (*leArquivos.py* - no momento) lerá os *.csv* de cada ano e agregará os valores lidos aos dataframes gerados na etapa anterior.

Depois disto as páginas HTML, os textos de comentário e os gráficos poderão ser gerados.

### Segunda atualização em 31/01/2018
Ao analisar todos os arquivos desde novembro de 2016 até novembro de 2017, verificamos que há vários formatos de arquivo *PDF*, com tabelas distintas, colunas de nomes diferentes, erros de grafia entre outras inconsistências.

Não se justifica construir uma solução automatizada em função da miríade de alternativas e problemas a resolver. Portanto o método adotado será:
1. Inicialmente baixar todos os *PDFs* de cada ano
2. Para cada ano, converter *PDFs* para *.csv* utilizando o [tabula](https://github.com/tabulapdf/tabula). *Massagear* manualmente os arquivos para garantir a coerência das colunas de identificação do senador e gasto com combustíveis, ignorar as outras colunas.
3. Usar um procedimento parcialmente manual (em Jypiter notebook) para unificar os dados e gerar o arquivo *.csv* para cada ano.
4. A cada relatório mensal, analisar o arquivo e definir o procedimento a seguir.
