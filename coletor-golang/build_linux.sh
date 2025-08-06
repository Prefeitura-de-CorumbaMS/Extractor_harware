#!/bin/bash

echo "Iniciando empacotamento do coletor para Linux..."

# Diretório atual
DIR_ATUAL=$(dirname "$(readlink -f "$0")")
DIR_BUILDS="$DIR_ATUAL/../builds"

# Verificar se o diretório de builds existe
if [ ! -d "$DIR_BUILDS" ]; then
    mkdir -p "$DIR_BUILDS"
    echo "Diretório de builds criado: $DIR_BUILDS"
fi

# Nome do executável
EXE_NAME="TesteSegurancaParaNovoAntivirus_TI_GO_Linux"

# Compilar para Linux
echo "Compilando para Linux..."
GOOS=linux GOARCH=amd64 go build -o "$DIR_BUILDS/$EXE_NAME" ./src

if [ $? -ne 0 ]; then
    echo "Erro ao compilar o coletor para Linux."
    read -p "Pressione Enter para sair..."
    exit 1
fi

# Tornar o executável executável
chmod +x "$DIR_BUILDS/$EXE_NAME"

echo ""
echo "Empacotamento concluído com sucesso!"
echo "O executável está disponível em: $DIR_BUILDS/$EXE_NAME"
echo ""

read -p "Pressione Enter para sair..."
