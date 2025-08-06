@echo off
echo Iniciando empacotamento do coletor para Windows...

rem Diretório atual
set DIR_ATUAL=%~dp0
set DIR_BUILDS=%DIR_ATUAL%..\builds

rem Verificar se o diretório de builds existe
if not exist "%DIR_BUILDS%" (
    mkdir "%DIR_BUILDS%"
    echo Diretório de builds criado: %DIR_BUILDS%
)

rem Nome do executável
set EXE_NAME=TesteSegurancaParaNovoAntivirus_TI_GO.exe

rem Compilar para Windows
echo Compilando para Windows...
go build -o "%DIR_BUILDS%\%EXE_NAME%" -ldflags="-H windowsgui" ./src

if %ERRORLEVEL% NEQ 0 (
    echo Erro ao compilar o coletor para Windows.
    pause
    exit /b 1
)

echo.
echo Empacotamento concluído com sucesso!
echo O executável está disponível em: %DIR_BUILDS%\%EXE_NAME%
echo.

pause
