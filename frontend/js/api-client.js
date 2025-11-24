/**
 * Cliente API com prioridade de Origem (Domain-First)
 * Corrige erro 401 de Cookies
 */

class APIClient {
    constructor() {
        // LISTA DE SERVIDORES
        // O primeiro item deve ser SEMPRE a origem atual (seja ela domínio ou IP)
        // Isso garante que o cookie seja enviado corretamente.
        this.servers = [
            { url: window.location.origin, name: 'current-origin' }, // http://www.meutrabalho.com.br
            { url: 'http://172.20.0.10', name: 'http1' },
            { url: 'http://172.20.0.11', name: 'http2' },
            { url: 'http://172.20.0.12', name: 'http3' }
        ];
        
        // Remove duplicatas se eu já estiver acessando pelo IP direto
        this.servers = this.servers.filter((v,i,a)=>a.findIndex(t=>(t.url===v.url))===i);

        console.log('🌐 Estratégia de Conexão:', this.servers.map(s => s.url));
        
        this.baseUrl = this.servers[0].url; 
    }

    createTimeout(ms) {
        return new Promise((_, reject) => {
            setTimeout(() => reject(new Error('Timeout')), ms);
        });
    }

    // Tenta encontrar um servidor vivo se o atual falhar
    async findActiveServer() {
        console.log('🔍 Buscando servidor alternativo...');
        
        // Começa do índice 1 porque o 0 (origem atual) teoricamente falhou
        for (let i = 1; i < this.servers.length; i++) {
            try {
                const response = await Promise.race([
                    fetch(`${this.servers[i].url}/api/health`, { credentials: 'include' }),
                    this.createTimeout(1500)
                ]);
                
                if (response && response.ok) {
                    console.log(`✅ Servidor de resgate encontrado: ${this.servers[i].url}`);
                    this.baseUrl = this.servers[i].url;
                    return this.baseUrl;
                }
            } catch (e) {
                console.log(`❌ ${this.servers[i].url} inativo.`);
            }
        }
        throw new Error('Todos os servidores estão inativos.');
    }

    async request(endpoint, options = {}) {
        const maxRetries = 2; // Tenta a origem atual, depois tenta failover

        for (let attempt = 0; attempt < maxRetries; attempt++) {
            try {
                // Se URL base for a mesma da janela, usa caminho relativo (melhor pra cookies)
                let url;
                if (this.baseUrl === window.location.origin) {
                    url = endpoint; // ex: /api/login
                } else {
                    url = `${this.baseUrl}${endpoint}`; // ex: http://172.20.0.10/api/login
                }

                console.log(`🔄 Request: ${url}`);
                
                const response = await Promise.race([
                    fetch(url, { ...options, credentials: 'include' }),
                    this.createTimeout(5000)
                ]);

                // 401 é "sucesso de rede" (servidor respondeu), então retornamos a resposta
                // para a aplicação tratar (redirecionar pra login)
                if (response.ok || response.status === 401 || response.status === 400 || response.status === 404) {
                    return response;
                }

                // Se for erro 500 ou falha de rede, lança erro para cair no catch e tentar outro server
                throw new Error(`Erro de Servidor: ${response.status}`);

            } catch (error) {
                console.log(`⚠️ Falha na tentativa ${attempt}:`, error.message);
                
                // Se falhou na origem atual, tenta achar um IP alternativo
                if (attempt === 0) {
                    try {
                        await this.findActiveServer();
                        // Se achou novo servidor, loop continua e tenta de novo
                    } catch (fatal) {
                        break; // Ninguém responde
                    }
                }
            }
        }
        
        // Se chegamos aqui, falha total
        if (window.location.pathname !== '/fallback.html') {
             // Redirecionamento de emergência via browser
             // Tenta o primeiro IP fixo se o domínio morreu
             window.location.href = 'http://172.20.0.10/fallback.html';
        }
        throw new Error('Falha total de conexão');
    }

    async get(endpoint) {
        return this.request(endpoint, { method: 'GET' });
    }

    async post(endpoint, data) {
        return this.request(endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
    }
}

const apiClient = new APIClient();