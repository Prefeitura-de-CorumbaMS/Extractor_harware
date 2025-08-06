// +build windows

package hardware

import (
	"fmt"
	"os"
	"os/exec"
	"os/user"
	"path/filepath"
	"strconv"
	"strings"
	"time"

	"github.com/go-ole/go-ole"
	"github.com/go-ole/go-ole/oleutil"
	"github.com/shirou/gopsutil/v3/cpu"
	"github.com/shirou/gopsutil/v3/disk"
	"github.com/shirou/gopsutil/v3/mem"
)

// ObterUsuarioLogado retorna o nome do usuário logado no sistema
func ObterUsuarioLogado() string {
	// Método 1: Usando os/user
	currentUser, err := user.Current()
	if err == nil && currentUser.Username != "" {
		// Remover domínio se presente (formato: DOMINIO\usuario)
		username := currentUser.Username
		if strings.Contains(username, "\\") {
			parts := strings.Split(username, "\\")
			return parts[1]
		}
		return username
	}

	// Método 2: Usando variáveis de ambiente
	username := os.Getenv("USERNAME")
	if username != "" {
		return username
	}

	// Método 3: Usando PowerShell
	cmd := exec.Command("powershell", "-command", "[System.Security.Principal.WindowsIdentity]::GetCurrent().Name")
	output, err := cmd.Output()
	if err == nil && len(output) > 0 {
		username = strings.TrimSpace(string(output))
		if strings.Contains(username, "\\") {
			parts := strings.Split(username, "\\")
			return parts[1]
		}
		return username
	}

	return "Usuário desconhecido"
}

// ObterNomeDispositivo retorna o nome do dispositivo
func ObterNomeDispositivo() string {
	hostname, err := os.Hostname()
	if err != nil {
		return "Dispositivo desconhecido"
	}
	return hostname
}

// ObterInfoProcessador retorna informações detalhadas do processador
func ObterInfoProcessador() string {
	// Inicializar COM para WMI
	err := ole.CoInitializeEx(0, ole.COINIT_MULTITHREADED)
	if err != nil {
		return obterInfoProcessadorFallback()
	}
	defer ole.CoUninitialize()

	unknown := "Desconhecido"
	
	// Conectar ao serviço WMI
	wmi, err := oleutil.CreateObject("WbemScripting.SWbemLocator")
	if err != nil {
		return obterInfoProcessadorFallback()
	}
	defer wmi.Release()

	wmiIDispatch, err := wmi.QueryInterface(ole.IID_IDispatch)
	if err != nil {
		return obterInfoProcessadorFallback()
	}
	defer wmiIDispatch.Release()

	// Conectar ao namespace root\cimv2
	serviceRaw, err := oleutil.CallMethod(wmiIDispatch, "ConnectServer", ".", "root\\cimv2")
	if err != nil {
		return obterInfoProcessadorFallback()
	}
	service := serviceRaw.ToIDispatch()
	defer service.Release()

	// Consultar informações do processador
	resultsRaw, err := oleutil.CallMethod(service, "ExecQuery", "SELECT * FROM Win32_Processor")
	if err != nil {
		return obterInfoProcessadorFallback()
	}
	results := resultsRaw.ToIDispatch()
	defer results.Release()

	// Processar resultados
	countVar, err := oleutil.GetProperty(results, "Count")
	if err != nil {
		return obterInfoProcessadorFallback()
	}
	count := int(countVar.Val)

	if count > 0 {
		// Obter o primeiro processador
		itemRaw, err := oleutil.CallMethod(results, "ItemIndex", 0)
		if err != nil {
			return obterInfoProcessadorFallback()
		}
		item := itemRaw.ToIDispatch()
		defer item.Release()

		// Obter propriedades do processador
		manufacturerRaw, err := oleutil.GetProperty(item, "Manufacturer")
		manufacturer := unknown
		if err == nil {
			manufacturer = manufacturerRaw.ToString()
			if strings.Contains(strings.ToLower(manufacturer), "intel") {
				manufacturer = "Intel"
			} else if strings.Contains(strings.ToLower(manufacturer), "amd") {
				manufacturer = "AMD"
			}
		}

		nameRaw, err := oleutil.GetProperty(item, "Name")
		name := unknown
		if err == nil {
			name = nameRaw.ToString()
		}

		coresRaw, err := oleutil.GetProperty(item, "NumberOfCores")
		cores := unknown
		if err == nil {
			cores = fmt.Sprintf("%d", int(coresRaw.Val))
		}

		threadsRaw, err := oleutil.GetProperty(item, "NumberOfLogicalProcessors")
		threads := unknown
		if err == nil {
			threads = fmt.Sprintf("%d", int(threadsRaw.Val))
		}

		// Identificar geração para processadores Intel
		geracao := "Não identificada"
		if strings.Contains(strings.ToLower(manufacturer), "intel") && name != unknown {
			nameLower := strings.ToLower(name)
			if strings.Contains(nameLower, "core") {
				// Verificar se contém a geração no nome (ex: "12th Gen")
				if strings.Contains(nameLower, "gen") {
					parts := strings.Split(nameLower, " ")
					for _, part := range parts {
						if strings.Contains(part, "gen") && len(part) > 0 && part[0] >= '0' && part[0] <= '9' {
							numGen := ""
							for _, c := range part {
								if c >= '0' && c <= '9' {
									numGen += string(c)
								}
							}
							if numGen != "" {
								geracao = fmt.Sprintf("%sª Geração", numGen)
								break
							}
						}
					}
				} else if strings.Contains(nameLower, "i3") || strings.Contains(nameLower, "i5") || 
					strings.Contains(nameLower, "i7") || strings.Contains(nameLower, "i9") {
					// Tentar extrair o número da geração do modelo
					parts := strings.Split(name, "-")
					if len(parts) > 1 {
						modelNum := strings.TrimSpace(parts[1])
						if len(modelNum) >= 4 {
							// Para processadores mais recentes (10ª geração ou superior)
							if len(modelNum) >= 2 && modelNum[0] >= '1' && modelNum[0] <= '9' && modelNum[1] >= '0' && modelNum[1] <= '9' {
								geracao = fmt.Sprintf("%sª Geração", modelNum[0:2])
							} else if modelNum[0] >= '1' && modelNum[0] <= '9' {
								// Para processadores mais antigos (1ª a 9ª geração)
								geracao = fmt.Sprintf("%sª Geração", string(modelNum[0]))
							}
						}
					}
				}
			}
		}

		// Formatar saída detalhada
		infoDetalhada := fmt.Sprintf("Fabricante: %s\n", manufacturer)
		infoDetalhada += fmt.Sprintf("Modelo: %s\n", name)
		if geracao != "Não identificada" {
			infoDetalhada += fmt.Sprintf("Geração: %s\n", geracao)
		}
		infoDetalhada += fmt.Sprintf("Núcleos: %s\n", cores)
		infoDetalhada += fmt.Sprintf("Threads: %s\n", threads)

		// Adicionar informações de utilização
		cpuPercent, err := cpu.Percent(time.Second, false)
		if err == nil && len(cpuPercent) > 0 {
			infoDetalhada += fmt.Sprintf("Utilização atual: %.2f%%", cpuPercent[0])
		}

		return infoDetalhada
	}

	return obterInfoProcessadorFallback()
}

// obterInfoProcessadorFallback é um método alternativo para obter informações do processador
func obterInfoProcessadorFallback() string {
	info, err := cpu.Info()
	if err != nil || len(info) == 0 {
		return "Informações do processador não disponíveis"
	}

	cpuInfo := info[0]
	cpuPercent, _ := cpu.Percent(time.Second, false)
	
	utilization := 0.0
	if len(cpuPercent) > 0 {
		utilization = cpuPercent[0]
	}

	return fmt.Sprintf("%s %s, %d núcleos, %.2f%% utilização", 
		cpuInfo.VendorID, cpuInfo.ModelName, cpuInfo.Cores, utilization)
}

// ObterInfoDisco retorna informações detalhadas dos discos
func ObterInfoDisco() string {
	// Inicializar COM para WMI
	err := ole.CoInitializeEx(0, ole.COINIT_MULTITHREADED)
	if err != nil {
		return obterInfoDiscoFallback()
	}
	defer ole.CoUninitialize()

	unknown := "Desconhecido"
	
	// Conectar ao serviço WMI
	wmi, err := oleutil.CreateObject("WbemScripting.SWbemLocator")
	if err != nil {
		return obterInfoDiscoFallback()
	}
	defer wmi.Release()

	wmiIDispatch, err := wmi.QueryInterface(ole.IID_IDispatch)
	if err != nil {
		return obterInfoDiscoFallback()
	}
	defer wmiIDispatch.Release()

	// Conectar ao namespace root\cimv2
	serviceRaw, err := oleutil.CallMethod(wmiIDispatch, "ConnectServer", ".", "root\\cimv2")
	if err != nil {
		return obterInfoDiscoFallback()
	}
	service := serviceRaw.ToIDispatch()
	defer service.Release()

	// Consultar informações dos discos físicos
	resultsRaw, err := oleutil.CallMethod(service, "ExecQuery", "SELECT * FROM Win32_DiskDrive")
	if err != nil {
		return obterInfoDiscoFallback()
	}
	results := resultsRaw.ToIDispatch()
	defer results.Release()

	// Processar resultados
	countVar, err := oleutil.GetProperty(results, "Count")
	if err != nil {
		return obterInfoDiscoFallback()
	}
	count := int(countVar.Val)

	if count > 0 {
		discosDetalhes := []string{}

		// Informações básicas do disco principal via gopsutil
		partitions, err := disk.Partitions(false)
		usageInfo := ""
		if err == nil && len(partitions) > 0 {
			usage, err := disk.Usage(partitions[0].Mountpoint)
			if err == nil {
				totalGB := float64(usage.Total) / (1024 * 1024 * 1024)
				usadoGB := float64(usage.Used) / (1024 * 1024 * 1024)
				usageInfo = fmt.Sprintf("Disco principal: %.2f GB / %.2f GB (%.1f%% usado)", 
					usadoGB, totalGB, usage.UsedPercent)
			}
		}

		// Enumerar cada disco
		for i := 0; i < count; i++ {
			itemRaw, err := oleutil.CallMethod(results, "ItemIndex", i)
			if err != nil {
				continue
			}
			item := itemRaw.ToIDispatch()

			// Obter propriedades do disco
			modelRaw, _ := oleutil.GetProperty(item, "Model")
			model := unknown
			if modelRaw.Value() != nil {
				model = modelRaw.ToString()
			}

			manufacturerRaw, _ := oleutil.GetProperty(item, "Manufacturer")
			manufacturer := unknown
			if manufacturerRaw.Value() != nil {
				manufacturer = manufacturerRaw.ToString()
			}

			sizeRaw, _ := oleutil.GetProperty(item, "Size")
			sizeGB := 0.0
			if sizeRaw.Value() != nil {
				size := sizeRaw.ToString()
				if s, err := strconv.ParseUint(size, 10, 64); err == nil {
					sizeGB = float64(s) / (1024 * 1024 * 1024)
				}
			}

			interfaceTypeRaw, _ := oleutil.GetProperty(item, "InterfaceType")
			interfaceType := unknown
			if interfaceTypeRaw.Value() != nil {
				interfaceType = interfaceTypeRaw.ToString()
			}

			// Determinar se é SSD ou HDD
			tipoDisco := "Não identificado"
			modelLower := strings.ToLower(model)
			if strings.Contains(modelLower, "ssd") || 
			   strings.Contains(modelLower, "solid") || 
			   strings.Contains(modelLower, "nvme") || 
			   strings.Contains(modelLower, "flash") || 
			   strings.Contains(modelLower, "m.2") {
				tipoDisco = "SSD"
			} else if strings.Contains(modelLower, "hdd") || 
					  strings.Contains(modelLower, "hard") {
				tipoDisco = "HDD"
			}

			// Formatar informações do disco
			infoDisco := fmt.Sprintf("Disco: %s\n", model)
			infoDisco += fmt.Sprintf("Fabricante: %s\n", manufacturer)
			infoDisco += fmt.Sprintf("Tipo: %s\n", tipoDisco)
			infoDisco += fmt.Sprintf("Interface: %s\n", interfaceType)
			if sizeGB > 0 {
				infoDisco += fmt.Sprintf("Capacidade: %.2f GB", sizeGB)
			}

			discosDetalhes = append(discosDetalhes, infoDisco)
			item.Release()
		}

		// Formatar a saída com as informações detalhadas
		if len(discosDetalhes) > 0 {
			detalhes := "\n\n" + strings.Join(discosDetalhes, "\n\n")
			if usageInfo != "" {
				return usageInfo + detalhes
			}
			return detalhes
		}
	}

	return obterInfoDiscoFallback()
}

// obterInfoDiscoFallback é um método alternativo para obter informações do disco
func obterInfoDiscoFallback() string {
	partitions, err := disk.Partitions(false)
	if err != nil || len(partitions) == 0 {
		return "Informações de disco não disponíveis"
	}

	var result strings.Builder
	for i, partition := range partitions {
		usage, err := disk.Usage(partition.Mountpoint)
		if err != nil {
			continue
		}

		totalGB := float64(usage.Total) / (1024 * 1024 * 1024)
		usadoGB := float64(usage.Used) / (1024 * 1024 * 1024)
		
		if i > 0 {
			result.WriteString("\n")
		}
		result.WriteString(fmt.Sprintf("Disco %s: %.2f GB / %.2f GB (%.1f%% usado)", 
			partition.Device, usadoGB, totalGB, usage.UsedPercent))
	}

	return result.String()
}

// ObterInfoRam retorna informações detalhadas da memória RAM
func ObterInfoRam() string {
	// Inicializar COM para WMI
	err := ole.CoInitializeEx(0, ole.COINIT_MULTITHREADED)
	if err != nil {
		return obterInfoRamFallback()
	}
	defer ole.CoUninitialize()

	unknown := "Desconhecido"
	
	// Conectar ao serviço WMI
	wmi, err := oleutil.CreateObject("WbemScripting.SWbemLocator")
	if err != nil {
		return obterInfoRamFallback()
	}
	defer wmi.Release()

	wmiIDispatch, err := wmi.QueryInterface(ole.IID_IDispatch)
	if err != nil {
		return obterInfoRamFallback()
	}
	defer wmiIDispatch.Release()

	// Conectar ao namespace root\cimv2
	serviceRaw, err := oleutil.CallMethod(wmiIDispatch, "ConnectServer", ".", "root\\cimv2")
	if err != nil {
		return obterInfoRamFallback()
	}
	service := serviceRaw.ToIDispatch()
	defer service.Release()

	// Informações básicas de uso da RAM via gopsutil
	ramInfo, err := mem.VirtualMemory()
	usoInfo := ""
	if err == nil {
		totalGB := float64(ramInfo.Total) / (1024 * 1024 * 1024)
		usadoGB := float64(ramInfo.Used) / (1024 * 1024 * 1024)
		usoInfo = fmt.Sprintf("%.2f GB / %.2f GB (%.1f%% usado)", 
			usadoGB, totalGB, ramInfo.UsedPercent)
	}

	// Consultar informações detalhadas dos módulos de memória
	resultsRaw, err := oleutil.CallMethod(service, "ExecQuery", "SELECT * FROM Win32_PhysicalMemory")
	if err != nil {
		return obterInfoRamFallback()
	}
	results := resultsRaw.ToIDispatch()
	defer results.Release()

	// Mapeamento de tipos de memória
	tiposMemoria := map[int]string{
		0: "Desconhecido", 1: "Outro", 2: "DRAM", 3: "EDRAM",
		4: "VRAM", 5: "SRAM", 6: "RAM", 7: "ROM",
		8: "Flash", 9: "EEPROM", 10: "FEPROM", 11: "EPROM",
		12: "CDRAM", 13: "3DRAM", 14: "SDRAM", 15: "SGRAM",
		16: "RDRAM", 17: "DDR", 18: "DDR2", 19: "DDR2 FB-DIMM",
		20: "DDR3", 21: "FBD2", 22: "DDR4", 23: "LPDDR",
		24: "LPDDR2", 25: "LPDDR3", 26: "LPDDR4", 27: "DDR5",
	}

	// Processar resultados
	countVar, err := oleutil.GetProperty(results, "Count")
	if err != nil {
		return obterInfoRamFallback()
	}
	count := int(countVar.Val)

	if count > 0 {
		ramDetalhes := []string{}

		// Enumerar cada módulo de memória
		for i := 0; i < count; i++ {
			itemRaw, err := oleutil.CallMethod(results, "ItemIndex", i)
			if err != nil {
				continue
			}
			item := itemRaw.ToIDispatch()

			// Obter propriedades do módulo
			capacityRaw, _ := oleutil.GetProperty(item, "Capacity")
			capacidadeGB := 0.0
			if capacityRaw.Value() != nil {
				capacity := capacityRaw.ToString()
				if c, err := strconv.ParseUint(capacity, 10, 64); err == nil {
					capacidadeGB = float64(c) / (1024 * 1024 * 1024)
				}
			}

			clockSpeedRaw, _ := oleutil.GetProperty(item, "ConfiguredClockSpeed")
			frequencia := unknown
			if clockSpeedRaw.Value() != nil {
				clockSpeed := int(clockSpeedRaw.Val)
				if clockSpeed > 0 {
					frequencia = fmt.Sprintf("%d MHz", clockSpeed)
				}
			}

			manufacturerRaw, _ := oleutil.GetProperty(item, "Manufacturer")
			fabricante := unknown
			if manufacturerRaw.Value() != nil {
				fabricante = manufacturerRaw.ToString()
				// Limpar o fabricante se for apenas números
				if _, err := strconv.Atoi(fabricante); err == nil {
					fabricante = "Não identificado"
				}
			}

			memoryTypeRaw, _ := oleutil.GetProperty(item, "SMBIOSMemoryType")
			tipoMemoria := unknown
			if memoryTypeRaw.Value() != nil {
				memoryType := int(memoryTypeRaw.Val)
				if tipo, ok := tiposMemoria[memoryType]; ok {
					tipoMemoria = tipo
				}
			}

			partNumberRaw, _ := oleutil.GetProperty(item, "PartNumber")
			partNumber := unknown
			if partNumberRaw.Value() != nil {
				partNumber = strings.TrimSpace(partNumberRaw.ToString())
			}

			// Formatar informações do módulo
			infoModulo := fmt.Sprintf("Módulo: %.2f GB\n", capacidadeGB)
			infoModulo += fmt.Sprintf("Frequência: %s\n", frequencia)
			infoModulo += fmt.Sprintf("Fabricante: %s\n", fabricante)
			infoModulo += fmt.Sprintf("Tipo: %s\n", tipoMemoria)
			infoModulo += fmt.Sprintf("Part Number: %s", partNumber)

			ramDetalhes = append(ramDetalhes, infoModulo)
			item.Release()
		}

		// Formatar a saída com as informações detalhadas
		if len(ramDetalhes) > 0 {
			detalhes := "\n\n" + strings.Join(ramDetalhes, "\n\n")
			if usoInfo != "" {
				return usoInfo + detalhes
			}
			return detalhes
		}
	}

	return obterInfoRamFallback()
}

// obterInfoRamFallback é um método alternativo para obter informações da RAM
func obterInfoRamFallback() string {
	ramInfo, err := mem.VirtualMemory()
	if err != nil {
		return "Informações de memória RAM não disponíveis"
	}

	totalGB := float64(ramInfo.Total) / (1024 * 1024 * 1024)
	usadoGB := float64(ramInfo.Used) / (1024 * 1024 * 1024)
	
	return fmt.Sprintf("%.2f GB / %.2f GB (%.1f%% usado)", 
		usadoGB, totalGB, ramInfo.UsedPercent)
}

// ObterInfoMonitores retorna informações detalhadas dos monitores conectados
func ObterInfoMonitores() []string {
	// Criar arquivo temporário para o script PowerShell
	tempDir := os.TempDir()
	scriptPath := filepath.Join(tempDir, "coletar_monitores.ps1")

	// Conteúdo do script PowerShell
	scriptContent := `
# Script para coletar informações dos monitores conectados
$ErrorActionPreference = "Stop"

function Get-MonitorInfo {
    try {
        # Usar WMI para obter informações dos monitores
        $monitors = Get-WmiObject WmiMonitorID -Namespace root\wmi
        $results = @()

        foreach ($monitor in $monitors) {
            # Decodificar as informações do monitor
            $manufacturer = $null
            if ($monitor.ManufacturerName) {
                $manufacturer = [System.Text.Encoding]::ASCII.GetString($monitor.ManufacturerName).Trim(0)
            }

            $name = $null
            if ($monitor.UserFriendlyName) {
                $name = [System.Text.Encoding]::ASCII.GetString($monitor.UserFriendlyName).Trim(0)
            }

            $serialNumber = $null
            if ($monitor.SerialNumberID) {
                $serialNumber = [System.Text.Encoding]::ASCII.GetString($monitor.SerialNumberID).Trim(0)
            }

            # Obter informações adicionais como resolução
            $size = "Desconhecido"
            try {
                $monitorInfo = Get-WmiObject WmiMonitorBasicDisplayParams -Namespace root\wmi | Where-Object { $_.InstanceName -eq $monitor.InstanceName }
                if ($monitorInfo) {
                    $maxHorizontal = $monitorInfo.MaxHorizontalImageSize
                    $maxVertical = $monitorInfo.MaxVerticalImageSize

                    # Calcular tamanho diagonal em polegadas (WMI retorna em cm)
                    if ($maxHorizontal -gt 0 -and $maxVertical -gt 0) {
                        $diagonalInches = [Math]::Round([Math]::Sqrt([Math]::Pow($maxHorizontal, 2) + [Math]::Pow($maxVertical, 2)) / 2.54, 1)
                        $size = "$diagonalInches\""
                    }
                }
            } catch {
                # Ignorar erro se não conseguir obter o tamanho
            }

            # Formatar as informações
            $info = "Monitor: "
            if ($manufacturer) { $info += "$manufacturer " }
            if ($name) { $info += "$name" }
            if (-not $manufacturer -and -not $name) { $info += "Desconhecido" }
            
            $info += ", Tamanho: $size"
            if ($serialNumber) { $info += ", S/N: $serialNumber" }
            
            $results += $info
        }

        # Se não encontrou monitores, retornar mensagem padrão
        if ($results.Count -eq 0) {
            $results += "Nenhum monitor detectado"
        }

        return $results
    } catch {
        return @("Erro ao obter informações dos monitores: $_")
    }
}

# Executar a função e retornar os resultados
Get-MonitorInfo
`

	// Escrever o script no arquivo temporário
	err := os.WriteFile(scriptPath, []byte(scriptContent), 0644)
	if err != nil {
		return []string{"Erro ao criar script para coletar informações dos monitores"}
	}

	// Executar o script PowerShell
	cmd := exec.Command("powershell", "-ExecutionPolicy", "Bypass", "-File", scriptPath)
	output, err := cmd.Output()
	if err != nil {
		return []string{"Erro ao executar script para coletar informações dos monitores"}
	}

	// Processar a saída
	result := strings.Split(strings.TrimSpace(string(output)), "\r\n")
	if len(result) == 0 {
		return []string{"Nenhum monitor detectado"}
	}

	return result
}
