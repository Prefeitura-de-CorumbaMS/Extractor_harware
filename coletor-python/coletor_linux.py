#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import json
import socket
import platform
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox
import requests
import psutil
import tempfile
from datetime import datetime

# Configuração
SERVER_BASE_URL = "http://localhost:3000"
SERVER_URL = f"{SERVER_BASE_URL}/api/hardware-data"
VERIFICAR_URL = f"{SERVER_BASE_URL}/api/verificar-cadastro/"

def obter_usuario_logado():
    """Obtém o nome do usuário atualmente logado na máquina."""
    try:
        # No Linux, podemos usar o comando 'whoami'
        usuario = subprocess.check_output(['whoami'], text=True).strip()
        return usuario
    except Exception as e:
        print(f"Erro ao obter usuário logado: {e}")
        return "Desconhecido"

def obter_nome_dispositivo():
    """Obtém o nome do dispositivo."""
    return socket.gethostname()

def obter_info_processador():
    """Obtém informações detalhadas do processador."""
    try:
        # Usar o comando lscpu para obter informações do processador
        info_cpu = subprocess.check_output(['lscpu'], text=True)
        
        # Extrair informações relevantes
        modelo = "Desconhecido"
        fabricante = "Desconhecido"
        cores = "Desconhecido"
        threads = "Desconhecido"
        
        for linha in info_cpu.split('\n'):
            if 'Model name' in linha:
                modelo = linha.split(':')[1].strip()
            elif 'Vendor ID' in linha:
                fabricante = linha.split(':')[1].strip()
            elif 'CPU(s)' in linha and cores == "Desconhecido":
                cores = linha.split(':')[1].strip()
            elif 'Thread(s) per core' in linha:
                threads_por_core = linha.split(':')[1].strip()
                threads = str(int(cores) * int(threads_por_core))
        
        # Informações adicionais usando /proc/cpuinfo
        try:
            with open('/proc/cpuinfo', 'r') as f:
                cpuinfo = f.read()
                
            # Extrair frequência
            freq = "Desconhecido"
            for linha in cpuinfo.split('\n'):
                if 'cpu MHz' in linha:
                    freq_mhz = float(linha.split(':')[1].strip())
                    freq = f"{freq_mhz/1000:.2f} GHz"
                    break
        except:
            freq = "Desconhecido"
        
        return f"{fabricante} {modelo}, {cores} núcleos, {threads} threads, {freq}"
    except Exception as e:
        print(f"Erro ao obter informações do processador: {e}")
        return "Informações do processador não disponíveis"

def obter_info_disco():
    """Obtém informações detalhadas dos discos."""
    try:
        # Usar o comando lsblk para listar discos
        info_discos = subprocess.check_output(['lsblk', '-d', '-o', 'NAME,SIZE,MODEL,SERIAL'], text=True)
        
        # Processar a saída
        linhas = info_discos.strip().split('\n')
        discos = []
        
        # Pular o cabeçalho
        for linha in linhas[1:]:
            partes = linha.split()
            if len(partes) >= 2:
                nome = partes[0]
                tamanho = partes[1]
                modelo = ' '.join(partes[2:-1]) if len(partes) > 3 else "Desconhecido"
                discos.append(f"{nome}: {modelo} ({tamanho})")
        
        # Verificar se há discos SSD usando o comando smartctl
        try:
            for disco in discos:
                nome_disco = disco.split(':')[0]
                # Verificar se é SSD ou HDD usando smartctl
                tipo_cmd = subprocess.run(['smartctl', '-i', f'/dev/{nome_disco}'], 
                                         stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                if 'Solid State Device' in tipo_cmd.stdout:
                    disco = disco.replace(')', ', SSD)')
                else:
                    disco = disco.replace(')', ', HDD)')
        except:
            pass  # Ignorar erros do smartctl
            
        return ", ".join(discos) if discos else "Informações de disco não disponíveis"
    except Exception as e:
        print(f"Erro ao obter informações do disco: {e}")
        return "Informações de disco não disponíveis"

def obter_info_ram():
    """Obtém informações detalhadas da memória RAM."""
    try:
        # Obter memória total usando psutil
        mem = psutil.virtual_memory()
        total_gb = mem.total / (1024**3)
        
        # Tentar obter informações mais detalhadas usando dmidecode (requer sudo)
        try:
            # Verificar se o usuário tem permissão para executar dmidecode
            dmidecode_test = subprocess.run(['sudo', '-n', 'dmidecode', '-t', '17'], 
                                           stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
                                           text=True)
            
            if dmidecode_test.returncode == 0:
                # Usuário tem permissão para executar dmidecode sem senha
                ram_info = subprocess.check_output(['sudo', 'dmidecode', '-t', '17'], text=True)
                
                # Processar informações
                modulos = []
                modulo_atual = {}
                
                for linha in ram_info.split('\n'):
                    linha = linha.strip()
                    if 'Memory Device' in linha and not modulo_atual:
                        modulo_atual = {}
                    elif 'Size:' in linha and 'No Module Installed' not in linha:
                        modulo_atual['tamanho'] = linha.split(':')[1].strip()
                    elif 'Type:' in linha and 'Unknown' not in linha:
                        modulo_atual['tipo'] = linha.split(':')[1].strip()
                    elif 'Speed:' in linha and 'Unknown' not in linha:
                        modulo_atual['velocidade'] = linha.split(':')[1].strip()
                        if modulo_atual:
                            modulos.append(modulo_atual)
                            modulo_atual = {}
                
                if modulos:
                    detalhes = []
                    for m in modulos:
                        if 'tamanho' in m and 'tipo' in m and 'velocidade' in m:
                            detalhes.append(f"{m['tamanho']} {m['tipo']} {m['velocidade']}")
                    
                    return ", ".join(detalhes)
            
            # Se não conseguiu detalhes ou não tem permissão, retorna informação básica
            return f"Total: {total_gb:.2f} GB"
            
        except Exception:
            # Fallback para informação básica
            return f"Total: {total_gb:.2f} GB"
            
    except Exception as e:
        print(f"Erro ao obter informações da RAM: {e}")
        return "Informações de RAM não disponíveis"

def obter_info_monitores():
    """Obtém informações detalhadas dos monitores conectados."""
    try:
        # Verificar se o comando xrandr está disponível
        if subprocess.run(['which', 'xrandr'], stdout=subprocess.PIPE, stderr=subprocess.PIPE).returncode == 0:
            # Usar xrandr para obter informações dos monitores
            saida = subprocess.check_output(['xrandr', '--verbose'], text=True)
            
            # Processar a saída para extrair informações dos monitores
            monitores = []
            monitor_atual = None
            edid = ""
            
            for linha in saida.split('\n'):
                if ' connected ' in linha:
                    # Novo monitor encontrado
                    if monitor_atual:
                        # Processar EDID do monitor anterior
                        monitor_atual['edid'] = edid
                        monitores.append(monitor_atual)
                        edid = ""
                    
                    nome = linha.split(' ')[0]
                    resolucao = linha.split('primary ')[1].split(' ')[0] if 'primary' in linha else "Desconhecido"
                    monitor_atual = {
                        'nome': nome,
                        'resolucao': resolucao,
                        'fabricante': "Desconhecido",
                        'modelo': "Desconhecido",
                        'tamanho': "Desconhecido"
                    }
                
                elif 'EDID:' in linha and monitor_atual:
                    # Início do bloco EDID
                    edid = ""
                
                elif '\t\t' in linha and monitor_atual and 'EDID:' in saida:
                    # Linha de EDID
                    edid += linha.strip()
                
                elif 'width' in linha and 'height' in linha and monitor_atual:
                    # Tamanho físico do monitor em mm
                    try:
                        partes = linha.strip().split()
                        width_idx = partes.index('width')
                        height_idx = partes.index('height')
                        if width_idx + 1 < len(partes) and height_idx + 1 < len(partes):
                            width_mm = int(partes[width_idx + 1])
                            height_mm = int(partes[height_idx + 1])
                            diagonal_inch = ((width_mm**2 + height_mm**2)**0.5) / 25.4
                            monitor_atual['tamanho'] = f"{diagonal_inch:.1f}\""
                    except:
                        pass
            
            # Adicionar o último monitor
            if monitor_atual:
                monitor_atual['edid'] = edid
                monitores.append(monitor_atual)
            
            # Tentar extrair informações do fabricante e modelo do EDID
            for monitor in monitores:
                if monitor['edid']:
                    try:
                        # Aqui seria necessário um parser de EDID mais complexo
                        # Por simplicidade, apenas indicamos que temos o monitor
                        monitor['fabricante'] = "Detectado"
                        monitor['modelo'] = "Detectado"
                    except:
                        pass
            
            # Formatar a saída
            resultado = []
            for i, monitor in enumerate(monitores, 1):
                info = f"Monitor {i}: {monitor['fabricante']} {monitor['modelo']}, {monitor['tamanho']}, {monitor['resolucao']}"
                resultado.append(info)
            
            return resultado if resultado else ["Nenhum monitor detectado"]
        
        else:
            # Fallback se xrandr não estiver disponível
            return ["Informações de monitores não disponíveis (xrandr não encontrado)"]
    
    except Exception as e:
        print(f"Erro ao obter informações dos monitores: {e}")
        return ["Erro ao obter informações dos monitores"]

def coletar_dados_hardware():
    """Coleta todos os dados de hardware."""
    return {
        "usuarioLogado": obter_usuario_logado(),
        "nomeDispositivo": obter_nome_dispositivo(),
        "processador": obter_info_processador(),
        "disco": obter_info_disco(),
        "ram": obter_info_ram(),
        "monitores": obter_info_monitores(),
        "sistemaOperacional": f"Linux {platform.release()}"
    }

def exibir_formulario(dados_hardware):
    """Exibe o formulário para coleta de informações do usuário."""
    respostas = {}
    
    # Criar janela do formulário
    form_window = tk.Tk()
    form_window.title("Formulário de Coleta")
    form_window.resizable(False, False)
    
    # Frame principal
    frame = ttk.Frame(form_window, padding=20)
    frame.pack(fill=tk.BOTH, expand=True)
    
    # Título
    ttk.Label(frame, text="PREENCHA AS INFORMAÇÕES ABAIXO", 
              font=("Arial", 12, "bold")).pack(pady=(0, 20))
    
    # Campos do formulário
    campos = [
        {"label": "Secretaria", "var": "secretaria"},
        {"label": "Setor", "var": "setor"},
        {"label": "Matrícula", "var": "matricula"},
        {"label": "Nome", "var": "nome"},
        {"label": "Observações", "var": "observacoes", "height": 3}
    ]
    
    # Criar campos
    for campo in campos:
        # Frame para cada campo
        field_frame = ttk.Frame(frame)
        field_frame.pack(fill=tk.X, pady=5)
        
        # Label
        ttk.Label(field_frame, text=f"{campo['label']}:", width=15).pack(side=tk.LEFT)
        
        # Campo de entrada
        if campo.get("height", 1) > 1:
            # Área de texto para campos multi-linha
            text_widget = tk.Text(field_frame, height=campo["height"], width=30)
            text_widget.pack(side=tk.LEFT, fill=tk.X, expand=True)
            respostas[campo["var"]] = text_widget
        else:
            # Entry para campos de linha única
            var = tk.StringVar()
            ttk.Entry(field_frame, textvariable=var, width=30).pack(side=tk.LEFT, fill=tk.X, expand=True)
            respostas[campo["var"]] = var
    
    # Função para enviar o formulário
    def enviar():
        # Validar campos obrigatórios
        campos_obrigatorios = ["secretaria", "setor", "matricula", "nome"]
        for campo in campos_obrigatorios:
            valor = respostas[campo].get() if isinstance(respostas[campo], tk.StringVar) else respostas[campo].get("1.0", tk.END).strip()
            if not valor:
                messagebox.showerror("Erro", f"O campo {campo} é obrigatório!")
                return
        
        # Coletar valores
        for campo in campos:
            var = campo["var"]
            if isinstance(respostas[var], tk.StringVar):
                dados_hardware[var] = respostas[var].get()
            else:
                dados_hardware[var] = respostas[var].get("1.0", tk.END).strip()
        
        # Adicionar data e hora
        dados_hardware["dataColeta"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Fechar janela
        form_window.destroy()
    
    # Botão de enviar
    ttk.Button(frame, text="Enviar", command=enviar).pack(pady=20)
    
    # Centralizar janela
    form_window.update_idletasks()
    width = form_window.winfo_width()
    height = form_window.winfo_height()
    x = (form_window.winfo_screenwidth() // 2) - (width // 2)
    y = (form_window.winfo_screenheight() // 2) - (height // 2)
    form_window.geometry('{}x{}+{}+{}'.format(width, height, x, y))
    
    # Executar a janela e aguardar até que seja fechada
    form_window.mainloop()
    
    return dados_hardware

def verificar_cadastro_existente(nome_dispositivo, matricula):
    """Verifica se a máquina ou matrícula já está registrada no servidor."""
    try:
        url = f"{VERIFICAR_URL}{nome_dispositivo}/{matricula}"
        resposta = requests.get(url, timeout=10)
        
        if resposta.status_code == 200:
            dados = resposta.json()
            resultado = {
                'jaExiste': dados.get('jaExiste', False),
                'maquinaExiste': dados.get('maquinaExiste', False),
                'matriculaExiste': dados.get('matriculaExiste', False)
            }
            return resultado
        else:
            print(f"Erro ao verificar cadastro. Código: {resposta.status_code}")
            return {'jaExiste': False, 'maquinaExiste': False, 'matriculaExiste': False}
    except requests.exceptions.ConnectionError:
        print("Erro de conexão ao verificar cadastro. Verifique se o servidor está online.")
        return {'jaExiste': False, 'maquinaExiste': False, 'matriculaExiste': False}
    except Exception as e:
        print(f"Erro ao verificar cadastro: {e}")
        return {'jaExiste': False, 'maquinaExiste': False, 'matriculaExiste': False}

def enviar_dados(dados):
    """Envia os dados coletados para o servidor."""
    try:
        # Verificar se a máquina ou matrícula já existe
        resultado = verificar_cadastro_existente(dados['nomeDispositivo'], dados['matricula'])
        
        if resultado['jaExiste']:
            mensagem = ""
            if resultado['maquinaExiste'] and resultado['matriculaExiste']:
                mensagem = "Esta máquina e esta matrícula já estão registradas no sistema."
            elif resultado['maquinaExiste']:
                mensagem = "Esta máquina já está registrada no sistema."
            elif resultado['matriculaExiste']:
                mensagem = "Esta matrícula já está registrada no sistema."
            
            return False, f"{mensagem} Não é possível cadastrar novamente."
        
        # Se não existe, enviar os dados
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
              font=("Arial", 12, "bold"), wraplength=450).pack(pady=(0, 20))
    
    # Informações coletadas
    info_text = f"""
Usuário Logado: {dados_hardware['usuarioLogado']}
Nome do Dispositivo: {dados_hardware['nomeDispositivo']}
Sistema Operacional: {dados_hardware['sistemaOperacional']}
Processador: {dados_hardware['processador']}
Disco: {dados_hardware['disco']}
RAM: {dados_hardware['ram']}
Monitores: {len(dados_hardware['monitores'])} detectado(s)
    """
    
    # Área de texto para exibir informações
    text_area = tk.Text(frame, height=10, width=50, wrap=tk.WORD)
    text_area.insert(tk.END, info_text)
    text_area.config(state=tk.DISABLED)
    text_area.pack(fill=tk.BOTH, expand=True, pady=10)
    
    # Função para continuar
    def continuar():
        info_window.destroy()
        
        # Exibir formulário para coleta de informações adicionais
        dados_completos = exibir_formulario(dados_hardware)
        
        # Verificar se o formulário foi preenchido
        if "secretaria" in dados_completos:
            # Enviar dados para o servidor
            sucesso, mensagem = enviar_dados(dados_completos)
            
            # Exibir resultado
            if sucesso:
                messagebox.showinfo("Sucesso", mensagem)
            else:
                messagebox.showerror("Erro", mensagem)
    
    # Botão para continuar
    ttk.Button(frame, text="Continuar", command=continuar).pack(pady=10)
    
    # Centralizar janela
    info_window.update_idletasks()
    width = info_window.winfo_width()
    height = info_window.winfo_height()
    x = (info_window.winfo_screenwidth() // 2) - (width // 2)
    y = (info_window.winfo_screenheight() // 2) - (height // 2)
    info_window.geometry('{}x{}+{}+{}'.format(width, height, x, y))
    
    # Executar a janela
    info_window.mainloop()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nOperação cancelada pelo usuário.")
    except Exception as e:
        print(f"Erro não tratado: {e}")
        messagebox.showerror("Erro", f"Ocorreu um erro inesperado: {e}")
    finally:
        sys.exit(0)
