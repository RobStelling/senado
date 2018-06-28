#!/bin/bash
# Script para coleta automática de dados do senado
# Arquivos alterados são atualizados no github
# OBS: git push requer configuração de ssh, como descrito em:
# https://gist.github.com/developius/c81f021eb5c5916013dc
#
# Uso: $0 -l|--legislatura # [-i|--intervalo #.#] [-v|--verbose]
IGNORE=()
verbose=""
legislatura=""
intervalo="0.5"
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
set -- "${IGNORE[@]}"

if [ "$legislatura" == "" ]
then
    echo " Uso: $0 -l|--legislatura # [-i|--intervalo #.#] [-v|--verbose]"
    exit 1
fi

echo "Iniciando leitura de dados do senado......"
python senado.py -v -i $intervalo -l $legislatura $verbose
if [ $? -eq 0 ]
then
    arquivos=`git diff --name-only | wc -l`
    if [ $arquivos -gt 1 ]
    then
	echo "Há arquivos a atualizar!"
	python leArquivos.py -l $legislatura
	arquivos=`git diff --name-only | wc -l`
	echo "$arquivos arquivos serão atualizados"
	git add `git diff --name-only | tr '\r\n' ' '`
	git commit -m "Atualização de dados do Senado - auto"
	git push
    else
	echo "Não há arquivos a atualizar!"
	git checkout -- csv/${legislatura}_anos.csv
    fi
fi
