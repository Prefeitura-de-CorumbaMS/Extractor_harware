package ui

import (
	"bufio"
	"fmt"
	"os"
	"strings"
)

// ExibirFormularioCLI exibe um formulário de linha de comando para coleta de informações adicionais
func ExibirFormularioCLI(dadosHardware map[string]interface{}) (map[string]interface{}, bool) {
	fmt.Println("\n=== FORMULÁRIO DE COLETA DE DADOS ===")
	fmt.Println("PREENCHA AS INFORMAÇÕES ABAIXO:")
	
	reader := bufio.NewReader(os.Stdin)
	
	// Coletar secretaria
	fmt.Print("Secretaria: ")
	secretaria, _ := reader.ReadString('\n')
	secretaria = strings.TrimSpace(secretaria)
	if secretaria == "" {
		fmt.Println("Erro: Secretaria é um campo obrigatório.")
		return dadosHardware, false
	}
	
	// Coletar setor
	fmt.Print("Setor: ")
	setor, _ := reader.ReadString('\n')
	setor = strings.TrimSpace(setor)
	if setor == "" {
		fmt.Println("Erro: Setor é um campo obrigatório.")
		return dadosHardware, false
	}
	
	// Coletar matrícula
	fmt.Print("Matrícula: ")
	matricula, _ := reader.ReadString('\n')
	matricula = strings.TrimSpace(matricula)
	if matricula == "" {
		fmt.Println("Erro: Matrícula é um campo obrigatório.")
		return dadosHardware, false
	}
	
	// Coletar nome
	fmt.Print("Nome: ")
	nome, _ := reader.ReadString('\n')
	nome = strings.TrimSpace(nome)
	if nome == "" {
		fmt.Println("Erro: Nome é um campo obrigatório.")
		return dadosHardware, false
	}
	
	// Coletar observações
	fmt.Print("Observações: ")
	observacoes, _ := reader.ReadString('\n')
	observacoes = strings.TrimSpace(observacoes)
	
	// Confirmar envio
	fmt.Print("\nDeseja enviar os dados? (S/N): ")
	confirmacao, _ := reader.ReadString('\n')
	confirmacao = strings.ToUpper(strings.TrimSpace(confirmacao))
	
	if confirmacao != "S" && confirmacao != "SIM" {
		fmt.Println("Operação cancelada pelo usuário.")
		return dadosHardware, false
	}
	
	// Adicionar dados ao mapa
	dadosHardware["secretaria"] = secretaria
	dadosHardware["setor"] = setor
	dadosHardware["matricula"] = matricula
	dadosHardware["nome"] = nome
	dadosHardware["observacoes"] = observacoes
	
	return dadosHardware, true
}

// MostrarMensagemSucessoCLI exibe uma mensagem de sucesso no console
func MostrarMensagemSucessoCLI(titulo, mensagem string) {
	fmt.Printf("\n=== %s ===\n%s\n\n", titulo, mensagem)
}

// MostrarMensagemErroCLI exibe uma mensagem de erro no console
func MostrarMensagemErroCLI(titulo, mensagem string) {
	fmt.Printf("\n=== ERRO: %s ===\n%s\n\n", titulo, mensagem)
}
