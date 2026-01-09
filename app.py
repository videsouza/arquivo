import os
import json
import base64
import requests
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# --- CONFIGURAÇÕES (Vêm das Variáveis de Ambiente do Render) ---
# Você NÃO coloca o token aqui no código. Colocará nas configurações do Render.
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
GITHUB_USERNAME = os.environ.get("GITHUB_USERNAME")
GITHUB_REPO = os.environ.get("GITHUB_REPO")
FILE_PATH = "dados.json"

# Headers para falar com a API do GitHub
def get_github_headers():
    return {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

# --- FUNÇÕES AUXILIARES ---
def get_data_from_github():
    url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{GITHUB_REPO}/contents/{FILE_PATH}"
    response = requests.get(url, headers=get_github_headers())
    
    if response.status_code == 404:
        return [], None # Arquivo não existe, retorna lista vazia
    
    if response.status_code != 200:
        raise Exception(f"Erro ao ler GitHub: {response.text}")

    data = response.json()
    sha = data.get('sha')
    content_base64 = data.get('content', '')
    
    # Limpa quebras de linha e decodifica
    content_json = base64.b64decode(content_base64).decode('utf-8')
    try:
        boxes = json.loads(content_json)
    except:
        boxes = []
        
    return boxes, sha

def save_data_to_github(boxes, sha_atual):
    url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{GITHUB_REPO}/contents/{FILE_PATH}"
    
    content_json = json.dumps(boxes, indent=2)
    content_base64 = base64.b64encode(content_json.encode('utf-8')).decode('utf-8')
    
    payload = {
        "message": "Update via Render App",
        "content": content_base64
    }
    if sha_atual:
        payload["sha"] = sha_atual
        
    response = requests.put(url, json=payload, headers=get_github_headers())
    
    if response.status_code not in [200, 201]:
        raise Exception(f"Erro ao salvar: {response.text}")
    
    return True

# --- ROTAS DO SITE ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/boxes', methods=['GET'])
def get_boxes():
    try:
        boxes, _ = get_data_from_github()
        return jsonify(boxes)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/boxes', methods=['POST'])
def save_boxes():
    try:
        new_boxes = request.json
        # Precisamos do SHA atual antes de salvar para evitar conflito
        _, current_sha = get_data_from_github()
        save_data_to_github(new_boxes, current_sha)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
