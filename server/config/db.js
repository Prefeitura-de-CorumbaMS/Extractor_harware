const mysql = require('mysql2/promise');

// Configuração da conexão com o banco de dados
const dbConfig = {
  host: 'localhost',
  user: 'root',
  password: 'pru',
  database: 'inventario_hardware'
};

// Criar pool de conexões
const pool = mysql.createPool(dbConfig);

// Função para testar a conexão
async function testConnection() {
  try {
    const connection = await pool.getConnection();
    console.log('Conexão com o banco de dados estabelecida com sucesso!');
    connection.release();
    return true;
  } catch (error) {
    console.error('Erro ao conectar ao banco de dados:', error);
    return false;
  }
}

// Função para criar o banco de dados e a tabela se não existirem
async function setupDatabase() {
  try {
    // Primeiro, criar o banco de dados se não existir
    const tempPool = mysql.createPool({
      host: dbConfig.host,
      user: dbConfig.user,
      password: dbConfig.password
    });
    
    await tempPool.query(`CREATE DATABASE IF NOT EXISTS ${dbConfig.database}`);
    console.log(`Banco de dados '${dbConfig.database}' verificado/criado com sucesso!`);
    
    // Agora, usar o pool principal para criar a tabela
    await pool.query(`
      CREATE TABLE IF NOT EXISTS hardware_data (
        id INT AUTO_INCREMENT PRIMARY KEY,
        secretaria VARCHAR(100) NOT NULL,
        setor VARCHAR(100) NOT NULL,
        matricula VARCHAR(20) NOT NULL,
        usuarioLogado VARCHAR(100) NOT NULL,
        nomeCompleto VARCHAR(200) NOT NULL,
        nomeDispositivo VARCHAR(100) NOT NULL,
        processador VARCHAR(200) NOT NULL,
        disco VARCHAR(100) NOT NULL,
        ram VARCHAR(100) NOT NULL,
        monitores JSON,
        dataColeta DATETIME DEFAULT CURRENT_TIMESTAMP
      )
    `);
    console.log('Tabela hardware_data verificada/criada com sucesso!');
    
    return true;
  } catch (error) {
    console.error('Erro ao configurar o banco de dados:', error);
    return false;
  }
}

module.exports = {
  pool,
  testConnection,
  setupDatabase
};
