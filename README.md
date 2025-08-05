# Sistema de Coleta de Inventário de Hardware

Este sistema permite coletar, armazenar e visualizar informações de hardware de computadores em uma organização. O sistema é composto por um servidor Node.js para gerenciar a API e interface web, e um coletor Python que pode ser distribuído como executável.

## Estrutura do Projeto

```
projeto-inventario/
├── server/             # Servidor Node.js
│   ├── config/         # Configurações do servidor
│   ├── public/         # Arquivos estáticos (HTML, CSS, JS)
│   └── index.js        # Arquivo principal do servidor
├── coletor-python/     # Coletor em Python
│   ├── venv/           # Ambiente virtual Python
│   ├── coletor.py      # Script principal do coletor
│   └── empacotar.py    # Script para empacotar o executável
└── builds/             # Diretório para o executável compilado
```

## Requisitos

### Servidor
- Node.js 14+
- MySQL 5.7+

### Coletor
- Python 3.7+
- Bibliotecas: psutil, inquirer, requests, pyinstaller

## Configuração

### Banco de Dados
1. Certifique-se de que o MySQL esteja instalado e em execução
2. As credenciais padrão são:
   - Host: localhost
   - Usuário: root
   - Senha: (em branco)
   - Banco de dados: inventario_hardware
3. O servidor criará automaticamente o banco de dados e a tabela necessária

### Servidor
1. Navegue até o diretório `server`
2. Instale as dependências: `npm install`
3. Inicie o servidor: `node index.js`
4. O servidor estará disponível em: http://localhost:3000

### Coletor
1. Navegue até o diretório `coletor-python`
2. Ative o ambiente virtual:
   - Windows: `.\venv\Scripts\activate`
   - Linux/Mac: `source venv/bin/activate`
3. Para empacotar o coletor em um executável:
   - Execute: `python empacotar.py`
   - O executável será gerado no diretório `builds`

## Uso

### Interface Web
1. Acesse http://localhost:3000 no navegador
2. Na página inicial, você pode:
   - Baixar o coletor de dados
   - Acessar a visualização de dados

### Coletor de Dados
1. Execute o arquivo `coletor.exe` no computador onde deseja coletar informações
2. O coletor detectará automaticamente as informações de hardware
3. Preencha as informações adicionais solicitadas:
   - Secretaria
   - Setor
   - Matrícula
   - Nome Completo
4. Os dados serão enviados automaticamente para o servidor

### Visualização de Dados
1. Acesse http://localhost:3000/dados no navegador
2. Você pode:
   - Visualizar todos os registros coletados
   - Filtrar por secretaria, setor ou nome
   - Exportar os dados para Excel

## Personalização

### Configuração do Servidor
- Edite o arquivo `server/config/db.js` para alterar as configurações do banco de dados
- A porta padrão do servidor é 3000, mas pode ser alterada através da variável de ambiente PORT

### Configuração do Coletor
- Edite o arquivo `coletor-python/coletor.py` para personalizar:
  - URL do servidor (variável SERVER_URL)
  - Lista de secretarias disponíveis
  - Informações adicionais a serem coletadas

## Solução de Problemas

### Servidor
- Verifique se o MySQL está em execução
- Confirme se as credenciais do banco de dados estão corretas
- Verifique os logs do servidor para mensagens de erro

### Coletor
- Certifique-se de que o servidor esteja em execução antes de enviar dados
- Se estiver usando um servidor remoto, atualize a variável SERVER_URL no arquivo coletor.py
- Execute o coletor como administrador se necessário para acessar informações de hardware
