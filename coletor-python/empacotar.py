#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import shutil
import subprocess

def main():
    """
    Script para empacotar o coletor.py em um executável usando PyInstaller.
    """
    print("Iniciando empacotamento do coletor...")
    
    # Diretório atual
    dir_atual = os.path.dirname(os.path.abspath(__file__))
    
    # Diretório de builds
    dir_builds = os.path.join(os.path.dirname(dir_atual), "builds")
    
    # Verificar se o diretório de builds existe
    if not os.path.exists(dir_builds):
        os.makedirs(dir_builds)
        print(f"Diretório de builds criado: {dir_builds}")
    
    # Comando PyInstaller
    comando = [
        "pyinstaller",
        "--onefile",  # Criar um único arquivo executável
        "--name=coletor",  # Nome do executável
        "--hidden-import=wmi",  # Incluir módulo wmi explicitamente
        "--hidden-import=pythoncom",  # Dependência do wmi
        "--hidden-import=subprocess",  # Garantir que subprocess seja incluído
        "--hidden-import=tempfile",  # Garantir que tempfile seja incluído
        "--hidden-import=ctypes",  # Garantir que ctypes seja incluído
        "--hidden-import=pypsrp",  # Biblioteca para comandos PowerShell
        "--debug=imports",  # Ajuda a identificar problemas de importação
      #  "--noconsole",  # Sem console para não mostrar terminal ao usuário
        "--icon=NONE",  # Sem ícone (pode ser substituído por um caminho para um arquivo .ico)
        "coletor.py"  # Script a ser empacotado
    ]
    
    try:
        # Executar PyInstaller
        subprocess.run(comando, check=True)
        print("PyInstaller executado com sucesso!")
        
        # Mover o executável para o diretório de builds
        origem = os.path.join(dir_atual, "dist", "coletor.exe")
        destino = os.path.join(dir_builds, "coletor.exe")
        
        if os.path.exists(origem):
            shutil.copy2(origem, destino)
            print(f"Executável copiado para: {destino}")
        else:
            print(f"Erro: Executável não encontrado em {origem}")
            return False
        
        print("\nEmpacotamento concluído com sucesso!")
        print(f"O executável está disponível em: {destino}")
        return True
    
    except Exception as e:
        print(f"Erro durante o empacotamento: {e}")
        return False

if __name__ == "__main__":
    sucesso = main()
    
    if not sucesso:
        print("\nOcorreram erros durante o empacotamento.")
        sys.exit(1)
    
    print("\nPressione Enter para sair...")
    input()
