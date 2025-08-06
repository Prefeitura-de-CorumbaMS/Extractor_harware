package server

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"
)

// VerificarCadastroExistente verifica se a máquina ou matrícula já está registrada no servidor
func VerificarCadastroExistente(baseURL, nomeDispositivo, matricula string) (map[string]interface{}, error) {
	url := fmt.Sprintf("%s%s/%s", baseURL, nomeDispositivo, matricula)
	
	// Criar cliente HTTP com timeout
	client := &http.Client{
		Timeout: 10 * time.Second,
	}
	
	// Fazer requisição GET
	resp, err := client.Get(url)
	if err != nil {
		return nil, fmt.Errorf("erro ao conectar ao servidor: %v", err)
	}
	defer resp.Body.Close()
	
	// Verificar status da resposta
	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("erro ao verificar cadastro. Código: %d", resp.StatusCode)
	}
	
	// Ler corpo da resposta
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("erro ao ler resposta do servidor: %v", err)
	}
	
	// Decodificar JSON
	var resultado map[string]interface{}
	err = json.Unmarshal(body, &resultado)
	if err != nil {
		return nil, fmt.Errorf("erro ao decodificar resposta do servidor: %v", err)
	}
	
	// Garantir que os campos existam
	if _, ok := resultado["jaExiste"]; !ok {
		resultado["jaExiste"] = false
	}
	if _, ok := resultado["maquinaExiste"]; !ok {
		resultado["maquinaExiste"] = false
	}
	if _, ok := resultado["matriculaExiste"]; !ok {
		resultado["matriculaExiste"] = false
	}
	
	return resultado, nil
}

// EnviarDados envia os dados coletados para o servidor
func EnviarDados(url string, dados map[string]interface{}) (bool, string) {
	// Converter dados para JSON
	dadosJSON, err := json.Marshal(dados)
	if err != nil {
		return false, fmt.Sprintf("Erro ao converter dados para JSON: %v", err)
	}
	
	// Criar cliente HTTP com timeout
	client := &http.Client{
		Timeout: 10 * time.Second,
	}
	
	// Fazer requisição POST
	resp, err := client.Post(url, "application/json", bytes.NewBuffer(dadosJSON))
	if err != nil {
		return false, fmt.Sprintf("Erro ao conectar ao servidor: %v", err)
	}
	defer resp.Body.Close()
	
	// Verificar status da resposta
	if resp.StatusCode != http.StatusCreated {
		return false, fmt.Sprintf("Erro ao enviar dados. Código: %d", resp.StatusCode)
	}
	
	// Ler corpo da resposta
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return false, fmt.Sprintf("Erro ao ler resposta do servidor: %v", err)
	}
	
	// Decodificar JSON
	var resposta map[string]interface{}
	err = json.Unmarshal(body, &resposta)
	if err != nil {
		return true, "Dados enviados com sucesso!"
	}
	
	// Verificar se há mensagem na resposta
	if mensagem, ok := resposta["message"].(string); ok {
		return true, mensagem
	}
	
	return true, "Dados enviados com sucesso!"
}
