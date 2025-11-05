# -*- coding: utf-8 -*-
import os
import re
import socket
import time
from datetime import datetime
from flask import (Flask, render_template, request, jsonify, redirect,
                   url_for, send_from_directory, session, flash)
import requests

# --- Configuração Inicial ---
app = Flask(__name__, template_folder='.')
app.config['SECRET_KEY'] = os.urandom(32)
app.config['UPLOAD_FOLDER'] = 'registros'

# --- MEMÓRIA TEMPORÁRIA DE LOGINS ---
# Esta variável guardará os usuários e senhas criados.
# Será apagada toda vez que o servidor for reiniciado.
SESSOES_ATIVAS = {}
# --- --- ---

# --- Funções Auxiliares (sem alterações) ---
def carregar_codigos_do_arquivo(caminho_arquivo):
    if not os.path.exists(caminho_arquivo): return set()
    try:
        with open(caminho_arquivo, "r", encoding="utf-8") as arquivo:
            return {linha.strip() for linha in arquivo if linha.strip()}
    except Exception as e:
        print(f"Erro ao carregar o arquivo: {e}")
        return set()

def formatar_tempo(segundos):
    if segundos is None: return "00:00:00"
    segundos = int(segundos)
    horas, resto = divmod(segundos, 3600)
    minutos, segundos = divmod(resto, 60)
    return f"{horas:02}:{minutos:02}:{segundos:02}"

# --- Rotas de Autenticação e Páginas ---
@app.route('/', methods=['GET'])
def index():
    host_ip = request.host.split(':')[0]
    if 'usuario' in session:
        return render_template('index.html', host_ip=host_ip, session_data=session)
    return render_template('login.html', host_ip=host_ip)

@app.route('/login', methods=['POST'])
def login():
    action = request.form.get('action')
    nome_usuario = request.form.get('nome_usuario', '').strip()
    senha = request.form.get('senha', '').strip()

    if not nome_usuario or not senha:
        flash('Nome de usuário e senha são obrigatórios!', 'error')
        return redirect(url_for('index'))

    if action == 'registrar':
        if nome_usuario in SESSOES_ATIVAS:
            flash('Este nome de usuário já está em uso. Tente outro ou entre com a senha correta.', 'error')
            return redirect(url_for('index'))
        
        SESSOES_ATIVAS[nome_usuario] = senha
        flash(f'Usuário "{nome_usuario}" criado! Agora você pode usar a aba "Entrar".', 'success')
        print(f"Sessão temporária criada para '{nome_usuario}'.")
        return redirect(url_for('index'))

    elif action == 'entrar':
        if nome_usuario in SESSOES_ATIVAS and SESSOES_ATIVAS[nome_usuario] == senha:
            nome_sanitizado = re.sub(r'[^a-zA-Z0-9_ -]', '', nome_usuario).replace(' ', '_')
            data_hoje = datetime.now().strftime('%Y-%m-%d')
            nome_arquivo = f"{data_hoje}_{nome_sanitizado}.txt"
            if not os.path.exists(app.config['UPLOAD_FOLDER']): os.makedirs(app.config['UPLOAD_FOLDER'])
            caminho_completo = os.path.join(app.config['UPLOAD_FOLDER'], nome_arquivo)
            
            session['usuario'] = nome_usuario
            session['start_time'] = time.time()
            session['arquivo_destino'] = caminho_completo
            session['nome_arquivo_atual'] = nome_arquivo
            session['codigos_lidos_cache'] = list(carregar_codigos_do_arquivo(caminho_completo))
            print(f"Login bem-sucedido para '{nome_usuario}'.")
            return redirect(url_for('index'))
        else:
            flash('Usuário ou senha inválidos!', 'error')
            return redirect(url_for('index'))
            
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    usuario = session.get('usuario', 'desconhecido')
    print(f"Encerrando sessão de '{usuario}'.")
    session.clear()
    return redirect(url_for('index'))

def login_necessario(f):
    def wrapper(*args, **kwargs):
        if 'usuario' not in session: return redirect(url_for('index'))
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper

@app.route('/desktop')
@login_necessario
def desktop_scanner():
    host_ip = request.host.split(':')[0]
    return render_template('desktop.html', host_ip=host_ip)

@app.route('/mobile')
@login_necessario
def mobile_scanner():
    return render_template('mobile.html')

# --- Rotas da API (lógica do leitor) ---
# (As rotas /scan, /data, /dados-sessao, etc. continuam iguais e funcionarão corretamente)
@app.route('/scan', methods=['POST'])
@login_necessario
def processar_scan():
    if 'arquivo_destino' not in session: return jsonify({"status": "error", "message": "Sessão inválida. Faça login novamente."}), 400
    data = request.json
    texto_lido = data.get('qr_code', '').strip()
    match = re.search(r'(\d{44})', texto_lido)
    codigo_processado = match.group(1) if match else None
    if not codigo_processado: return jsonify({"status": "error", "message": "Chave de NF-e inválida (44 dígitos)."}), 400
    if codigo_processado in session['codigos_lidos_cache']: return jsonify({"status": "duplicate", "code": codigo_processado, "message": "Esta NF-e já foi registrada."})
    session['codigos_lidos_cache'].append(codigo_processado)
    session.modified = True
    try:
        with open(session['arquivo_destino'], "a", encoding="utf-8") as arquivo:
            arquivo.write(codigo_processado + "\n")
        return jsonify({"status": "success", "code": codigo_processado, "message": "NF-e salva com sucesso!"})
    except Exception as e:
        session['codigos_lidos_cache'].pop()
        session.modified = True
        return jsonify({"status": "error", "message": f"Erro ao salvar: {e}"}), 500

@app.route('/data')
@login_necessario
def get_dados_atuais():
    codigos = sorted(session.get('codigos_lidos_cache', []), reverse=True)
    return jsonify({"codes": codigos, "count": len(codigos)})

@app.route('/dados-sessao')
@login_necessario
def get_dados_sessao():
    tempo_decorrido = time.time() - session.get("start_time", 0)
    return jsonify({"nome_usuario": session.get('usuario'), "tempo_formatado": formatar_tempo(tempo_decorrido)})

@app.route('/download')
@login_necessario
def download_arquivo():
    nome_arquivo = session.get("nome_arquivo_atual")
    if not nome_arquivo: return "Nenhum arquivo de sessão ativo.", 404
    return send_from_directory(app.config['UPLOAD_FOLDER'], nome_arquivo, as_attachment=True)

@app.route('/assets/<path:filename>')
def custom_static(filename):
    return send_from_directory('assets', filename)

def baixar_asset(nome_arquivo, url):
    caminho_arquivo = os.path.join('assets', nome_arquivo)
    if not os.path.exists(caminho_arquivo):
        try:
            print(f"Baixando {nome_arquivo}...")
            r = requests.get(url, allow_redirects=True, timeout=15)
            r.raise_for_status()
            with open(caminho_arquivo, 'wb') as f: f.write(r.content)
            print(f"Download de {nome_arquivo} concluído.")
        except Exception as e:
            print(f"ERRO ao baixar {nome_arquivo}: {e}\nPor favor, baixe manualmente de: {url} e coloque na pasta 'assets'.")
            exit()

if __name__ == '__main__':
    if not os.path.exists('assets'): os.makedirs('assets')
    baixar_asset('html5-qrcode.min.js', 'https://unpkg.com/html5-qrcode/html5-qrcode.min.js')
    baixar_asset('beep.mp3', 'https://www.soundjay.com/buttons/sounds/beep-07a.mp3')
    baixar_asset('qrcode.min.js', 'https://cdn.jsdelivr.net/npm/qrcode-generator/qrcode.js')
    host_ip_rede = "0.0.0.0"
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM); s.settimeout(2); s.connect(("8.8.8.8", 80)); host_ip_rede = s.getsockname()[0]; s.close()
    except Exception:
        print("Não foi possível determinar o IP da rede local. Use o IP da sua máquina.")
    print("\n--- Servidor de Leitor de NF-e ---")
    print("--> Acesse o sistema para criar um usuário ou entrar. <--")
    print(f"\nAcesse de outro dispositivo na mesma rede via: https://{host_ip_rede}:5000")
    print(f"Acesse no seu computador via: https://127.0.0.1:5000")
    try:
        app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False, ssl_context='adhoc')
    except ImportError:
        print("\n\nERRO: Pacotes não instalados.")
        print("Execute: pip install pyopenssl cryptography")
    except Exception as e:
        print(f"\n\nERRO ao iniciar o servidor: {e}")

