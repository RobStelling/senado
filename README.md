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
* Baixar dados do senado e gerar arquivos (csv, json)
* Ler arquivos de entrada e gerar arquivo html: [Versão atual da página](http://stelling.cc/senado)

### Futuro
Versões futuras devem:
* Melhorar tratamento de erros/exceções
* Melhorar e expandir gráficos gerados
* Coletar e agregar outras informações, como:
  * Salários de senadores
  * Custo estimado de pessoal em gabinete por senadores
  * Redes sociais de senadores
