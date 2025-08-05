@echo off
REM Coletor de Informacoes de Hardware - Versao BAT
REM Este arquivo executa o coletor Python diretamente

title Coletor de Informacoes de Hardware

echo ===================================================
echo   Coletor de Informacoes de Hardware - Prefeitura
echo ===================================================
echo.
echo Iniciando coleta de informacoes...
echo.

REM Verifica se o Python esta instalado
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERRO: Python nao encontrado. 
    echo Por favor, instale o Python 3.x ou use a versao executavel.
    echo.
    echo Pressione qualquer tecla para sair...
    pause >nul
    exit /b 1
)

REM Verifica se o script principal existe
if not exist "%~dp0coletor.py" (
    echo ERRO: Arquivo coletor.py nao encontrado.
    echo Certifique-se de que este .bat esta no mesmo diretorio que o coletor.py
    echo.
    echo Pressione qualquer tecla para sair...
    pause >nul
    exit /b 1
)

REM Verifica se o script PowerShell existe
if not exist "%~dp0coletar_monitores.ps1" (
    echo ERRO: Arquivo coletar_monitores.ps1 nao encontrado.
    echo Certifique-se de que este .bat esta no mesmo diretorio que o coletar_monitores.ps1
    echo.
    echo Pressione qualquer tecla para sair...
    pause >nul
    exit /b 1
)

REM Verifica se o ambiente virtual existe, se nao, cria
if not exist "%~dp0venv\" (
    echo Criando ambiente virtual...
    python -m venv "%~dp0venv"
    echo Instalando dependencias...
    call "%~dp0venv\Scripts\activate.bat"
    pip install -r "%~dp0requirements.txt"
) else (
    call "%~dp0venv\Scripts\activate.bat"
)

REM Executa o coletor
echo Coletando informacoes de hardware...
python "%~dp0coletor.py"

REM Verifica se a execucao foi bem-sucedida
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERRO: Ocorreu um problema durante a coleta de informacoes.
    echo Verifique se todas as dependencias estao instaladas.
) else (
    echo.
    echo Coleta de informacoes concluida com sucesso!
)

echo.
echo Pressione qualquer tecla para sair...
pause >nul
