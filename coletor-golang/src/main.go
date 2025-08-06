package main

import (
	"encoding/json"
	"fmt"
	"log"
	"os"
	"path/filepath"
	"runtime"
	"time"

	"coletor-golang/src/hardware"
	"coletor-golang/src/server"
	"coletor-golang/src/ui"
)

// Configuração
const (
	SERVER_BASE_URL = "http://localhost:3000"
	SERVER_URL      = SERVER_BASE_URL + "/api/hardware-data"
	VERIFICAR_URL   = SERVER_BASE_URL + "/api/verificar-cadastro/"
)

// Estrutura para armazenar os dados coletados
type DadosHardware struct {
	UsuarioLogado      string   `json:"usuarioLogado"`
	NomeDispositivo    string   `json:"nomeDispositivo"`
	Processador        string   `json:"processador"`
	Disco              string   `json:"disco"`
	Ram                string   `json:"ram"`
	Monitores          []string `json:"monitores"`
	SistemaOperacional string   `json:"sistemaOperacional"`
	Secretaria         string   `json:"secretaria,omitempty"`
	Setor              string   `json:"setor,omitempty"`
	Matricula          string   `json:"matricula,omitempty"`
	Nome               string   `json:"nome,omitempty"`
	Observacoes        string   `json:"observacoes,omitempty"`
	DataColeta         string   `json:"dataColeta,omitempty"`
}

func main() {
	log.Println("Iniciando coleta de dados de hardware...")

	// Coletar dados de hardware
	dadosHardware := coletarDadosHardware()

	// A lógica de exibir o formulário e processar os dados agora está encapsulada em ExibirFormulario
	// que irá bloquear a thread principal até que a UI seja fechada.
	ui.ExibirFormulario(dadosHardware, func(dadosCompletos map[string]interface{}) {
		processarDados(dadosCompletos)
	})
}

func processarDados(dadosCompletos map[string]interface{}) {
	// Adicionar data e hora da coleta
	dadosCompletos["dataColeta"] = time.Now().Format("2006-01-02 15:04:05")

	// Verificar se já existe cadastro
	nomeDispositivo := dadosCompletos["nomeDispositivo"].(string)
	matricula := dadosCompletos["matricula"].(string)
	resultado, err := server.VerificarCadastroExistente(VERIFICAR_URL, nomeDispositivo, matricula)
	if err != nil {
		ui.MostrarMensagemErro("Erro ao verificar cadastro",
			"Não foi possível verificar se o cadastro já existe: "+err.Error())
		return
	}

	if resultado["jaExiste"].(bool) {
		mensagem := ""
		if resultado["maquinaExiste"].(bool) && resultado["matriculaExiste"].(bool) {
			mensagem = "Esta máquina e esta matrícula já estão registradas no sistema."
		} else if resultado["maquinaExiste"].(bool) {
			mensagem = "Esta máquina já está registrada no sistema."
		} else if resultado["matriculaExiste"].(bool) {
			mensagem = "Esta matrícula já está registrada no sistema."
		}
		ui.MostrarMensagemErro("Cadastro existente", mensagem+" Não é possível cadastrar novamente.")
		return
	}

	// Enviar dados para o servidor
	sucesso, mensagem := server.EnviarDados(SERVER_URL, dadosCompletos)
	if sucesso {
		ui.MostrarMensagemSucesso("Sucesso", mensagem)
	} else {
		ui.MostrarMensagemErro("Erro", mensagem)
	}
}

func coletarDadosHardware() map[string]interface{} {
	// Coletar informações do sistema
	usuarioLogado := hardware.ObterUsuarioLogado()
	nomeDispositivo := hardware.ObterNomeDispositivo()
	processador := hardware.ObterInfoProcessador()
	disco := hardware.ObterInfoDisco()
	ram := hardware.ObterInfoRam()
	monitores := hardware.ObterInfoMonitores()
	sistemaOperacional := fmt.Sprintf("%s %s", runtime.GOOS, runtime.GOARCH)

	// Criar mapa com os dados coletados
	dados := map[string]interface{}{
		"usuarioLogado":      usuarioLogado,
		"nomeDispositivo":    nomeDispositivo,
		"processador":        processador,
		"disco":              disco,
		"ram":                ram,
		"monitores":          monitores,
		"sistemaOperacional": sistemaOperacional,
	}

	// Salvar dados em arquivo temporário (para debug)
	if os.Getenv("DEBUG") == "1" {
		dadosJson, _ := json.MarshalIndent(dados, "", "  ")
		tempDir := os.TempDir()
		arquivoTemp := filepath.Join(tempDir, "hardware_data.json")
		os.WriteFile(arquivoTemp, dadosJson, 0644)
		log.Printf("Dados salvos em: %s", arquivoTemp)
	}

	return dados
}
