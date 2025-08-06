//go:build linux
// +build linux

package hardware

import (
	"bufio"
	"fmt"
	"math"
	"os"
	"os/exec"
	"os/user"
	"strconv"
	"strings"
	"time"

	"github.com/shirou/gopsutil/v3/cpu"
	"github.com/shirou/gopsutil/v3/disk"
	"github.com/shirou/gopsutil/v3/mem"
)

// ObterUsuarioLogado retorna o nome do usuário logado no sistema
func ObterUsuarioLogado() string {
	// Método 1: Usando os/user
	currentUser, err := user.Current()
	if err == nil && currentUser.Username != "" {
		return currentUser.Username
	}

	// Método 2: Usando o comando 'whoami'
	cmd := exec.Command("whoami")
	output, err := cmd.Output()
	if err == nil && len(output) > 0 {
		return strings.TrimSpace(string(output))
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
	// Tentar obter informações usando lscpu
	cmd := exec.Command("lscpu")
	output, err := cmd.Output()
	if err == nil {
		modelo := "Desconhecido"
		fabricante := "Desconhecido"
		cores := "Desconhecido"
		threads := "Desconhecido"
		freq := "Desconhecido"

		scanner := bufio.NewScanner(strings.NewReader(string(output)))
		for scanner.Scan() {
			linha := scanner.Text()
			if strings.Contains(linha, "Model name") {
				partes := strings.Split(linha, ":")
				if len(partes) > 1 {
					modelo = strings.TrimSpace(partes[1])
				}
			} else if strings.Contains(linha, "Vendor ID") {
				partes := strings.Split(linha, ":")
				if len(partes) > 1 {
					fabricante = strings.TrimSpace(partes[1])
				}
			} else if strings.Contains(linha, "CPU(s)") && cores == "Desconhecido" {
				partes := strings.Split(linha, ":")
				if len(partes) > 1 {
					cores = strings.TrimSpace(partes[1])
				}
			} else if strings.Contains(linha, "Thread(s) per core") {
				partes := strings.Split(linha, ":")
				if len(partes) > 1 {
					threadsPerCore := strings.TrimSpace(partes[1])
					if coresInt, err := strconv.Atoi(cores); err == nil {
						if threadsPerCoreInt, err := strconv.Atoi(threadsPerCore); err == nil {
							threads = strconv.Itoa(coresInt * threadsPerCoreInt)
						}
					}
				}
			} else if strings.Contains(linha, "CPU MHz") {
				partes := strings.Split(linha, ":")
				if len(partes) > 1 {
					freqStr := strings.TrimSpace(partes[1])
					if freqFloat, err := strconv.ParseFloat(freqStr, 64); err == nil {
						freq = fmt.Sprintf("%.2f GHz", freqFloat/1000)
					}
				}
			}
		}

		// Adicionar informações de utilização
		cpuPercent, err := cpu.Percent(time.Second, false)
		utilizacao := 0.0
		if err == nil && len(cpuPercent) > 0 {
			utilizacao = cpuPercent[0]
		}

		return fmt.Sprintf("%s %s, %s núcleos, %s threads, %s, %.2f%% utilização",
			fabricante, modelo, cores, threads, freq, utilizacao)
	}

	// Fallback para psutil se lscpu falhar
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
	// Tentar obter informações usando lsblk
	cmd := exec.Command("lsblk", "-d", "-o", "NAME,SIZE,MODEL,SERIAL")
	output, err := cmd.Output()
	if err == nil {
		linhas := strings.Split(strings.TrimSpace(string(output)), "\n")
		discos := []string{}

		// Pular o cabeçalho
		for i := 1; i < len(linhas); i++ {
			campos := strings.Fields(linhas[i])
			if len(campos) >= 2 {
				nome := campos[0]
				tamanho := campos[1]
				modelo := "Desconhecido"
				if len(campos) > 2 {
					modelo = strings.Join(campos[2:len(campos)-1], " ")
				}
				discos = append(discos, fmt.Sprintf("%s: %s (%s)", nome, modelo, tamanho))
			}
		}

		// Tentar determinar se é SSD ou HDD usando smartctl
		for i, disco := range discos {
			nome := strings.Split(disco, ":")[0]
			tipoCmd := exec.Command("smartctl", "-i", "/dev/"+nome)
			tipoOutput, err := tipoCmd.Output()
			if err == nil && strings.Contains(string(tipoOutput), "Solid State Device") {
				discos[i] = strings.Replace(disco, ")", ", SSD)", 1)
			} else {
				discos[i] = strings.Replace(disco, ")", ", HDD)", 1)
			}
		}

		if len(discos) > 0 {
			return strings.Join(discos, ", ")
		}
	}

	// Fallback para psutil se lsblk falhar
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
	// Informações básicas de uso da RAM via gopsutil
	ramInfo, err := mem.VirtualMemory()
	if err != nil {
		return "Informações de memória RAM não disponíveis"
	}

	totalGB := float64(ramInfo.Total) / (1024 * 1024 * 1024)
	usadoGB := float64(ramInfo.Used) / (1024 * 1024 * 1024)
	usoInfo := fmt.Sprintf("%.2f GB / %.2f GB (%.1f%% usado)",
		usadoGB, totalGB, ramInfo.UsedPercent)

	// Tentar obter informações mais detalhadas usando dmidecode
	cmd := exec.Command("sudo", "-n", "dmidecode", "-t", "17")
	output, err := cmd.Output()
	if err == nil {
		modulos := []string{}
		var modulo map[string]string

		scanner := bufio.NewScanner(strings.NewReader(string(output)))
		for scanner.Scan() {
			linha := strings.TrimSpace(scanner.Text())

			if strings.Contains(linha, "Memory Device") && linha == "Memory Device" {
				if modulo != nil && len(modulo) > 0 {
					if tamanho, ok := modulo["tamanho"]; ok && tamanho != "No Module Installed" {
						info := tamanho
						if tipo, ok := modulo["tipo"]; ok && tipo != "Unknown" {
							info += " " + tipo
						}
						if velocidade, ok := modulo["velocidade"]; ok && velocidade != "Unknown" {
							info += " " + velocidade
						}
						modulos = append(modulos, info)
					}
				}
				modulo = make(map[string]string)
			} else if modulo != nil {
				if strings.Contains(linha, "Size:") {
					modulo["tamanho"] = strings.TrimSpace(strings.Split(linha, ":")[1])
				} else if strings.Contains(linha, "Type:") {
					modulo["tipo"] = strings.TrimSpace(strings.Split(linha, ":")[1])
				} else if strings.Contains(linha, "Speed:") {
					modulo["velocidade"] = strings.TrimSpace(strings.Split(linha, ":")[1])
				}
			}
		}

		// Adicionar o último módulo
		if modulo != nil && len(modulo) > 0 {
			if tamanho, ok := modulo["tamanho"]; ok && tamanho != "No Module Installed" {
				info := tamanho
				if tipo, ok := modulo["tipo"]; ok && tipo != "Unknown" {
					info += " " + tipo
				}
				if velocidade, ok := modulo["velocidade"]; ok && velocidade != "Unknown" {
					info += " " + velocidade
				}
				modulos = append(modulos, info)
			}
		}

		if len(modulos) > 0 {
			return usoInfo + "\n\n" + strings.Join(modulos, "\n")
		}
	}

	return usoInfo
}

// ObterInfoMonitores retorna informações detalhadas dos monitores conectados
func ObterInfoMonitores() []string {
	// Verificar se o comando xrandr está disponível
	if _, err := exec.LookPath("xrandr"); err == nil {
		cmd := exec.Command("xrandr", "--verbose")
		output, err := cmd.Output()
		if err == nil {
			monitores := []string{}
			var monitorAtual map[string]string
			var edid string

			scanner := bufio.NewScanner(strings.NewReader(string(output)))
			for scanner.Scan() {
				linha := scanner.Text()

				if strings.Contains(linha, " connected ") {
					// Novo monitor encontrado
					if monitorAtual != nil {
						monitorAtual["edid"] = edid
						info := fmt.Sprintf("Monitor: %s", monitorAtual["nome"])
						if resolucao, ok := monitorAtual["resolucao"]; ok && resolucao != "Desconhecido" {
							info += fmt.Sprintf(", Resolução: %s", resolucao)
						}
						if tamanho, ok := monitorAtual["tamanho"]; ok && tamanho != "Desconhecido" {
							info += fmt.Sprintf(", Tamanho: %s", tamanho)
						}
						monitores = append(monitores, info)
					}

					nome := strings.Fields(linha)[0]
					resolucao := "Desconhecido"
					if strings.Contains(linha, "primary") {
						resolucao = strings.Fields(strings.Split(linha, "primary ")[1])[0]
					}

					monitorAtual = map[string]string{
						"nome":      nome,
						"resolucao": resolucao,
						"tamanho":   "Desconhecido",
					}
					edid = ""
				} else if monitorAtual != nil {
					if strings.Contains(linha, "EDID:") {
						edid = ""
					} else if strings.HasPrefix(linha, "\t\t") && edid != "" {
						edid += strings.TrimSpace(linha)
					} else if strings.Contains(linha, "width") && strings.Contains(linha, "height") {
						campos := strings.Fields(linha)
						for i, campo := range campos {
							if campo == "width" && i+1 < len(campos) {
								larguraMM, err := strconv.Atoi(campos[i+1])
								if err == nil && i+3 < len(campos) && campos[i+2] == "height" {
									alturaMM, err := strconv.Atoi(campos[i+3])
									if err == nil {
										diagonalMM := math.Sqrt(float64(larguraMM*larguraMM + alturaMM*alturaMM))
										diagonalPolegadas := diagonalMM / 25.4
										monitorAtual["tamanho"] = fmt.Sprintf("%.1f\"", diagonalPolegadas)
									}
								}
								break
							}
						}
					}
				}
			}

			// Adicionar o último monitor
			if monitorAtual != nil {
				monitorAtual["edid"] = edid
				info := fmt.Sprintf("Monitor: %s", monitorAtual["nome"])
				if resolucao, ok := monitorAtual["resolucao"]; ok && resolucao != "Desconhecido" {
					info += fmt.Sprintf(", Resolução: %s", resolucao)
				}
				if tamanho, ok := monitorAtual["tamanho"]; ok && tamanho != "Desconhecido" {
					info += fmt.Sprintf(", Tamanho: %s", tamanho)
				}
				monitores = append(monitores, info)
			}

			if len(monitores) > 0 {
				return monitores
			}
		}
	}

	return []string{"Informações de monitores não disponíveis"}
}
