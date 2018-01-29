# Informações do senado brasileiro
Levantamento de informações sobre senadores brasileiros. Trabalho para o curso de Jornalismo de Dados do [KnightCenter](https://journalismcourses.org/)

## Importante
Alterações posteriores ao dia 17/01/2018 foram feitas no arquivo senadov2.py e outros arquivos que foram criados a partir desta data. O arquivo senado.py é o original do dia 17 e não foi alterado desde então. As imagens do diretorio 'imagens' e o arquivo 'texto.txt' também são originais do dia 17/01/2018.

Repositório como no fim do dia 17/01/2018 pode ser visto [aqui](https://github.com/RobStelling/senado/tree/38ef5779e164393248c864a96a44a9ed98157040)

### Como funciona?
O programa lê informações de todos os senadores da legislatura atual, usando a API do senado brasileiro, e
raspa dados das páginas de gastos de cada senador, desde o início desta legislatura, em 2015.

Com os dados contabilizados são gerados textos com informaçes dos senadores e gráficos de distribuição de participação
e gastos, por partido e por estado, além de lista de senadores com maiores gastos.

Na versão atual são contabilizados apenas os gastos de cotas para exercício da atividade parlamentar e outros gastos (como viagens oficiais, diárias, passagens, combustível, correios etc.) de todos os senadores.
O processo está separado em duas fases:
* Baixar dados do senado e gerar arquivos (csv, json, fotos etc.)
* Ler arquivos de entrada e gerar página html: [Versão atual da página](http://stelling.cc/senado)

![Página HTML](https://github.com/RobStelling/senado/blob/master/imagensV2/telaWeb.png)

A página lista todos os senadores, com suas despesas, informaçes de mandato, uso de pessoal em escritório e gabinete e número de meses de utilização de auxílio-moradia e imóvel funcinal.
É possível reordenar as colunas marcadas com o ícone ![sort](https://raw.githubusercontent.com/RobStelling/senado/master/imagensV2/sort.png). Por exemplo, clicar em **Despesas no Mandato** ordena a lista de senadores pelos seus gastos, do maior gasto para o menor. Clicar uma segunda vez na mesma coluna, ordena a lista de senadores do menor gasto para o maior.

Ao passar o mouse sobre a célula de gastos de um senador, abre-se uma janela mostrando os gastos daquele senador durante o mandato, como na imagem acima.

Os gráficos gerados serão incluídos na página HTML mas ainda falta decidir a forma de narrativa.

Por exemplo, o gráfico abaixo mostra os gastos de senadores, de 2015 a 2017 durante o exercício da sua legislatura.
![Gastos do Senado](https://github.com/RobStelling/senado/blob/master/imagensV2/gastosSenado.png)

Um dado interessante, é que despesas com serviços de segurança privada neste período somam R$ 1.419.945,91. O Senador Fernando Collor é responsável por  62% deste montante, com despesas de segurança somando R$ 879.672,41.

### Futuro
Versões futuras devem:
* Incluir mais informações sobre os gastos do senado
* Melhorar tratamento de erros/exceções
* Melhorar e expandir gráficos gerados
* Coletar e agregar outras informações, como:
  * Salários de senadores
  * Custo estimado de pessoal em gabinete por senadores
  * Redes sociais de senadores
