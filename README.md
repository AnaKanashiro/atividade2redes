# Trabalho 02 - Arquitetura Distribuída com Balanceamento DNS e Sessão Centralizada

## 📋 Visão Geral

Aplicação web distribuída implementada com **Docker Compose** contendo **5 servidores distintos**:
- **3 servidores HTTP** (backend Flask - portas 5000, 5001, 5002)
- **1 servidor DNS** (BIND9 - Round Robin)
- **1 servidor Banco de Dados** (PostgreSQL)

### 🎯 Objetivos

1. ✅ Aplicação web funcional (3 camadas: Frontend, Backend, Banco)
2. ✅ 3 servidores HTTP rodando a mesma aplicação
3. ✅ DNS Round Robin distribuindo requisições
4. ✅ Sessão centralizada (compartilhada entre servidores via PostgreSQL)
5. ✅ Testes unitários automatizados
6. ✅ Documentação de rede
7. ⭐ **EXTRA**: Detecção automática de falha de servidor

---

## 🏗️ Arquitetura

### Topologia de Rede

```
                    [Cliente/Browser]
                           |
                           | www.meutrabalho.com.br
                           |
                    [Servidor DNS]
                    (Round Robin - 172.20.0.5)
                           |
        ┌──────────────────┼──────────────────┐
        |                  |                  |
   [HTTP Server 1]   [HTTP Server 2]   [HTTP Server 3]
   (172.20.0.10)     (172.20.0.11)     (172.20.0.12)
   Porta: 5000       Porta: 5001       Porta: 5002
        |                  |                  |
        └──────────────────┼──────────────────┘
                           |
                    [Banco de Dados]
                    (172.20.0.20:5432)
              (Sessões + Usuários)
```

### Estrutura dos Containers

| Container | IP Docker | Porta Host | Função |
|-----------|-----------|------------|--------|
| `trabalho-database` | 172.20.0.20 | 5432 | PostgreSQL |
| `trabalho-http1` | 172.20.0.10 | 5000 | Servidor HTTP 1 |
| `trabalho-http2` | 172.20.0.11 | 5001 | Servidor HTTP 2 |
| `trabalho-http3` | 172.20.0.12 | 5002 | Servidor HTTP 3 |
| `trabalho-dns` | 172.20.0.5 | 53 | BIND9 DNS |

---

## 📦 Pré-requisitos

1. **Docker Desktop** instalado e rodando
2. **Docker Compose** (v2.0+)
3. **Python 3** (para gerar hashes de senha)

### Verificar Instalação

```powershell
docker --version
docker compose version
docker ps  # Deve funcionar sem erros
```

---

## 🚀 Instalação e Configuração

### Passo 1: Gerar Hashes de Senha

Execute o script para gerar hashes das senhas de teste:

```powershell
python gerar_hash.py
```

Copie os hashes gerados e atualize `database/seed.sql`.

### Passo 2: Configurar Hosts File

**Windows:** Edite `C:\Windows\System32\drivers\etc\hosts` (como Administrador):

```
127.0.0.1    www.meutrabalho.com.br
```

**Linux/Mac:** Edite `/etc/hosts`:

```
127.0.0.1    www.meutrabalho.com.br
```

### Passo 3: Iniciar os Containers

```powershell
# Construir e iniciar todos os containers
docker compose up --build -d

# Verificar status
docker compose ps
```

Aguarde cerca de 30 segundos para o banco de dados inicializar.

---

## 🎮 Como Usar

### Acessar a Aplicação

Você pode acessar a aplicação de 3 formas:

1. **Via DNS (Round Robin):**
   ```
   http://www.meutrabalho.com.br:5000
   ```

2. **Diretamente pelas portas:**
   ```
   http://localhost:5000  (HTTP Server 1)
   http://localhost:5001  (HTTP Server 2)
   http://localhost:5002  (HTTP Server 3)
   ```

### Credenciais de Teste

- **Login:** `usuario1` / **Senha:** `senha1`
- **Login:** `usuario2` / **Senha:** `senha2`

---

## 🧪 Testes

### Teste 1: Persistência de Sessão

1. Faça login na aplicação via `http://localhost:5000`
2. Anote o **hostname** exibido (ex: `http1-server`)
3. **Acesse outro servidor:** `http://localhost:5001`
4. **Verifique:**
   - ✅ Hostname mudou (ex: agora é `http2-server`)
   - ✅ Você **permanece logado**
   - ✅ Dados do perfil aparecem corretamente

### Teste 2: Detecção de Falha (Ponto Extra)

1. Faça login e vá para a página de perfil
2. **Abra o Console do navegador** (F12)
3. **Pare um servidor:**
   ```powershell
   docker compose stop http1
   ```
4. **Atualize a página** (F5)
5. **Resultado esperado:**
   - ✅ Console mostra tentativas de conexão
   - ✅ Redireciona automaticamente para servidor ativo
   - ✅ Você continua logado
   - ✅ Hostname mudou para servidor ativo

---

## 🛠️ Comandos Úteis

```powershell
# Ver status
docker compose ps

# Ver logs
docker compose logs -f

# Ver logs de um container específico
docker compose logs http1

# Parar tudo
docker compose down

# Parar e remover volumes
docker compose down -v

# Reiniciar um container
docker compose restart http1

# Reconstruir e reiniciar
docker compose up -d --build
```

---

## 🔧 Solução de Problemas

### Docker Desktop não está rodando

**Solução:** Abra o Docker Desktop e aguarde até aparecer "Docker Desktop is running"

### "Not Found" ao acessar URL

**Solução:**
1. Verifique se containers estão rodando: `docker compose ps`
2. Verifique hosts file
3. Tente: `http://localhost:5000`

### Erro de CORS

**Solução:**
```powershell
docker compose down
docker compose up --build -d
```

### DNS não está funcionando

**Solução:**
1. Verifique se o container DNS está rodando: `docker compose ps`
2. Verifique logs: `docker compose logs dns`
3. Teste DNS: `nslookup www.meutrabalho.com.br 127.0.0.1`

---

## 📁 Estrutura do Projeto

```
atividade2redes/
├── backend/
│   ├── app.py              # Aplicação Flask
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── index.html
│   ├── perfil.html
│   ├── fallback.html
│   └── js/
│       └── api-client.js
├── database/
│   ├── init.sql
│   └── seed.sql
├── dns/
│   ├── Dockerfile
│   ├── named.conf
│   └── db.meutrabalho.com.br
├── docker-compose.yml
├── gerar_hash.py
├── diagnostico.ps1
└── README.md
```

---

## ✅ Checklist de Avaliação

- [x] 3 servidores HTTP funcionando
- [x] 1 servidor DNS funcionando
- [x] 1 servidor de banco funcionando
- [x] Acesso via `www.meutrabalho.com.br` funciona
- [x] Acesso direto via portas funciona
- [x] Login funciona
- [x] Sessão persiste entre servidores
- [x] Detecção de falha implementada

---

**Desenvolvido com Docker Compose! 🐳**


para MacBook:

3 tipos de flush necessários, na ordem de execução

1 - Flush de DNS do Sistema Operacional (macOS)
sudo dscacheutil -flushcache; sudo killall -HUP mDNSResponder

2 - Flush de DNS do Navegador (Chrome Internal)
Aba: chrome://net-internals/#dns
Botão: "Clear host cache"

3 - Flush de Sockets / TCP (O "Matador de Round Robin")
Aba: chrome://net-internals/#sockets
Botão: "Flush socket pools"

www.meutrabalho.com.br 