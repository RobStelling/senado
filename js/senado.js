var temDados = false,
  dadosSenadores;

d3.queue()
  .defer(d3.json, "./json/{leg}_gastosSenadores.json".replace("{leg}", legislaturaLevantamento))
  .await(ready);

function ready(error, dados) {
  if (error)
    throw error;
  dadosSenadores = dados;
  temDados = true;
  createTooltip();
}


document.addEventListener("touchstart", function () {}, true);

function ordenaTabela(dir, nomeTabela, coluna, tipo) {
  // Baseado em https://www.w3schools.com/howto/howto_js_sort_table.asp
  function comparaTexto(dir, a, b) {
    // Compara duas strings considerando locale.
    return (dir == "asc" && a.localeCompare(b) == 1) ||
      (dir == "desc" && a.localeCompare(b) == -1);
  }

  function comparaReal(dir, a, b) {
    // Compara valores em reais, no formato R$ 1.027.468,32
    function realParaFloat(texto) {
      // Retorna um float de um texto no formato "R$ 1.534.445,93"
      // Ex: (str) R$ 1.534.445,93 -> (float) 153445.93
      return parseFloat(texto.split(' ')[1].replace(/\./g, '').replace(',', '.'));
    }

    a = realParaFloat(a);
    b = realParaFloat(b);
    return (dir == "asc" && a > b) ||
      (dir == "desc" && a < b);
  }

  function comparaDados(dir, a, b) {
    // Compara valores no formato "<número> <texto>"" ignorando o texto
    // comparação numérica
    function numTexto(texto) {
      // Retorna um inteiro da string no formato
      // <número> <texto>
      return parseInt(texto.split(' ')[0])
    }
    a = numTexto(a);
    b = numTexto(b);
    return (dir == "asc" && a > b) ||
      (dir == "desc" && a < b);
  }

  function comparaParticipacao(dir, a, b) {
    // Compara participação do senador, Titular > 1º Suplente > 2º Suplente etc.
    const ordem = {
      'Titular': 0,
      '1º Suplente': 1,
      '2º Suplente': 2,
      '3º Sup;lente': 3,
      '4º Suplente': 4,
      '5º Suplente': 5,
      '6º Suplente': 6,
      '7º Suplente': 7
    }
    a = ordem[a];
    b = ordem[b];
    return (dir == "asc" && a > b) ||
      (dir == "desc" && a < b);
  }

  var tabela,
    linhas,
    troca,
    i,
    x,
    y,
    temQueTrocar,
    contaTrocas = 0;

  const funcoes = {
    'texto': comparaTexto,
    'reais': comparaReal,
    'dados': comparaDados,
    'participacao': comparaParticipacao
  };

  compara = funcoes[tipo];
  tabela = document.getElementById(nomeTabela);
  troca = true;

  /* Fica em loop enquanto foram feitas trocas */
  while (troca) {
    // No início do loop, nenhuma troca foi feita
    troca = false;
    linhas = tabela.getElementsByTagName("TR");
    // Passa por todos os elementos da tabela, exceto pelo primeiro, que contém o header
    for (i = 1; i < (linhas.length - 1); i++) {
      // Assume que não tem que trocar
      temQueTrocar = false;
      // Recupera os dois elementos a comparar, o da linha atual e o da seguinte
      x = linhas[i].getElementsByTagName("TD")[coluna].innerHTML.trim();
      y = linhas[i + 1].getElementsByTagName("TD")[coluna].innerHTML.trim();
      // Verifica se as linhas precisam ser trocadas
      temQueTrocar = compara(dir, x, y)
      // Se tem que trocar, interrompe o loop
      if (temQueTrocar)
        break;
    }
    if (temQueTrocar) {
      /* Se tem que trocar, faz a troca mas ignora a primeira coluna, que tem
      a numeração da linha da tabela. Marca que a troca foi feita */
      linhas[i].parentNode.insertBefore(linhas[i + 1], linhas[i]);
      // Como trocou a linha inteira, pega só a primeira coluna e inverte
      pa = linhas[i].getElementsByTagName("TD")[0].innerHTML;
      pb = linhas[i + 1].getElementsByTagName("TD")[0].innerHTML;
      linhas[i].getElementsByTagName("TD")[0].innerHTML = pb;
      linhas[i + 1].getElementsByTagName("TD")[0].innerHTML = pa;
      troca = true;
      // A cada troca, incrementa a contagem de trocas
      contaTrocas++;
    } else if (contaTrocas == 0) {
      /* Se o for terminou sem trocas então, da primeira
      vez que chegamos aqui, a tabela já estava ordenada
      pelo critério atual (ascendente, por exemplo) nesse
      caso invertemos a critério e somamos um à contagem de
      trocas. Isso evita um loop infinito caso todos os valores
      da coluna que estamos comparando sejam iguais. */
      const inverte = {
        "asc": "desc",
        "desc": "asc"
      };

      dir = inverte[dir];
      troca = true;
      /* Evita que passemos por aqui mais de uma vez caso
      a coluna só tenha valores iguais */
      contaTrocas++;
    } else
      break;
    /* Se chegamos aqui então todos os valores são iguais,
    não precisamos ficar em loop infinito... */
  }
}

//Cria tooltip para a coluna de Despesas no Mandato
function createTooltip()
{
  tooltip = d3.select("body")
    .append("div")
    .classed("myTip tabelaSimples", true)
    .html("Senado");
  hookTooltip();
}

/* sen = objeto de variaveis globais
 * sen.lista = lista inversa de acesso ao objeto json com dados de gastos de senadores
 * sen.inicio = indice do inicio da busca para senadores que naõ estão na lista inversa
 */
var sen = {};
sen.lista = {};
sen.inicio = 0; 
/* Descreve ações para mouseover, mousemove, mouseout e click sobre o tooltip de despesas
 */
function hookTooltip()
{
  function recuperaSenador(codigo) {
    if (sen.lista[codigo] != undefined)
      return dadosSenadores[sen.lista[codigo]];

    for (i = sen.inicio; i < dadosSenadores.length; i++) {
      sen.lista[dadosSenadores[i]['senador']] = i;
      if (dadosSenadores[i]['senador'] == codigo)
        break;
    }
    sen.inicio = i + 1;
    return dadosSenadores[i];
  }

  var valores = d3.selectAll(".gastos")

  .on("mouseover", function(d){
    var tip = d3.select("div.myTip");
    var k;

    senador = +this.getAttribute('name');
    k = "";
    dados = recuperaSenador(senador);
    for (i=dados['gastos'].length-1; i>=0; i--) {
      if (dados['gastos'][i]['total'] > 0) {
        k += "<table><tr><th>Gastos "+dados['gastos'][i]['ano']+"</th><th>Valor</ht><tr>"
        for (caput in dados['gastos'][i]['lista']) {
          k += "<tr><td>"+caput+"</td><td align='left'>R$ "+dados['gastos'][i]['lista'][caput].toLocaleString('pt-BR')+"</td>";
        }
        k += "</table>"
      }
    }
    tip.html(k);
// Tooltip visivel se houverem gastos
    return tooltip.style("visibility", k == "" ? "hidden" : "visible");})

  .on("mousemove", function(){
/*
* Mantém o tooltip 20px acima e 25px à direita do mouse
*/
    return tooltip.style("top", (d3.event.pageY-20)+"px")
      .style("left",(d3.event.pageX+25)+"px");})

  .on("mouseout", function(d){
/*
* Esconde o tooltip
*/
    return tooltip.style("visibility", "hidden");}) // Hides the tooltip when finished
/*
* Click sem ações no momento
*/
  .on("click", function(d){
    return;
  });
}