# Informações do senado brasileiro
Levantamento de informações sobre senadores brasileiros. Trabalho para o curso de Jornalismo de Dados do [KnightCenter](https://journalismcourses.org/)

### Como funciona?
O programa lê informações de todos os senadores da legislatura atual, usando a API do senado brasileiro, e
raspa dados das páginas de gastos de cada senador, desde o início desta legislatura, em 2015.

Com os dados contabilizados são gerados textos com informaçes dos senadores e gráficos de distribuição de participação
e gastos, por partido e por estado, além de lista de senadores com maiores gastos.

### Futuro
Versões futuras devem:
* Melhorar tratamento de erros/exceções
* Gerar página HTML com os dados coletados
  * Incluindo informações sobre cada senador (Nome, foto, email etc.)
  * Utilizar frameworks de visualização?
* Salvar e permitir reuso de informação coletada
* Melhorar e expandir gráficos gerados
* Coletar e agregar outras informações, como:
  * Salários de senadores
  * Pessoal em gabinete por senadores
  * Redes sociais de senadores
