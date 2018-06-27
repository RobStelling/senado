#!/bin/bash
# Script para coleta de dados do senado
# Arquivos alterados são atualizados no git
# Falta incluir ftp dos arquivos para stelling.cc
# Uso: $0 -l|--legislatura legislatura -i|--intervalo intervalo -v|--verbose

POSITIONAL=()
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
	POSITIONAL+=("$1")
	shift
	;;
    esac
done
set -- "${POSITIONAL[@]}"

if [ "$legislatura" == "" ]
then
    echo " Uso: $0 -l|--legislatura legislatura -i|--intervalo intervalo -v|--verbose"
    exit 1
fi

echo "Iniciando leitura de dados do senado......"
python senado.py -v -i $intervalo -l $legislatura $verbose
if [ $? -eq 0 ]
then
    linhas=`git diff --name-only | wc -l`
    if [ $linhas -gt 1 ]
    then
	echo "Há dados a atualizar!"
	python leArquivos.py -l $legislatura
	git add `git diff --name-only | tr '\r\n' ' '`
	git commit -m "Atualização de dados do Senado"
	git push
    else
	echo "Não há dados a atualizar!"
	git checkout -- csv/${legislatura}_anos.csv
    fi
fi
