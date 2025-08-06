#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import shutil
import subprocess

def main():
    """
    Script para empacotar o coletor.py em um executável para Linux usando PyInstaller.
    """
    print("Iniciando empacotamento do coletor para Linux...")
    
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
        '--name=TesteSegurancaParaNovoAntivirus_TI_Linux',
        '--hidden-import=psutil',
        '--hidden-import=subprocess',
        '--hidden-import=tempfile',
        '--hidden-import=ctypes',
        '--debug=imports',
        '--icon=NONE',
        '--noconsole',  # Sem console para não mostrar terminal ao usuário
        'coletor_linux.py'
    ]

    try:
        # Executar o PyInstaller diretamente pelo módulo
        import PyInstaller.__main__
        PyInstaller.__main__.run(pyinstaller_args)
        print("PyInstaller executado com sucesso!")
        
        # Mover o executável para o diretório de builds
        origem = os.path.join(dir_atual, "dist", "TesteSegurancaParaNovoAntivirus_TI_Linux")
        destino = os.path.join(dir_builds, "TesteSegurancaParaNovoAntivirus_TI_Linux")
        
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
