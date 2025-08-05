#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import platform
import json
import socket
import psutil
import requests
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

# Configuração
SERVER_URL = "http://localhost:3000/api/hardware-data"

def obter_usuario_logado():
    """Obtém o nome do usuário atualmente logado na máquina."""
    try:
        if platform.system() == "Windows":
            # Método 1: Usando os.getlogin()
            try:
                return os.getlogin()
            except Exception as e:
                print(f"Erro ao obter usuário com os.getlogin(): {e}")
            
            # Método 2: Usando variáveis de ambiente
            try:
                return os.environ.get('USERNAME') or os.environ.get('USER')
            except Exception as e:
                print(f"Erro ao obter usuário das variáveis de ambiente: {e}")
            
            # Método 3: Usando PowerShell
            try:
                import subprocess
                cmd = "powershell -command \"[System.Security.Principal.WindowsIdentity]::GetCurrent().Name\""
                resultado = subprocess.check_output(cmd, shell=True, text=True)
                # Remover domínio se presente (formato: DOMINIO\usuario)
                usuario = resultado.strip()
                if '\\' in usuario:
                    usuario = usuario.split('\\')[1]
                return usuario
            except Exception as e:
                print(f"Erro ao obter usuário com PowerShell: {e}")
        
        else:  # Linux, macOS, etc.
            try:
                import pwd
                return pwd.getpwuid(os.getuid())[0]
            except Exception as e:
                print(f"Erro ao obter usuário em sistema não-Windows: {e}")
    
    except Exception as e:
        print(f"Erro ao obter usuário logado: {e}")
    
    return "Usuário desconhecido"

def obter_nome_dispositivo():
    """Obtém o nome do dispositivo."""
    return platform.node()

def obter_info_processador():
    """Obtém informações detalhadas do processador, incluindo fabricante, modelo e geração."""
    try:
        # Informações básicas via psutil
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_freq = psutil.cpu_freq()
        if cpu_freq:
            freq_atual = f"{cpu_freq.current:.2f} MHz"
            if cpu_freq.max:
                freq_max = f"{cpu_freq.max:.2f} MHz"
            else:
                freq_max = "N/A"
        else:
            freq_atual = "N/A"
            freq_max = "N/A"
        
        # Informações básicas via platform
        cpu_info_basic = platform.processor()
        
        # Informações detalhadas via WMI
        try:
            import wmi
            w = wmi.WMI()
            
            # Obter informações do processador via WMI
            for proc in w.Win32_Processor():
                # Fabricante (Intel, AMD, etc.)
                fabricante = proc.Manufacturer.strip() if proc.Manufacturer else "Não disponível"
                if "intel" in fabricante.lower():
                    fabricante = "Intel"
                elif "amd" in fabricante.lower():
                    fabricante = "AMD"
                
                # Nome completo do processador
                nome = proc.Name.strip() if proc.Name else "Não disponível"
                
                # Modelo e família
                modelo = proc.Description.strip() if proc.Description else nome
                familia = f"Família {proc.Family}" if proc.Family else "Não disponível"
                
                # Identificar geração para processadores Intel
                geracao = "Não identificada"
                if "intel" in fabricante.lower() and nome:
                    # Extrair geração de processadores Intel Core
                    if "core" in nome.lower():
                        # Verificar se contém a geração no nome (ex: "12th Gen")
                        if "gen" in nome.lower():
                            for parte in nome.lower().split():
                                if "gen" in parte and parte[0].isdigit():
                                    num_gen = ''.join(filter(str.isdigit, parte))
                                    if num_gen:
                                        geracao = f"{num_gen}ª Geração"
                                        break
                        # Se não encontrou pelo método acima, tentar pelo modelo
                        elif "i3" in nome.lower() or "i5" in nome.lower() or "i7" in nome.lower() or "i9" in nome.lower():
                            # Tentar extrair o número da geração (geralmente o primeiro ou primeiros dígitos do modelo)
                            partes = nome.split("-")
                            if len(partes) > 1:
                                num_modelo = partes[1].strip()
                                if num_modelo and len(num_modelo) >= 4:
                                    # Para processadores mais recentes (10ª geração ou superior)
                                    if num_modelo[0:2].isdigit() and int(num_modelo[0:2]) >= 10:
                                        geracao = f"{num_modelo[0:2]}ª Geração"
                                    # Para processadores mais antigos (1ª a 9ª geração)
                                    elif num_modelo[0].isdigit():
                                        geracao = f"{num_modelo[0]}ª Geração"
                
                # Número de núcleos e threads
                nucleos = proc.NumberOfCores if hasattr(proc, 'NumberOfCores') and proc.NumberOfCores else "N/A"
                threads = proc.NumberOfLogicalProcessors if hasattr(proc, 'NumberOfLogicalProcessors') and proc.NumberOfLogicalProcessors else "N/A"
                
                # Socket
                socket = proc.SocketDesignation if hasattr(proc, 'SocketDesignation') and proc.SocketDesignation else "N/A"
                
                # Arquitetura
                arquitetura = "64-bit" if proc.AddressWidth == 64 else "32-bit" if proc.AddressWidth == 32 else "N/A"
                
                # Formatar saída detalhada
                info_detalhada = f"Fabricante: {fabricante}\n"
                info_detalhada += f"Modelo: {nome}\n"
                if geracao != "Não identificada":
                    info_detalhada += f"Geração: {geracao}\n"
                info_detalhada += f"Arquitetura: {arquitetura}\n"
                info_detalhada += f"Socket: {socket}\n"
                info_detalhada += f"Núcleos: {nucleos}\n"
                info_detalhada += f"Threads: {threads}\n"
                info_detalhada += f"Frequência máxima: {freq_max}\n"
                info_detalhada += f"Utilização atual: {cpu_percent}%"
                
                return info_detalhada
            
            # Se não encontrou processador via WMI, retorna informações básicas
            return f"{cpu_info_basic} (Utilização: {cpu_percent}%, Frequência: {freq_atual})"
            
        except Exception as wmi_erro:
            print(f"Erro ao obter detalhes do processador via WMI: {wmi_erro}")
            return f"{cpu_info_basic} (Utilização: {cpu_percent}%, Frequência: {freq_atual})"
            
    except Exception as e:
        print(f"Erro ao obter informações do processador: {e}")
        return "Erro ao obter informações do processador"

def obter_info_disco():
    """Obtém informações detalhadas de todos os discos, incluindo tipo (HDD/SSD), modelo e velocidade."""
    try:
        # Informações básicas do disco principal via psutil
        disk = psutil.disk_usage('/')
        total_gb = disk.total / (1024**3)
        usado_gb = disk.used / (1024**3)
        uso_info = f"Disco principal: {usado_gb:.2f} GB / {total_gb:.2f} GB ({disk.percent}% usado)"
        
        # Informações detalhadas de todos os discos via WMI
        try:
            import wmi
            w = wmi.WMI()
            discos_detalhes = []
            
            # Coleta informações de cada disco físico
            for disco in w.Win32_DiskDrive():
                # Modelo e fabricante
                modelo = disco.Model.strip() if disco.Model else "Não disponível"
                fabricante = disco.Manufacturer.strip() if disco.Manufacturer else "Não disponível"
                
                # Tamanho
                if disco.Size:
                    tamanho_gb = int(disco.Size) / (1024**3)
                else:
                    tamanho_gb = 0
                
                # Interface (SATA, NVMe, etc.)
                interface = disco.InterfaceType if disco.InterfaceType else "Não disponível"
                
                # Determinar se é SSD ou HDD
                tipo_disco = "Não identificado"
                try:
                    # Verificar se é SSD baseado no nome do modelo ou na descrição
                    modelo_lower = modelo.lower()
                    if any(termo in modelo_lower for termo in ["ssd", "solid", "nvme", "flash", "m.2"]):
                        tipo_disco = "SSD"
                    elif "hdd" in modelo_lower or "hard" in modelo_lower:
                        tipo_disco = "HDD"
                    else:
                        # Tentar identificar pelo MediaType
                        for disk_to_partition in w.Win32_DiskDriveToDiskPartition():
                            if disk_to_partition.Antecedent.DeviceID.replace('\\\\.\\', '') == disco.DeviceID.replace('\\\\.\\', ''):
                                for partition_to_logical in w.Win32_LogicalDiskToPartition():
                                    if partition_to_logical.Antecedent.DeviceID == disk_to_partition.Dependent.DeviceID:
                                        logical_disk = w.Win32_LogicalDisk(DeviceID=partition_to_logical.Dependent.DeviceID)[0]
                                        if hasattr(logical_disk, 'MediaType'):
                                            if logical_disk.MediaType == 12:
                                                tipo_disco = "SSD"
                                            else:
                                                tipo_disco = "HDD"
                except Exception as e:
                    print(f"Erro ao determinar tipo de disco: {e}")
                
                # Velocidade de rotação (apenas para HDDs)
                velocidade = "Não disponível"
                if disco.MaxMediaSize and tipo_disco == "HDD":
                    velocidade = f"{disco.MaxMediaSize} RPM"
                elif tipo_disco == "SSD":
                    # Para SSDs, tentar obter velocidade de leitura/escrita
                    velocidade = "Varia conforme modelo"
                
                # Partições associadas a este disco
                particoes = []
                try:
                    for disk_to_partition in w.Win32_DiskDriveToDiskPartition():
                        if disk_to_partition.Antecedent.DeviceID.replace('\\\\.\\', '') == disco.DeviceID.replace('\\\\.\\', ''):
                            for partition_to_logical in w.Win32_LogicalDiskToPartition():
                                if partition_to_logical.Antecedent.DeviceID == disk_to_partition.Dependent.DeviceID:
                                    logical_disk = w.Win32_LogicalDisk(DeviceID=partition_to_logical.Dependent.DeviceID)[0]
                                    if logical_disk.Size:
                                        tamanho_particao_gb = int(logical_disk.Size) / (1024**3)
                                        livre_particao_gb = int(logical_disk.FreeSpace) / (1024**3) if logical_disk.FreeSpace else 0
                                        usado_percent = 100 - (livre_particao_gb / tamanho_particao_gb * 100) if tamanho_particao_gb > 0 else 0
                                        particoes.append(f"Unidade {logical_disk.DeviceID}: {livre_particao_gb:.2f} GB livre de {tamanho_particao_gb:.2f} GB ({usado_percent:.1f}% usado)")
                except Exception as e:
                    print(f"Erro ao obter partições: {e}")
                
                # Formata as informações do disco
                info_disco = f"Disco: {modelo}\n"
                info_disco += f"Fabricante: {fabricante}\n"
                info_disco += f"Tipo: {tipo_disco}\n"
                info_disco += f"Interface: {interface}\n"
                info_disco += f"Capacidade: {tamanho_gb:.2f} GB\n"                
                # Adiciona informações das partições
                if particoes:
                    info_disco += "\nPartições:\n - " + "\n - ".join(particoes)
                
                discos_detalhes.append(info_disco)
            
            # Formata a saída com as informações detalhadas
            if discos_detalhes:
                detalhes = "\n\n" + "\n\n".join(discos_detalhes)
                return f"{uso_info}\n{detalhes}"
            else:
                return f"{uso_info}\nNão foi possível obter detalhes adicionais dos discos."
        except Exception as wmi_erro:
            print(f"Erro ao obter detalhes dos discos: {wmi_erro}")
            return uso_info
    except Exception as e:
        print(f"Erro ao obter informações do disco: {e}")
        return "Erro ao obter informações do disco"

def obter_info_ram():
    """Obtém informações detalhadas da memória RAM, incluindo capacidade, frequência, fabricante, tipo e part number."""
    try:
        # Informações básicas de uso da RAM via psutil
        ram = psutil.virtual_memory()
        total_gb = ram.total / (1024**3)
        usado_gb = ram.used / (1024**3)
        uso_info = f"{usado_gb:.2f} GB / {total_gb:.2f} GB ({ram.percent}% usado)"
        
        # Informações detalhadas via WMI
        try:
            import wmi
            w = wmi.WMI()
            ram_detalhes = []
            
            # Mapeamento de tipos de memória
            tipos_memoria = {
                0: "Desconhecido",
                1: "Outro",
                2: "DRAM",
                3: "EDRAM",
                4: "VRAM",
                5: "SRAM",
                6: "RAM",
                7: "ROM",
                8: "Flash",
                9: "EEPROM",
                10: "FEPROM",
                11: "EPROM",
                12: "CDRAM",
                13: "3DRAM",
                14: "SDRAM",
                15: "SGRAM",
                16: "RDRAM",
                17: "DDR",
                18: "DDR2",
                19: "DDR2 FB-DIMM",
                20: "DDR3",
                21: "FBD2",
                22: "DDR4",
                23: "LPDDR",
                24: "LPDDR2",
                25: "LPDDR3",
                26: "LPDDR4",
                27: "DDR5"
            }
            
            # Coleta informações de cada módulo de memória
            for modulo in w.Win32_PhysicalMemory():
                if modulo.Capacity:
                    # Capacidade
                    capacidade_gb = int(modulo.Capacity) / (1024**3)
                    
                    # Frequência
                    frequencia = "Não disponível"
                    if modulo.ConfiguredClockSpeed:
                        frequencia = f"{modulo.ConfiguredClockSpeed} MHz"
                    
                    # Fabricante
                    fabricante = modulo.Manufacturer or "Não disponível"
                    # Limpar o fabricante se for apenas números
                    if fabricante.isdigit():
                        fabricante = "Não identificado"
                    
                    # Tipo de memória
                    tipo_memoria = "Não disponível"
                    if modulo.SMBIOSMemoryType and modulo.SMBIOSMemoryType in tipos_memoria:
                        tipo_memoria = tipos_memoria[modulo.SMBIOSMemoryType]
                    
                    # Part Number
                    part_number = modulo.PartNumber.strip() if modulo.PartNumber else "Não disponível"
                    
                    # Formata as informações do módulo
                    info_modulo = f"Módulo: {capacidade_gb:.2f} GB\n"
                    info_modulo += f"Frequência: {frequencia}\n"
                    info_modulo += f"Fabricante: {fabricante}\n"
                    info_modulo += f"Tipo: {tipo_memoria}\n"
                    info_modulo += f"Part Number: {part_number}"
                    
                    ram_detalhes.append(info_modulo)
            
            # Formata a saída com as informações detalhadas
            if ram_detalhes:
                # Usar uma formatação que garanta que as informações fiquem agrupadas
                detalhes = "\n\n" + "\n\n".join(ram_detalhes)
                return f"{uso_info}{detalhes}"
            else:
                return f"{uso_info}\nNão foi possível obter detalhes dos módulos de memória."
        except Exception as wmi_erro:
            print(f"Erro ao obter detalhes da RAM: {wmi_erro}")
            return uso_info
    except Exception as e:
        print(f"Erro ao obter informações da RAM: {e}")
        return "Erro ao obter informações da RAM"

def obter_info_monitores():
    """Obtém informações detalhadas dos monitores conectados usando um script PowerShell externo.

    Retorna:
        str: Texto formatado com informações dos monitores (quantidade, modelo, fabricante, tamanho).
    """
    import subprocess  # Importação necessária para executar comandos PowerShell
    import os          # Para operações de sistema de arquivos
    import sys         # Para verificar se estamos executando como executável
    import tempfile    # Para criar arquivos temporários
    monitores_formatados = []

    try:
        # Determinar o caminho base (diferente se executado como script ou como executável)
        if getattr(sys, 'frozen', False):
            # Executando como executável empacotado
            base_path = sys._MEIPASS
        else:
            # Executando como script normal
            base_path = os.path.dirname(os.path.abspath(__file__))
            
        # Caminho para o script PowerShell externo
        script_path = os.path.join(base_path, "coletar_monitores.ps1")
        output_path = os.path.join(tempfile.gettempdir(), "monitores_info.txt")
        
        # Verificar se o script existe
        if not os.path.exists(script_path):
            raise Exception(f"Script PowerShell não encontrado: {script_path}")
        
        # Executar o script PowerShell externo
        try:
            # Executar o script PowerShell com bypass de política de execução e passar o caminho do arquivo de saída
            subprocess.run(["powershell", "-ExecutionPolicy", "Bypass", "-File", script_path, "-OutputFilePath", output_path], check=True)
            
            # Verificar se o arquivo de saída foi criado
            if not os.path.exists(output_path):
                raise Exception(f"Arquivo de saída não foi criado: {output_path}")
                
            # Ler o arquivo de saída
            with open(output_path, 'r', encoding='utf-8') as f:
                stdout_text = f.read()
                
        except Exception as e:
            # Se ocorrer qualquer erro
            raise Exception(f"Erro ao executar o script PowerShell para obter informações do monitor: {str(e)}")
        finally:
            # Tentar remover o arquivo de saída
            try:
                if os.path.exists(output_path):
                    os.unlink(output_path)
            except:
                pass  # Ignorar erros na limpeza

        # Processar a saída de texto simples
        if "NENHUM_MONITOR_DETECTADO" in stdout_text:
            monitores_formatados.append("Nenhum monitor detectado.")
        else:
            # Verificar se temos informação sobre a quantidade de monitores
            quantidade_linha = None
            for linha in stdout_text.split('\n'):
                if linha.startswith("QUANTIDADE_MONITORES:"):
                    quantidade_linha = linha.replace("QUANTIDADE_MONITORES:", "").strip()
                    break
            
            # Dividir a saída por monitores usando o separador
            monitores_texto = stdout_text.split("---FIM_MONITOR---")
            
            for monitor_texto in monitores_texto:
                if not monitor_texto.strip():
                    continue
                    
                linhas = monitor_texto.strip().split('\n')
                monitor_info = {}
                
                for linha in linhas:
                    linha = linha.strip()
                    if linha.startswith("MONITOR_"):
                        continue
                    elif linha.startswith("QUANTIDADE_MONITORES:"):
                        continue
                    elif linha.startswith("FABRICANTE: "):
                        monitor_info["fabricante"] = linha.replace("FABRICANTE: ", "")
                    elif linha.startswith("MODELO: "):
                        monitor_info["modelo"] = linha.replace("MODELO: ", "")
                    elif linha.startswith("TAMANHO: "):
                        monitor_info["tamanho"] = linha.replace("TAMANHO: ", "")
                
                # Verificar se temos informações suficientes para este monitor
                if not monitor_info:
                    continue
                
                # Formatar a informação do monitor
                info = f"Monitor: {monitor_info.get('modelo', 'Desconhecido')}\n"
                info += f"Fabricante: {monitor_info.get('fabricante', 'Desconhecido')}\n"
                info += f"Tamanho: {monitor_info.get('tamanho', 'Tamanho desconhecido')}"
                
                monitores_formatados.append(info)

    except NotImplementedError:
        monitores_formatados.append("Coleta de monitores não suportada neste sistema operacional.")
    except Exception as e:
        print(f"Erro ao obter informações dos monitores: {e}")
        # Adicionar uma mensagem de erro clara para o relatório final
        monitores_formatados.append(f"Falha ao obter dados do monitor. Erro: {e}")

    # Se nada foi detectado, adicione uma mensagem padrão
    if not monitores_formatados:
        monitores_formatados.append("Nenhum monitor detectado.")

    # Formatar a saída final
    resultado = f"Total de monitores detectados: {len(monitores_formatados)}\n\n"
    resultado += "\n\n".join(monitores_formatados)
    
    return resultado

def coletar_dados_hardware():
    """Coleta todos os dados de hardware."""
    return {
        "usuarioLogado": obter_usuario_logado(),
        "nomeDispositivo": obter_nome_dispositivo(),
        "processador": obter_info_processador(),
        "disco": obter_info_disco(),
        "ram": obter_info_ram(),
        "monitores": obter_info_monitores()
    }

def exibir_formulario():
    """Exibe o formulário para coleta de informações do usuário usando tkinter."""
    secretarias = [
        "Administração",
        "Educação",
        "Saúde",
        "Segurança",
        "Infraestrutura",
        "Meio Ambiente",
        "Assistência Social",
        "Outra"
    ]
    
    # Variáveis para armazenar as respostas
    respostas = {}
    
    # Criar janela do formulário
    form_window = tk.Tk()
    form_window.title("Formulário de Coleta")
    form_window.geometry("500x400")
    form_window.resizable(False, False)
    
    # Frame principal
    frame = ttk.Frame(form_window, padding=20)
    frame.pack(fill=tk.BOTH, expand=True)
    
    # Título
    ttk.Label(frame, text="Preencha as informações abaixo", 
              font=("Segoe UI", 12, "bold")).pack(pady=(0, 20))
    
    # Variáveis para armazenar os valores dos campos
    secretaria_var = tk.StringVar()
    setor_var = tk.StringVar()
    matricula_var = tk.StringVar()
    nome_var = tk.StringVar()
    outra_secretaria_var = tk.StringVar()
    
    # Frame para secretaria
    secretaria_frame = ttk.Frame(frame)
    secretaria_frame.pack(fill=tk.X, pady=5)
    ttk.Label(secretaria_frame, text="Secretaria:", width=15).pack(side=tk.LEFT)
    secretaria_combo = ttk.Combobox(secretaria_frame, textvariable=secretaria_var, values=secretarias, state="readonly")
    secretaria_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)
    secretaria_combo.current(0)  # Selecionar o primeiro item por padrão
    
    # Frame para outra secretaria (inicialmente oculto)
    outra_frame = ttk.Frame(frame)
    ttk.Label(outra_frame, text="Nome da Secretaria:", width=15).pack(side=tk.LEFT)
    ttk.Entry(outra_frame, textvariable=outra_secretaria_var).pack(side=tk.LEFT, fill=tk.X, expand=True)
    
    # Função para mostrar/ocultar o campo de outra secretaria
    def on_secretaria_change(*args):
        if secretaria_var.get() == "Outra":
            outra_frame.pack(fill=tk.X, pady=5)
        else:
            outra_frame.pack_forget()
    
    secretaria_var.trace('w', on_secretaria_change)
    
    # Frame para setor
    setor_frame = ttk.Frame(frame)
    setor_frame.pack(fill=tk.X, pady=5)
    ttk.Label(setor_frame, text="Setor:", width=15).pack(side=tk.LEFT)
    ttk.Entry(setor_frame, textvariable=setor_var).pack(side=tk.LEFT, fill=tk.X, expand=True)
    
    # Frame para matrícula
    matricula_frame = ttk.Frame(frame)
    matricula_frame.pack(fill=tk.X, pady=5)
    ttk.Label(matricula_frame, text="Matrícula:", width=15).pack(side=tk.LEFT)
    ttk.Entry(matricula_frame, textvariable=matricula_var).pack(side=tk.LEFT, fill=tk.X, expand=True)
    
    # Frame para nome
    nome_frame = ttk.Frame(frame)
    nome_frame.pack(fill=tk.X, pady=5)
    ttk.Label(nome_frame, text="Nome Completo:", width=15).pack(side=tk.LEFT)
    ttk.Entry(nome_frame, textvariable=nome_var).pack(side=tk.LEFT, fill=tk.X, expand=True)
    
    # Função para validar e enviar o formulário
    def enviar_formulario():
        # Validar campos obrigatórios
        if not setor_var.get() or not matricula_var.get() or not nome_var.get():
            messagebox.showerror("Erro", "Todos os campos são obrigatórios!")
            return
        
        # Obter secretaria (normal ou outra)
        if secretaria_var.get() == "Outra":
            if not outra_secretaria_var.get():
                messagebox.showerror("Erro", "Digite o nome da Secretaria!")
                return
            secretaria_final = outra_secretaria_var.get()
        else:
            secretaria_final = secretaria_var.get()
        
        # Armazenar respostas
        respostas['secretaria'] = secretaria_final
        respostas['setor'] = setor_var.get()
        respostas['matricula'] = matricula_var.get()
        respostas['nomeCompleto'] = nome_var.get()
        
        # Fechar janela
        form_window.destroy()
    
    # Botão de enviar
    ttk.Button(frame, text="Enviar", command=enviar_formulario).pack(pady=20)
    
    # Centralizar a janela
    form_window.update_idletasks()
    width = form_window.winfo_width()
    height = form_window.winfo_height()
    x = (form_window.winfo_screenwidth() // 2) - (width // 2)
    y = (form_window.winfo_screenheight() // 2) - (height // 2)
    form_window.geometry('{}x{}+{}+{}'.format(width, height, x, y))
    
    # Executar a janela e aguardar até que seja fechada
    form_window.mainloop()
    
    return respostas

def enviar_dados(dados):
    """Envia os dados coletados para o servidor."""
    try:
        resposta = requests.post(SERVER_URL, json=dados, timeout=10)
        
        if resposta.status_code == 201:
            return True, "Dados enviados com sucesso!"
        else:
            return False, f"Erro ao enviar dados. Código: {resposta.status_code}, Resposta: {resposta.text}"
    except requests.exceptions.ConnectionError:
        return False, "Erro de conexão. Verifique se o servidor está online e acessível."
    except Exception as e:
        return False, f"Erro ao enviar dados: {e}"

def main():
    """Função principal do coletor."""
    # Coletar dados de hardware
    dados_hardware = coletar_dados_hardware()
    
    # Exibir informações em uma janela
    info_window = tk.Tk()
    info_window.title("Informações de Hardware")
    info_window.geometry("500x400")
    info_window.resizable(False, False)
    
    # Frame principal
    frame = ttk.Frame(info_window, padding=20)
    frame.pack(fill=tk.BOTH, expand=True)
    
    # Título
    ttk.Label(frame, text="SISTEMA DE COLETA DE INVENTÁRIO DE HARDWARE", 
              font=("Segoe UI", 12, "bold"), wraplength=450).pack(pady=(0, 20))
    
    # Informações coletadas
    info_text = f"""
Usuário Logado: {dados_hardware['usuarioLogado']}
Nome do Dispositivo: {dados_hardware['nomeDispositivo']}
Processador: {dados_hardware['processador']}
Disco: {dados_hardware['disco']}
RAM: {dados_hardware['ram']}
Monitores: {len(dados_hardware['monitores'])} detectado(s)
    """
    
    # Área de texto para exibir informações
    info_area = tk.Text(frame, height=10, width=50, wrap=tk.WORD)
    info_area.insert(tk.END, info_text)
    info_area.config(state=tk.DISABLED)
    info_area.pack(fill=tk.BOTH, expand=True, pady=10)
    
    # Função para continuar
    def continuar():
        info_window.destroy()
    
    # Botão para continuar
    ttk.Button(frame, text="Continuar", command=continuar).pack(pady=10)
    
    # Centralizar a janela
    info_window.update_idletasks()
    width = info_window.winfo_width()
    height = info_window.winfo_height()
    x = (info_window.winfo_screenwidth() // 2) - (width // 2)
    y = (info_window.winfo_screenheight() // 2) - (height // 2)
    info_window.geometry('{}x{}+{}+{}'.format(width, height, x, y))
    
    info_window.mainloop()
    
    # Exibir formulário para coletar informações do usuário
    dados_usuario = exibir_formulario()
    
    # Combinar dados
    dados_completos = {**dados_hardware, **dados_usuario}
    
    # Enviar dados
    sucesso, mensagem = enviar_dados(dados_completos)
    
    # Exibir resultado
    result_window = tk.Tk()
    result_window.title("Resultado")
    result_window.geometry("400x200")
    result_window.resizable(False, False)
    
    # Frame principal
    frame = ttk.Frame(result_window, padding=20)
    frame.pack(fill=tk.BOTH, expand=True)
    
    # Mensagem de resultado
    if sucesso:
        ttk.Label(frame, text="✓ " + mensagem, font=("Segoe UI", 12)).pack(pady=20)
    else:
        ttk.Label(frame, text="✗ " + mensagem, font=("Segoe UI", 12), wraplength=350).pack(pady=20)
    
    # Botão para fechar
    ttk.Button(frame, text="Fechar", command=result_window.destroy).pack(pady=10)
    
    # Centralizar a janela
    result_window.update_idletasks()
    width = result_window.winfo_width()
    height = result_window.winfo_height()
    x = (result_window.winfo_screenwidth() // 2) - (width // 2)
    y = (result_window.winfo_screenheight() // 2) - (height // 2)
    result_window.geometry('{}x{}+{}+{}'.format(width, height, x, y))
    
    result_window.mainloop()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nOperação cancelada pelo usuário.")
    except Exception as e:
        print(f"\n\nOcorreu um erro inesperado: {e}")
        print("\nPressione Enter para sair...")
        input()
