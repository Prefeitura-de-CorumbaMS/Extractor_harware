# Script para coletar informações detalhadas dos monitores usando comandos exatos fornecidos pelo usuário
# Salva os resultados em um arquivo para ser lido pelo Python

# Verificar se foi passado um caminho para o arquivo de saída como parâmetro
param(
    [string]$OutputFilePath = ""
)

# Se não foi especificado um caminho, usar o diretório do script
if ([string]::IsNullOrEmpty($OutputFilePath)) {
    $scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Definition
    $outputPath = Join-Path -Path $scriptPath -ChildPath "monitores_info.txt"
} else {
    $outputPath = $OutputFilePath
}

# Limpar o arquivo de saída se existir
if (Test-Path $outputPath) {
    Remove-Item $outputPath
}

# 1. Obter quantidade de monitores (comando exato fornecido pelo usuário)
try {
    $quantidadeMonitores = (Get-CimInstance -Namespace root\wmi -ClassName WmiMonitorID).Count
    Add-Content -Path $outputPath -Value "QUANTIDADE_MONITORES: $quantidadeMonitores" -Encoding ASCII
} catch {
    Add-Content -Path $outputPath -Value "QUANTIDADE_MONITORES: Erro ao obter" -Encoding ASCII
}

# Se não encontrou nenhum monitor
if ($quantidadeMonitores -eq 0) {
    Add-Content -Path $outputPath -Value "NENHUM_MONITOR_DETECTADO" -Encoding ASCII
    exit 0
}

# 2. Obter modelo e fabricante (comando exato fornecido pelo usuário)
try {
    $monitoresInfo = @()
    Get-CimInstance -Namespace root\wmi -ClassName WmiMonitorID | ForEach-Object { 
        $modelo = ([System.Text.Encoding]::ASCII.GetString($_.UserFriendlyName -ne 0)).Trim()
        $fabricante = ([System.Text.Encoding]::ASCII.GetString($_.ManufacturerName -ne 0)).Trim()
        $monitoresInfo += [PSCustomObject]@{
            Modelo = $modelo
            Fabricante = $fabricante
            InstanceName = $_.InstanceName
        }
    }
} catch {
    Add-Content -Path $outputPath -Value "ERRO_MODELO_FABRICANTE: $($_.Exception.Message)" -Encoding ASCII
}

# 3. Obter tamanho físico (comando exato fornecido pelo usuário)
try {
    $tamanhos = @{}
    Get-CimInstance -Namespace root\wmi -ClassName WmiMonitorBasicDisplayParams | ForEach-Object {
        $tamanhos[$_.InstanceName] = [PSCustomObject]@{
            LarguraCm = $_.MaxHorizontalImageSize
            AlturaCm = $_.MaxVerticalImageSize
        }
    }
} catch {
    Add-Content -Path $outputPath -Value "ERRO_TAMANHO: $($_.Exception.Message)" -Encoding ASCII
}

# Combinar todas as informações e salvar no arquivo
$contador = 1
foreach ($monitor in $monitoresInfo) {
    Add-Content -Path $outputPath -Value "MONITOR_$contador" -Encoding ASCII
    Add-Content -Path $outputPath -Value "FABRICANTE: $($monitor.Fabricante)" -Encoding ASCII
    Add-Content -Path $outputPath -Value "MODELO: $($monitor.Modelo)" -Encoding ASCII
    
    # Adicionar informações de tamanho se disponíveis
    $tamanhoInfo = $tamanhos[$monitor.InstanceName]
    if ($tamanhoInfo) {
        $larguraCm = $tamanhoInfo.LarguraCm
        $alturaCm = $tamanhoInfo.AlturaCm
        
        if ($larguraCm -gt 0 -and $alturaCm -gt 0) {
            $diagonalCm = [Math]::Sqrt($larguraCm * $larguraCm + $alturaCm * $alturaCm)
            $diagonalPolegadas = [Math]::Round($diagonalCm / 2.54, 1)
            Add-Content -Path $outputPath -Value "TAMANHO: $diagonalPolegadas polegadas ($larguraCm cm x $alturaCm cm)" -Encoding ASCII
        } else {
            Add-Content -Path $outputPath -Value "TAMANHO: Desconhecido" -Encoding ASCII
        }
    } else {
        Add-Content -Path $outputPath -Value "TAMANHO: Desconhecido" -Encoding ASCII
    }
    
    Add-Content -Path $outputPath -Value "---FIM_MONITOR---" -Encoding ASCII
    $contador++
}

# Saída para confirmar conclusão
Write-Output "Informações dos monitores coletadas com sucesso e salvas em: $outputPath"
