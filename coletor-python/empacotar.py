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
    pyinstaller_args = [
        '--onefile',
        '--name=coletor',
        '--hidden-import=wmi',
        '--hidden-import=pythoncom',
        '--hidden-import=subprocess',
        '--hidden-import=tempfile',
        '--hidden-import=ctypes',
        '--hidden-import=pypsrp',
        '--debug=imports',
        '--icon=NONE',
        #  "--noconsole",  # Sem console para não mostrar terminal ao usuário
        '--add-data=coletar_monitores.ps1;.',  # Incluir o script PowerShell no executável
        'coletor.py'
    ]

    try:
        # Executar o PyInstaller diretamente pelo módulo
        import PyInstaller.__main__
        PyInstaller.__main__.run(pyinstaller_args)
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
