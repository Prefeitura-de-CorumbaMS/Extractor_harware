package ui

import (
	"encoding/json"
	"fmt"
	"log"

	webview "github.com/webview/webview_go"
)

// Campos do formulário
type FormFields struct {
	Secretaria  string
	Setor       string
	Matricula   string
	Nome        string
	Observacoes string
}

// ExibirFormulario exibe o formulário para coleta de informações adicionais
func ExibirFormulario(dadosHardware map[string]interface{}, processarDados func(map[string]interface{})) {
	done := make(chan struct{})

	html := getFormHTML()

	w := webview.New(true)
	defer w.Destroy()
	w.SetTitle("Formulário de Coleta")
	w.SetSize(800, 650, webview.HintNone)
	w.SetHtml(html)

	// Bind Go function to be callable from JS
	w.Bind("external", func(msg string) {
		var req struct {
			Action string                 `json:"action"`
			Data   map[string]interface{} `json:"data"`
		}
		if err := json.Unmarshal([]byte(msg), &req); err != nil {
			log.Printf("Error processing form data: %v", err)
			log.Println("Dados do formulário recebidos:", req.Data)
			go processarDados(req.Data)
			return
		}

		switch req.Action {
		case "submit":
			go processarDados(req.Data)
			close(done)
		case "cancel":
			accepted = false
			w.Terminate()
		}
	})

	// This needs to be run in the main OS thread, so we handle it in main.go
	// For now, we just prepare it. The actual blocking call will be in main.
	go func() {
		w.Run()
		close(done)
	}()

	<-done
	return dadosHardware, accepted
}

// showMessage displays a generic message window.
func showMessage(title, header, message, buttonClass string) {
	html := fmt.Sprintf(`
	<!DOCTYPE html>
	<html>
	<head>
		<meta charset="UTF-8">
		<title>%s</title>
		<style>
			body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; text-align: center; }
			.container { max-width: 400px; margin: 0 auto; background-color: white; padding: 20px; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
			h2 { color: #333; }
			.message { margin: 20px 0; }
			button { padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; font-size: 16px; color: white; }
			.success { background-color: #4CAF50; }
			.error { background-color: #f44336; }
		</style>
	</head>
	<body>
		<div class="container">
			<h2>%s</h2>
			<div class="message">%s</div>
			<button class="%s" onclick="window.external.invoke('close')">OK</button>
		</div>
	</body>
	</html>
	`, title, header, message, buttonClass)

	w := webview.New(true)
	defer w.Destroy()
	w.SetTitle(title)
	w.SetSize(400, 250, webview.HintNone)
	w.SetHtml(html)

	w.Bind("external", func(msg string) {
		if msg == "close" {
			w.Terminate()
		}
	})

	w.Run()
}

// MostrarMensagemSucesso displays a success message.
func MostrarMensagemSucesso(titulo, mensagem string) {
	showMessage(titulo, titulo, mensagem, "success")
}

// MostrarMensagemErro displays an error message.
func MostrarMensagemErro(titulo, mensagem string) {
	showMessage(titulo, titulo, mensagem, "error")
}

// getFormHTML returns the HTML content for the main form.
func getFormHTML() string {
	return `
        <!DOCTYPE html>
        <html>
        <head>
                <meta charset="UTF-8">
                <title>Formulário de Coleta</title>
                <style>
                        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }
                        .container { max-width: 600px; margin: 0 auto; background-color: white; padding: 20px; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
                        h1 { text-align: center; color: #333; }
                        .form-group { margin-bottom: 15px; }
                        label { display: block; margin-bottom: 5px; font-weight: bold; }
                        input, textarea { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; box-sizing: border-box; }
                        textarea { height: 100px; }
                        .buttons { text-align: center; margin-top: 20px; }
                        button { padding: 10px 20px; margin: 0 10px; border: none; border-radius: 4px; cursor: pointer; font-size: 16px; }
                        .submit { background-color: #4CAF50; color: white; }
                        .cancel { background-color: #f44336; color: white; }
                        .error { color: red; text-align: center; margin-bottom: 10px; display: none; }
                </style>
        </head>
        <body>
                <div class="container">
                        <h1>PREENCHA AS INFORMAÇÕES ABAIXO</h1>
                        <div id="error-message" class="error"></div>
                        <form id="coleta-form">
                                <div class="form-group">
                                        <label for="secretaria">Secretaria:</label>
                                        <input type="text" id="secretaria" name="secretaria" required>
                                </div>
                                <div class="form-group">
                                        <label for="setor">Setor:</label>
                                        <input type="text" id="setor" name="setor" required>
                                </div>
                                <div class="form-group">
                                        <label for="matricula">Matrícula:</label>
                                        <input type="text" id="matricula" name="matricula" required>
                                </div>
                                <div class="form-group">
                                        <label for="nome">Nome:</label>
                                        <input type="text" id="nome" name="nome" required>
                                </div>
                                <div class="form-group">
                                        <label for="observacoes">Observações:</label>
                                        <textarea id="observacoes" name="observacoes"></textarea>
                                </div>
                                <div class="buttons">
                                        <button type="submit" class="submit">Enviar</button>
                                        <button type="button" class="cancel">Cancelar</button>
                                </div>
                        </form>
                </div>
                <script>
                        document.getElementById('coleta-form').addEventListener('submit', function(e) {
                                e.preventDefault();
                                const secretaria = document.getElementById('secretaria').value;
                                const setor = document.getElementById('setor').value;
                                const matricula = document.getElementById('matricula').value;
                                const nome = document.getElementById('nome').value;
                                if (!secretaria || !setor || !matricula || !nome) {
                                        const errorMsg = document.getElementById('error-message');
                                        errorMsg.textContent = 'Todos os campos são obrigatórios!';
                                        errorMsg.style.display = 'block';
                                        return;
                                }
                                const formData = {
                                        secretaria: secretaria,
                                        setor: setor,
                                        matricula: matricula,
                                        nome: nome,
                                        observacoes: document.getElementById('observacoes').value
                                };
                                window.external.invoke(JSON.stringify({ action: 'submit', data: formData }));
                        });
                        document.querySelector('.cancel').addEventListener('click', function() {
                                window.external.invoke(JSON.stringify({ action: 'cancel' }));
                        });
                </script>
        </body>
        </html>
        `
}
