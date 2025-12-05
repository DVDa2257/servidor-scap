#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
=====================================================
SERVIDOR DE CONTROLE DE ACESSO
Samsung A20 - Termux
Python 3 + Flask + SQLite3
=====================================================
"""

from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import sqlite3
import json
from datetime import datetime
import os

app = Flask(__name__)
CORS(app)

# Configurações
DATABASE = 'controle_acesso.db'
PORT = 3000

# ==================== BANCO DE DADOS ====================

def get_db():
    """Conectar ao banco de dados"""
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row  # Retornar dict em vez de tupla
    return db

def init_db():
    """Inicializar banco de dados"""
    db = get_db()
    cursor = db.cursor()
    
    # Tabela de usuários
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            uid TEXT UNIQUE NOT NULL,
            nome TEXT NOT NULL,
            cargo TEXT,
            ativo BOOLEAN DEFAULT 1,
            validade INTEGER,
            criado_em INTEGER DEFAULT (strftime('%s', 'now'))
        )
    ''')
    
    # Tabela de máquinas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS maquinas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            machine_id TEXT UNIQUE NOT NULL,
            nome TEXT NOT NULL,
            local TEXT,
            ativa BOOLEAN DEFAULT 1,
            ip TEXT,
            criado_em INTEGER DEFAULT (strftime('%s', 'now'))
        )
    ''')
    
    # Tabela de logs
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp INTEGER NOT NULL,
            machine_id TEXT NOT NULL,
            uid TEXT NOT NULL,
            usuario TEXT,
            evento TEXT NOT NULL,
            rssi INTEGER,
            duracao INTEGER,
            criado_em INTEGER DEFAULT (strftime('%s', 'now'))
        )
    ''')
    
    db.commit()
    
    # Inserir dados iniciais
    inserir_dados_iniciais(cursor, db)
    
    db.close()
    print('✅ Banco de dados inicializado')

def inserir_dados_iniciais(cursor, db):
    """Inserir usuários e máquinas de exemplo"""
    usuarios = [
        ('FA089CBC', 'João Silva', 'Operador Senior'),
        ('EBEABCA5', 'Maria Santos', 'Supervisora'),
        ('6B423203', 'Pedro Costa', 'Técnico'),
        ('FB32FAA5', 'Ana Oliveira', 'Operadora'),
        ('AA5C15BC', 'Carlos Souza', 'Mecânico'),
        ('F1B2715B', 'Lucas Ferreira', 'Auxiliar')
    ]
    
    for uid, nome, cargo in usuarios:
        try:
            cursor.execute(
                'INSERT OR IGNORE INTO usuarios (uid, nome, cargo, ativo) VALUES (?, ?, ?, 1)',
                (uid, nome, cargo)
            )
        except:
            pass
    
    # Máquina de exemplo
    try:
        cursor.execute(
            'INSERT OR IGNORE INTO maquinas (machine_id, nome, local, ativa) VALUES (?, ?, ?, 1)',
            ('DEMO-01', 'Torno Mecânico', 'Oficina A')
        )
    except:
        pass
    
    db.commit()
    print('✅ Dados iniciais inseridos')

# ==================== ROTAS API ====================

@app.route('/')
def index():
    """Página inicial"""
    db = get_db()
    
    total_usuarios = db.execute('SELECT COUNT(*) as count FROM usuarios').fetchone()['count']
    total_maquinas = db.execute('SELECT COUNT(*) as count FROM maquinas').fetchone()['count']
    total_logs = db.execute('SELECT COUNT(*) as count FROM logs').fetchone()['count']
    
    db.close()
    
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Controle de Acesso - API</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <meta charset="utf-8">
        <style>
            body {{ 
                font-family: Arial; 
                max-width: 800px; 
                margin: 50px auto; 
                padding: 20px;
                background: #f0f0f0;
            }}
            .card {{
                background: white;
                padding: 20px;
                border-radius: 8px;
                margin: 10px 0;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            }}
            h1 {{ color: #333; }}
            .stats {{
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 10px;
                margin: 20px 0;
            }}
            .stat {{
                background: #e8f4f8;
                padding: 15px;
                border-radius: 5px;
                text-align: center;
            }}
            .stat h3 {{ margin: 0; color: #2c3e50; }}
            .stat p {{ margin: 10px 0 0 0; font-size: 2em; color: #3498db; font-weight: bold; }}
            .endpoint {{ 
                background: #e8f4f8; 
                padding: 10px; 
                margin: 5px 0;
                border-radius: 4px;
                font-family: monospace;
            }}
            .method {{ 
                display: inline-block;
                padding: 2px 8px;
                border-radius: 3px;
                font-size: 12px;
                font-weight: bold;
            }}
            .get {{ background: #61affe; color: white; }}
            .post {{ background: #49cc90; color: white; }}
            a {{ color: #3498db; text-decoration: none; }}
            a:hover {{ text-decoration: underline; }}
        </style>
    </head>
    <body>
        <div class="card">
            <h1>🔐 Sistema de Controle de Acesso</h1>
            <p>Servidor rodando no Samsung A20</p>
            <p><strong>Status:</strong> ✅ Online</p>
            <p><strong>Porta:</strong> {PORT}</p>
            <p><strong>Database:</strong> SQLite3 (Python)</p>
        </div>
        
        <div class="stats">
            <div class="stat">
                <h3>👥 Usuários</h3>
                <p>{total_usuarios}</p>
            </div>
            <div class="stat">
                <h3>🏭 Máquinas</h3>
                <p>{total_maquinas}</p>
            </div>
            <div class="stat">
                <h3>📊 Logs</h3>
                <p>{total_logs}</p>
            </div>
        </div>
        
        <div class="card">
            <h2>📡 Endpoints da API</h2>
            
            <div class="endpoint">
                <span class="method get">GET</span>
                <strong>/api/validar/&lt;uid&gt;</strong> - Validar usuário
            </div>
            
            <div class="endpoint">
                <span class="method get">GET</span>
                <strong>/api/usuarios</strong> - Listar todos usuários
            </div>
            
            <div class="endpoint">
                <span class="method post">POST</span>
                <strong>/api/usuarios</strong> - Cadastrar usuário
            </div>
            
            <div class="endpoint">
                <span class="method post">POST</span>
                <strong>/api/log</strong> - Registrar log
            </div>
            
            <div class="endpoint">
                <span class="method get">GET</span>
                <strong>/api/logs</strong> - Listar logs recentes
            </div>
            
            <div class="endpoint">
                <span class="method get">GET</span>
                <strong>/api/maquinas</strong> - Listar máquinas
            </div>
        </div>
        
        <div class="card">
            <h2>📊 Dashboard</h2>
            <p><a href="/dashboard">Ver Dashboard Completo →</a></p>
        </div>
    </body>
    </html>
    '''

@app.route('/api/validar/<uid>')
def validar_usuario(uid):
    """Validar usuário - ESP32 usa esta rota"""
    uid = uid.upper()
    
    db = get_db()
    usuario = db.execute(
        'SELECT * FROM usuarios WHERE uid = ? AND ativo = 1',
        (uid,)
    ).fetchone()
    db.close()
    
    if usuario:
        print(f"✅ Usuário validado: {usuario['nome']} ({uid})")
        return jsonify({
            'autorizado': True,
            'usuario': {
                'uid': usuario['uid'],
                'nome': usuario['nome'],
                'cargo': usuario['cargo']
            }
        })
    else:
        print(f"❌ UID não autorizado: {uid}")
        return jsonify({'autorizado': False})

@app.route('/api/usuarios', methods=['GET', 'POST'])
def usuarios():
    """Listar ou cadastrar usuários"""
    
    if request.method == 'GET':
        db = get_db()
        usuarios = db.execute('SELECT * FROM usuarios ORDER BY nome').fetchall()
        db.close()
        
        return jsonify([dict(u) for u in usuarios])
    
    elif request.method == 'POST':
        data = request.get_json()
        uid = data.get('uid', '').upper()
        nome = data.get('nome')
        cargo = data.get('cargo', '')
        
        if not uid or not nome:
            return jsonify({'erro': 'UID e nome são obrigatórios'}), 400
        
        db = get_db()
        try:
            cursor = db.cursor()
            cursor.execute(
                'INSERT INTO usuarios (uid, nome, cargo, ativo) VALUES (?, ?, ?, 1)',
                (uid, nome, cargo)
            )
            db.commit()
            user_id = cursor.lastrowid
            db.close()
            
            print(f"✅ Usuário cadastrado: {nome} ({uid})")
            return jsonify({
                'sucesso': True,
                'id': user_id,
                'mensagem': 'Usuário cadastrado com sucesso'
            })
        except sqlite3.IntegrityError:
            db.close()
            return jsonify({'erro': 'UID já cadastrado'}), 400

@app.route('/api/log', methods=['POST'])
def registrar_log():
    """Registrar log - ESP32 envia para cá"""
    data = request.get_json()
    
    timestamp = data.get('timestamp', int(datetime.now().timestamp()))
    machine_id = data.get('machine_id')
    uid = data.get('uid')
    usuario = data.get('usuario')
    evento = data.get('evento')
    rssi = data.get('rssi', 0)
    duracao = data.get('duracao', 0)
    
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        '''INSERT INTO logs (timestamp, machine_id, uid, usuario, evento, rssi, duracao)
           VALUES (?, ?, ?, ?, ?, ?, ?)''',
        (timestamp, machine_id, uid, usuario, evento, rssi, duracao)
    )
    db.commit()
    log_id = cursor.lastrowid
    db.close()
    
    print(f"📝 Log registrado: {evento} - {usuario} ({machine_id})")
    return jsonify({'sucesso': True, 'id': log_id})

@app.route('/api/logs')
def listar_logs():
    """Listar logs recentes"""
    limite = request.args.get('limite', 50, type=int)
    
    db = get_db()
    logs = db.execute(
        'SELECT * FROM logs ORDER BY criado_em DESC LIMIT ?',
        (limite,)
    ).fetchall()
    db.close()
    
    return jsonify([dict(log) for log in logs])

@app.route('/api/maquinas')
def listar_maquinas():
    """Listar máquinas"""
    db = get_db()
    maquinas = db.execute('SELECT * FROM maquinas ORDER BY nome').fetchall()
    db.close()
    
    return jsonify([dict(m) for m in maquinas])

@app.route('/api/usuarios/<int:user_id>', methods=['DELETE'])
def deletar_usuario(user_id):
    """Deletar usuário"""
    db = get_db()
    db.execute('DELETE FROM usuarios WHERE id = ?', (user_id,))
    db.commit()
    db.close()
    
    print(f"🗑️ Usuário {user_id} deletado")
    return jsonify({'sucesso': True, 'mensagem': 'Usuário deletado'})

@app.route('/dashboard')
def dashboard():
    """Dashboard HTML completo"""
    html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Dashboard - Controle de Acesso</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <meta charset="utf-8">
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { 
                font-family: Arial; 
                background: #1a1a2e;
                color: #eee;
                padding: 20px;
            }
            .container { max-width: 1400px; margin: 0 auto; }
            h1 { margin-bottom: 30px; color: #4ecca3; text-align: center; }
            .grid { 
                display: grid; 
                grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
                gap: 20px;
                margin-bottom: 30px;
            }
            .card {
                background: #16213e;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.3);
            }
            .card h2 { 
                color: #4ecca3; 
                margin-bottom: 15px;
                font-size: 1.3em;
            }
            table {
                width: 100%;
                border-collapse: collapse;
                margin-top: 10px;
            }
            th, td {
                padding: 12px 8px;
                text-align: left;
                border-bottom: 1px solid #0f3460;
            }
            th { 
                background: #0f3460; 
                color: #4ecca3;
                font-weight: bold;
            }
            tr:hover { background: #0f3460; }
            .badge {
                display: inline-block;
                padding: 5px 10px;
                border-radius: 4px;
                font-size: 0.85em;
                font-weight: bold;
            }
            .ativo { background: #4ecca3; color: #000; }
            .inativo { background: #e74c3c; color: #fff; }
            .btn {
                background: #4ecca3;
                color: #000;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                cursor: pointer;
                font-weight: bold;
                margin: 5px;
            }
            .btn:hover { background: #45b393; }
            .btn-delete { background: #e74c3c; color: #fff; }
            #logs { max-height: 500px; overflow-y: auto; }
            .form-add {
                background: #0f3460;
                padding: 15px;
                border-radius: 5px;
                margin-bottom: 15px;
            }
            .form-add input {
                padding: 8px;
                margin: 5px;
                border: none;
                border-radius: 3px;
                background: #16213e;
                color: #fff;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🔐 Dashboard - Sistema de Controle de Acesso</h1>
            
            <div class="grid">
                <div class="card">
                    <h2>👥 Usuários Cadastrados</h2>
                    <div class="form-add">
                        <input type="text" id="novoUid" placeholder="UID (ex: FA089CBC)" maxlength="8">
                        <input type="text" id="novoNome" placeholder="Nome completo">
                        <input type="text" id="novoCargo" placeholder="Cargo">
                        <button class="btn" onclick="adicionarUsuario()">➕ Adicionar</button>
                    </div>
                    <div id="usuarios">Carregando...</div>
                </div>
                
                <div class="card">
                    <h2>🏭 Máquinas Cadastradas</h2>
                    <div id="maquinas">Carregando...</div>
                </div>
            </div>
            
            <div class="card">
                <h2>📊 Logs Recentes</h2>
                <button class="btn" onclick="carregarLogs()">🔄 Atualizar</button>
                <div id="logs">Carregando...</div>
            </div>
        </div>
        
        <script>
            function carregarUsuarios() {
                fetch('/api/usuarios')
                    .then(r => r.json())
                    .then(data => {
                        let html = '<table><tr><th>UID</th><th>Nome</th><th>Cargo</th><th>Status</th><th>Ações</th></tr>';
                        data.forEach(u => {
                            html += `<tr>
                                <td><strong>${u.uid}</strong></td>
                                <td>${u.nome}</td>
                                <td>${u.cargo || '-'}</td>
                                <td><span class="badge ${u.ativo ? 'ativo' : 'inativo'}">${u.ativo ? 'ATIVO' : 'INATIVO'}</span></td>
                                <td><button class="btn btn-delete" onclick="deletarUsuario(${u.id})">🗑️</button></td>
                            </tr>`;
                        });
                        html += '</table>';
                        document.getElementById('usuarios').innerHTML = html;
                    });
            }
            
            function carregarMaquinas() {
                fetch('/api/maquinas')
                    .then(r => r.json())
                    .then(data => {
                        let html = '<table><tr><th>ID</th><th>Nome</th><th>Local</th><th>Status</th></tr>';
                        data.forEach(m => {
                            html += `<tr>
                                <td><strong>${m.machine_id}</strong></td>
                                <td>${m.nome}</td>
                                <td>${m.local || '-'}</td>
                                <td><span class="badge ${m.ativa ? 'ativo' : 'inativo'}">${m.ativa ? 'ATIVA' : 'INATIVA'}</span></td>
                            </tr>`;
                        });
                        html += '</table>';
                        document.getElementById('maquinas').innerHTML = html;
                    });
            }
            
            function carregarLogs() {
                fetch('/api/logs?limite=50')
                    .then(r => r.json())
                    .then(data => {
                        let html = '<table><tr><th>Data/Hora</th><th>Máquina</th><th>Usuário</th><th>Evento</th><th>RSSI</th></tr>';
                        data.forEach(log => {
                            const data = new Date(log.timestamp * 1000).toLocaleString('pt-BR');
                            html += `<tr>
                                <td>${data}</td>
                                <td>${log.machine_id}</td>
                                <td>${log.usuario || log.uid}</td>
                                <td>${log.evento}</td>
                                <td>${log.rssi ? log.rssi + ' dBm' : '-'}</td>
                            </tr>`;
                        });
                        html += '</table>';
                        document.getElementById('logs').innerHTML = html;
                    });
            }
            
            function adicionarUsuario() {
                const uid = document.getElementById('novoUid').value.toUpperCase();
                const nome = document.getElementById('novoNome').value;
                const cargo = document.getElementById('novoCargo').value;
                
                if (!uid || !nome) {
                    alert('Preencha UID e Nome!');
                    return;
                }
                
                fetch('/api/usuarios', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ uid, nome, cargo })
                })
                .then(r => r.json())
                .then(data => {
                    if (data.sucesso) {
                        alert('✅ Usuário cadastrado!');
                        document.getElementById('novoUid').value = '';
                        document.getElementById('novoNome').value = '';
                        document.getElementById('novoCargo').value = '';
                        carregarUsuarios();
                    } else {
                        alert('❌ ' + data.erro);
                    }
                });
            }
            
            function deletarUsuario(id) {
                if (!confirm('Deletar este usuário?')) return;
                
                fetch('/api/usuarios/' + id, { method: 'DELETE' })
                    .then(() => carregarUsuarios());
            }
            
            carregarUsuarios();
            carregarMaquinas();
            carregarLogs();
            
            setInterval(carregarLogs, 10000);
        </script>
    </body>
    </html>
    '''
    return html

# ==================== INICIAR SERVIDOR ====================

if __name__ == '__main__':
    print('\n╔════════════════════════════════════════════════════╗')
    print('║  🚀 SERVIDOR DE CONTROLE DE ACESSO - PYTHON       ║')
    print('╚════════════════════════════════════════════════════╝\n')
    
    # Inicializar banco de dados
    if not os.path.exists(DATABASE):
        print('📦 Criando banco de dados...')
        init_db()
    else:
        print('✅ Banco de dados já existe')
    
    print(f'\n✅ Servidor Flask rodando na porta {PORT}')
    print(f'🌐 Acesse: http://localhost:{PORT}')
    print(f'📱 Dashboard: http://localhost:{PORT}/dashboard')
    print('\n📋 Pressione Ctrl+C para parar o servidor\n')
    
    # Iniciar servidor
    app.run(host='0.0.0.0', port=PORT, debug=False)