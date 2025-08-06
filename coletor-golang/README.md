# Coletor de Hardware em Golang

Este projeto é uma reimplementação em Golang do coletor de informações de hardware originalmente desenvolvido em Python. O objetivo principal é permitir a geração de executáveis multiplataforma (Windows e Linux) para coleta de informações de hardware e envio para um servidor central.

## Funcionalidades

- Coleta de informações detalhadas de hardware:
  - Processador (fabricante, modelo, núcleos, threads)
  - Disco (tipo, tamanho, modelo)
  - Memória RAM (quantidade, tipo, fabricante)
  - Monitores conectados
  - Nome do dispositivo e usuário logado
  - Sistema operacional
- Interface gráfica para coleta de informações adicionais
- Verificação de cadastro existente no servidor
- Envio dos dados coletados para o servidor

## Requisitos

- Go 1.18 ou superior
- Dependências:
  - github.com/shirou/gopsutil/v3
  - github.com/lxn/walk (para Windows)
  - github.com/go-ole/go-ole (para Windows)

## Estrutura do Projeto

```
coletor-golang/
├── src/
│   ├── main.go            # Ponto de entrada do programa
│   ├── hardware/          # Pacote para coleta de informações de hardware
│   │   ├── hardware_windows.go  # Implementação específica para Windows
│   │   └── hardware_linux.go    # Implementação específica para Linux
│   ├── ui/                # Pacote para interface gráfica
│   │   └── ui.go          # Implementação da interface gráfica
│   └── server/            # Pacote para comunicação com o servidor
│       └── server.go      # Implementação da comunicação com o servidor
├── go.mod                 # Gerenciamento de dependências
├── go.sum                 # Checksums das dependências
├── build_windows.bat      # Script para compilar para Windows
└── build_linux.sh         # Script para compilar para Linux
```

## Compilação

### Windows

Execute o script `build_windows.bat` para compilar o projeto para Windows:

```
.\build_windows.bat
```

O executável será gerado na pasta `builds` com o nome `TesteSegurancaParaNovoAntivirus_TI_GO.exe`.

### Linux

Execute o script `build_linux.sh` para compilar o projeto para Linux:

```
./build_linux.sh
```

O executável será gerado na pasta `builds` com o nome `TesteSegurancaParaNovoAntivirus_TI_GO_Linux`.

## Configuração do Servidor

Por padrão, o coletor se conecta ao servidor em `http://localhost:3000`. Para alterar essa configuração, edite as constantes no arquivo `src/main.go`:

```go
const (
    SERVER_BASE_URL = "http://localhost:3000"
    SERVER_URL      = SERVER_BASE_URL + "/api/hardware-data"
    VERIFICAR_URL   = SERVER_BASE_URL + "/api/verificar-cadastro/"
)
```

## Diferenças em Relação à Versão Python

- Implementação totalmente em Golang
- Melhor desempenho e menor tamanho de executável
- Compatibilidade nativa com Windows e Linux sem necessidade de interpretador
- Mesma interface gráfica e funcionalidades da versão Python
