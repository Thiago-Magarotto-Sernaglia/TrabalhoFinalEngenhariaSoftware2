/**
 * Sistema de Autenticação Compartilhado
 * Gerencia sessão do usuário em todas as páginas
 */

// API_URL global para uso em todas as páginas
window.API_URL = window.API_URL || "http://localhost:8000";
const API_URL = window.API_URL;

// ==================================================================
// FUNÇÕES DE VERIFICAÇÃO DE SESSÃO
// ==================================================================

/**
 * Verifica se o usuário está autenticado
 * Retorna os dados do usuário ou null
 */
async function verificarSessao() {
    try {
        // Verifica se tem usuário no localStorage
        const usuarioLocal = localStorage.getItem('usuario');
        if (usuarioLocal) {
            const usuario = JSON.parse(usuarioLocal);
            // Valida se tem pelo menos um campo identificador
            if (usuario && (usuario.id || usuario.nome || usuario.email)) {
                console.log('Usuário encontrado no localStorage:', usuario);
                return usuario;
            } else {
                console.log('Usuário no localStorage inválido:', usuario);
            }
        } else {
            console.log('Nenhum usuário encontrado no localStorage');
        }

        return null;
    } catch (error) {
        console.error('Erro ao verificar sessão:', error);
        return null;
    }
}

/**
 * Verifica se o usuário está logado e redireciona se não estiver
 * @param {boolean} redirect - Se true, redireciona para login se não autenticado
 */
async function verificarAutenticacao(redirect = true) {
    const usuario = await verificarSessao();
    
    if (!usuario && redirect) {
        // Salva a URL atual para redirecionar após login
        sessionStorage.setItem('redirectAfterLogin', window.location.href);
        window.location.href = 'login.html';
        return null;
    }
    
    return usuario;
}

/**
 * Faz logout do usuário
 */
async function fazerLogout() {
    try {
        // Tenta remover do backend (se o endpoint existir)
        try {
            await fetch(`${API_URL}/logout`, {
                method: 'POST',
                credentials: 'include'
            });
        } catch (error) {
            // Se não existir endpoint, continua mesmo assim
            console.log('Endpoint /logout não disponível, usando apenas localStorage');
        }
    } catch (error) {
        console.error('Erro ao fazer logout no backend:', error);
    } finally {
        // Remove do localStorage
        localStorage.removeItem('usuario');
        // Opcional: limpar carrinho também
        // localStorage.removeItem('carrinho');
        
        // Redireciona para login
        window.location.href = 'login.html';
    }
}

/**
 * Atualiza a navbar com informações do usuário logado
 */
async function atualizarNavbar() {
    const usuario = await verificarSessao();
    
    // Procura pelos elementos do menu
    const menuVisitante = document.getElementById('menu-visitante');
    const menuUsuario = document.getElementById('menu-usuario');
    const loginLink = document.getElementById('nav-login');
    const userInfo = document.getElementById('nav-user');
    const userName = document.getElementById('user-name');
    
    if (usuario) {
        // Usuário logado - mostra menu de usuário
        if (menuVisitante) {
            menuVisitante.style.display = 'none';
            menuVisitante.classList.add('hidden');
        }
        if (menuUsuario) {
            menuUsuario.classList.remove('hidden');
            menuUsuario.style.display = 'flex';
        }
        
        // Tenta pegar nome do usuário (pode ser nome, username ou email)
        const nomeUsuario = usuario.nome ? usuario.nome.split(' ')[0] : (usuario.username || usuario.email || 'Usuário');
        
        // Atualiza nav-user se existir (algumas páginas usam isso)
        if (userInfo) {
            userInfo.textContent = `Olá, ${nomeUsuario}`;
        }
        // Atualiza user-name se existir (index.html usa isso dentro de um <strong>)
        if (userName) {
            userName.textContent = nomeUsuario;
        }
    } else {
        // Usuário não logado - mostra menu de visitante
        if (menuVisitante) {
            menuVisitante.classList.remove('hidden');
            menuVisitante.style.display = 'flex';
        }
        if (menuUsuario) {
            menuUsuario.classList.add('hidden');
            menuUsuario.style.display = 'none';
        }
    }
    
    console.log('Navbar atualizada. Usuário:', usuario ? 'logado' : 'não logado');
}

/**
 * Inicializa o sistema de autenticação na página
 * Deve ser chamado quando a página carregar
 */
async function initAuth() {
    // Aguarda um pouco para garantir que o DOM está totalmente carregado
    if (document.readyState === 'loading') {
        await new Promise(resolve => {
            if (document.readyState === 'complete') {
                resolve();
            } else {
                document.addEventListener('DOMContentLoaded', resolve);
            }
        });
    }
    
    await atualizarNavbar();
    
    // Adiciona listener para logout se existir botão
    const logoutBtn = document.getElementById('btn-logout') || document.querySelector('.btn-logout');
    if (logoutBtn) {
        // Remove listeners anteriores para evitar duplicação
        const newLogoutBtn = logoutBtn.cloneNode(true);
        logoutBtn.parentNode.replaceChild(newLogoutBtn, logoutBtn);
        
        newLogoutBtn.addEventListener('click', async (e) => {
            e.preventDefault();
            await fazerLogout();
        });
    }
}

// Exporta funções para uso global
window.verificarSessao = verificarSessao;
window.verificarAutenticacao = verificarAutenticacao;
window.fazerLogout = fazerLogout;
window.atualizarNavbar = atualizarNavbar;
window.initAuth = initAuth;

