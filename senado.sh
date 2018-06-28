#!/bin/bash
# Script para coleta automática de dados do senado
# Arquivos alterados são atualizados no github
# OBS: git push requer configuração de ssh, como descrito em:
# https://gist.github.com/developius/c81f021eb5c5916013dc
#
# Uso: $0 -l|--legislatura # [-i|--intervalo #.#] [-v|--verbose]
IGNORE=()

# Valores default para as variáveis que
# dependem dos parâmetros
verbose=""
legislatura=""
intervalo="0.5"

# Tratamento de parâmetros
while [[ $# -gt 0 ]]
do
    key="$1"
    case $key in
	-l|--legislatura)
	legislatura=$2
	shift
	shift
	;;
	-i|--intervalo)
	intervalo=$2
	shift
	shift
	;;
	-v|--verbose)
	verbose="-v"
	shift
	;;
	*)
	IGNORE+=("$1")
	shift
	;;
    esac
done
# Repõe os parâmetros ignorados, não
# é estritamente necessário
set -- "${IGNORE[@]}"

# Se o parâmetro legislatura não foi passado, mostra como chamar
# e termina a execução com erro
if [ "$legislatura" == "" ]
then
    echo " Uso: $0 -l|--legislatura # [-i|--intervalo #.#] [-v|--verbose]"
    exit 1
fi

# Lista de arquivos que já tinham sido modificados
# antes da chamada do script
antigos=`git diff --name-only`
contaAntigos=`echo $antigos | wc -w`

echo "Iniciando leitura de dados do senado......"
python senado.py -v -i $intervalo -l $legislatura $verbose

# Se não houve erro na execução (como timeout de rede, por exemplo)
if [ $? -eq 0 ]
then
	arquivos=`git diff --name-only`
    contaArquivos=`echo $arquivos | wc -w`
    adicionais=`expr $contaArquivos - $contaAntigos`
    # Verifica se arquivos foram alterados
    # $adicionais -eq 1 significa que apenas anos.csv foi alterado
    if [ $adicionais -gt 1 ]
    then
		echo "Há arquivos a atualizar!"
		python leArquivos.py -l $legislatura
		arquivos=`git diff --name-only`
		contaArquivos=`echo $arquivos | wc -w`
		contaArquivos=`expr $contaArquivos - $contaAntigos`
		# Se não havia artivos já modificados
		if [ $contaAntigos -eq 0 ]
		then
			# Usa a lista de arquivos do git diff
			lista=$arquivos
		else
			# Senão exclui os já alterados dos arquivos
			# dar commit
			lista=""
			for i in $arquivos
			do
				if ! [[ " $antigos " =~ .*\ $i\ .* ]]
				then
					lista+="$i "
				fi
			done
		fi
		# Acrescenta os arquivos, dá commit e push
		# É necessária uma autenticação ssh entre a
		# estação de trabalho e o github para que o 
		# push possa ser executado sem pedir senha
		echo "$contaArquivos arquivos serão atualizados"
		git add $lista
		git commit -m "Atualização de dados do Senado - auto"
		git push
    else
		echo "Não há arquivos a atualizar!"
		git checkout -- csv/${legislatura}_anos.csv
    fi
fi
