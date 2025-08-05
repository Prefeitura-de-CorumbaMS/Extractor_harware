const express = require('express');
const bodyParser = require('body-parser');
const cors = require('cors');
const path = require('path');
const fs = require('fs');
const ExcelJS = require('exceljs');
const { pool, testConnection, setupDatabase } = require('./config/db');

// Inicializar o aplicativo Express
const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(cors());
app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: true }));
app.use(express.static(path.join(__dirname, 'public')));

// Rota raiz - Página inicial
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

// Rota para download do coletor
app.get('/download/coletor.exe', (req, res) => {
  const filePath = path.join(__dirname, '..', 'builds', 'coletor.exe');
  
  // Verificar se o arquivo existe
  if (fs.existsSync(filePath)) {
    res.download(filePath);
  } else {
    res.status(404).send('Arquivo não encontrado. O coletor ainda não foi compilado.');
  }
});

// API para receber dados de hardware
app.post('/api/hardware-data', async (req, res) => {
  try {
    const { 
      secretaria, 
      setor, 
      matricula, 
      usuarioLogado,
      nomeCompleto, 
      nomeDispositivo, 
      processador, 
      disco, 
      ram, 
      monitores 
    } = req.body;
    
    // Validar dados recebidos
    if (!secretaria || !setor || !matricula || !usuarioLogado || !nomeCompleto || !nomeDispositivo) {
      return res.status(400).json({ 
        success: false, 
        message: 'Dados incompletos. Todos os campos são obrigatórios.' 
      });
    }
    
    // Inserir dados no banco de dados
    const [result] = await pool.query(
      `INSERT INTO hardware_data 
       (secretaria, setor, matricula, usuarioLogado, nomeCompleto, nomeDispositivo, processador, disco, ram, monitores) 
       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
      [secretaria, setor, matricula, usuarioLogado, nomeCompleto, nomeDispositivo, processador, disco, ram, JSON.stringify(monitores)]
    );
    
    res.status(201).json({ 
      success: true, 
      message: 'Dados de hardware registrados com sucesso!',
      id: result.insertId
    });
  } catch (error) {
    console.error('Erro ao salvar dados de hardware:', error);
    res.status(500).json({ 
      success: false, 
      message: 'Erro ao processar a requisição. Tente novamente mais tarde.' 
    });
  }
});

// API para obter todos os dados de hardware
app.get('/api/hardware-data', async (req, res) => {
  try {
    const [rows] = await pool.query('SELECT * FROM hardware_data ORDER BY dataColeta DESC');
    
    // Converter o campo monitores de JSON para objeto JavaScript
    const data = rows.map(row => ({
      ...row,
      monitores: JSON.parse(row.monitores || '[]')
    }));
    
    res.json({ success: true, data });
  } catch (error) {
    console.error('Erro ao buscar dados de hardware:', error);
    res.status(500).json({ 
      success: false, 
      message: 'Erro ao buscar dados. Tente novamente mais tarde.' 
    });
  }
});

// Rota para visualização de dados
app.get('/dados', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'dados.html'));
});

// Rota para exportar dados para Excel
app.get('/exportar-excel', async (req, res) => {
  try {
    // Buscar dados do banco
    const [rows] = await pool.query('SELECT * FROM hardware_data ORDER BY dataColeta DESC');
    
    // Criar um novo workbook
    const workbook = new ExcelJS.Workbook();
    const worksheet = workbook.addWorksheet('Inventário de Hardware');
    
    // Definir cabeçalhos
    worksheet.columns = [
      { header: 'ID', key: 'id', width: 10 },
      { header: 'Secretaria', key: 'secretaria', width: 20 },
      { header: 'Setor', key: 'setor', width: 20 },
      { header: 'Matrícula', key: 'matricula', width: 15 },
      { header: 'Nome Completo', key: 'nomeCompleto', width: 30 },
      { header: 'Nome do Dispositivo', key: 'nomeDispositivo', width: 25 },
      { header: 'Processador', key: 'processador', width: 30 },
      { header: 'Disco', key: 'disco', width: 15 },
      { header: 'RAM', key: 'ram', width: 15 },
      { header: 'Monitores', key: 'monitores', width: 40 },
      { header: 'Data da Coleta', key: 'dataColeta', width: 20 }
    ];
    
    // Estilizar cabeçalhos
    worksheet.getRow(1).font = { bold: true };
    worksheet.getRow(1).fill = {
      type: 'pattern',
      pattern: 'solid',
      fgColor: { argb: 'FFD3D3D3' }
    };
    
    // Adicionar dados
    rows.forEach(row => {
      // Formatar os monitores como string
      const monitoresStr = JSON.parse(row.monitores || '[]')
        .map(m => `${m.marca || 'N/A'} ${m.modelo || 'N/A'} ${m.tamanho || 'N/A'}`)
        .join(', ');
      
      // Formatar a data
      const data = new Date(row.dataColeta);
      const dataFormatada = data.toLocaleString('pt-BR');
      
      worksheet.addRow({
        ...row,
        monitores: monitoresStr,
        dataColeta: dataFormatada
      });
    });
    
    // Configurar resposta
    res.setHeader('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet');
    res.setHeader('Content-Disposition', 'attachment; filename=inventario_hardware.xlsx');
    
    // Escrever para o response
    await workbook.xlsx.write(res);
    res.end();
  } catch (error) {
    console.error('Erro ao exportar para Excel:', error);
    res.status(500).send('Erro ao gerar o arquivo Excel. Tente novamente mais tarde.');
  }
});

// Inicializar o servidor
async function iniciarServidor() {
  try {
    // Configurar o banco de dados
    await setupDatabase();
    
    // Iniciar o servidor
    app.listen(PORT, () => {
      console.log(`Servidor rodando na porta ${PORT}`);
      console.log(`Acesse: http://localhost:${PORT}`);
    });
  } catch (error) {
    console.error('Erro ao iniciar o servidor:', error);
    process.exit(1);
  }
}

// Iniciar o servidor
iniciarServidor();
