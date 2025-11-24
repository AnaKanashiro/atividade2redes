"""
Aplicação Flask - Trabalho 02 Redes
Backend HTTP com sessão centralizada em PostgreSQL
"""

from flask import Flask, request, jsonify, make_response, send_from_directory
from flask_cors import CORS
from werkzeug.security import check_password_hash, generate_password_hash
import psycopg2
import psycopg2.extras
import uuid
from datetime import datetime, timedelta
import socket
import os

FRONTEND_PATH = '/app/frontend'
if not os.path.exists(FRONTEND_PATH):
    FRONTEND_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend')

app = Flask(__name__, static_folder=FRONTEND_PATH, static_url_path='')

# ============================================
# CORREÇÃO CRÍTICA DO CORS
# ============================================
# Permitir os IPs da nova arquitetura (172.20.0.x)
allowed_origins = [
    'http://localhost',
    'http://127.0.0.1',
    'http://www.meutrabalho.com.br',
    'http://meutrabalho.com.br',
    # IPs dos containers na porta 80 (padrão)
    'http://172.20.0.10',
    'http://172.20.0.11',
    'http://172.20.0.12',
    # Manter portas antigas apenas por compatibilidade de desenvolvimento
    'http://localhost:5000', 'http://localhost:5003', 'http://localhost:5004', 'http://localhost:5005'
]

CORS(app, 
     origins=allowed_origins,
     supports_credentials=True,
     allow_headers=['Content-Type', 'Authorization', 'Cookie'],
     methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
     expose_headers=['Content-Type'])

@app.route('/js/<path:filename>')
def serve_js(filename):
    return send_from_directory(os.path.join(FRONTEND_PATH, 'js'), filename)

app.secret_key = os.getenv('SECRET_KEY', 'sua-chave-secreta-aqui-mude-em-producao')

# Configuração do banco de dados PostgreSQL
DB_CONFIG = {
    'host': os.getenv('DB_HOST', '172.20.0.20'),
    'port': os.getenv('DB_PORT', '5432'),
    'database': os.getenv('DB_NAME', 'meutrabalho'),
    'user': os.getenv('DB_USER', 'trabalho'),
    'password': os.getenv('DB_PASSWORD', 'trabalho123')
}

def get_db():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except psycopg2.OperationalError as e:
        print(f"❌ Erro ao conectar ao banco: {e}")
        raise
    except psycopg2.Error as e:
        print(f"Erro ao conectar ao banco: {e}")
        raise

def criar_sessao(usuario_id):
    session_id = str(uuid.uuid4())
    expires_at = datetime.now() + timedelta(hours=1)
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                'INSERT INTO sessoes (session_id, usuario_id, expires_at) VALUES (%s, %s, %s)',
                (session_id, usuario_id, expires_at)
            )
        conn.commit()
        return session_id
    except psycopg2.Error as e:
        conn.rollback()
        raise
    finally:
        conn.close()

def validar_sessao(session_id):
    if not session_id: return None
    conn = get_db()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                'SELECT * FROM sessoes WHERE session_id = %s AND expires_at > %s',
                (session_id, datetime.now())
            )
            return cur.fetchone()
    except psycopg2.Error:
        return None
    finally:
        conn.close()

def get_hostname():
    return os.getenv('SERVER_NAME', socket.gethostname())

# ROTAS
@app.route('/')
def index():
    try: return send_from_directory(FRONTEND_PATH, 'index.html')
    except: return send_from_directory(FRONTEND_PATH, 'fallback.html')

@app.route('/perfil.html')
def perfil():
    try: return send_from_directory(FRONTEND_PATH, 'perfil.html')
    except Exception as e: return str(e), 500

@app.route('/fallback.html')
def fallback():
    try: return send_from_directory(FRONTEND_PATH, 'fallback.html')
    except Exception as e: return str(e), 500

# API
@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        if not data: return jsonify({'erro': 'Dados inválidos'}), 400
        login, senha = data.get('login'), data.get('senha')
        
        conn = get_db()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute('SELECT * FROM usuarios WHERE login = %s', (login,))
                usuario = cur.fetchone()
        finally:
            conn.close()
        
        if not usuario or not check_password_hash(usuario['senha_hash'], senha):
            return jsonify({'erro': 'Credenciais inválidas'}), 401
        
        session_id = criar_sessao(usuario['id'])
        response = make_response(jsonify({'sucesso': True, 'session_id': session_id}))
        response.set_cookie('session_id', session_id, httponly=True, max_age=3600, samesite='Lax', path='/')
        return response
    except Exception as e:
        print(f"Erro: {e}")
        return jsonify({'erro': 'Erro interno'}), 500

@app.route('/api/meu-perfil', methods=['GET'])
def meu_perfil():
    try:
        session_id = request.cookies.get('session_id')
        sessao = validar_sessao(session_id)
        if not sessao: return jsonify({'erro': 'Não autenticado'}), 401
        
        conn = get_db()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute('SELECT * FROM usuarios WHERE id = %s', (sessao['usuario_id'],))
                usuario = cur.fetchone()
        finally:
            conn.close()
            
        if not usuario: return jsonify({'erro': 'Usuário não encontrado'}), 404
        
        return jsonify({
            'nome': usuario['nome'],
            'hostname': get_hostname(),
            'data_login': sessao['created_at'].isoformat(),
            'codigo_sessao': sessao['session_id']
        })
    except Exception:
        return jsonify({'erro': 'Erro interno'}), 500

@app.route('/api/logout', methods=['POST'])
def logout():
    try:
        session_id = request.cookies.get('session_id')
        if session_id:
            conn = get_db()
            try:
                with conn.cursor() as cur:
                    cur.execute('DELETE FROM sessoes WHERE session_id = %s', (session_id,))
                conn.commit()
            finally:
                conn.close()
        response = make_response(jsonify({'sucesso': True}))
        response.set_cookie('session_id', '', expires=0, path='/')
        return response
    except Exception:
        return jsonify({'erro': 'Erro interno'}), 500

@app.route('/api/health', methods=['GET'])
def health():
    try:
        conn = get_db()
        conn.close()
        return jsonify({'status': 'ok', 'hostname': get_hostname(), 'timestamp': datetime.now().isoformat()})
    except Exception as e:
        return jsonify({'status': 'error', 'hostname': get_hostname(), 'erro': str(e)}), 503


@app.after_request
def add_header(response):
    """
    Adiciona headers para desativar cache do navegador e 
    forçar o fechamento da conexão TCP após cada requisição.
    Isso obriga o navegador a fazer uma nova consulta DNS no próximo F5.
    """
    # Desativar Cache de Arquivos
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    
    # MATAR A CONEXÃO TCP (O Segredo do Round Robin no Browser)
    response.headers['Connection'] = 'close'
    
    return response

# ============================================
# INICIALIZAÇÃO
# ============================================

if __name__ == '__main__':
    print(f"🚀 Iniciando servidor HTTP: {get_hostname()}")
    app.run(host='0.0.0.0', port=5000, debug=False)