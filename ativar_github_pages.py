"""
Script para ativar o GitHub Pages via API do GitHub
"""
import requests
import os
import sys

# Configurações
OWNER = "OmniChat"
REPO = "analise-conversas-after-sales"
GITHUB_API_URL = f"https://api.github.com/repos/{OWNER}/{REPO}/pages"

def ativar_github_pages(token):
    """Ativa o GitHub Pages para o repositório"""
    
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    
    data = {
        "source": {
            "branch": "main",
            "path": "/"
        }
    }
    
    try:
        # Verificar status atual
        response = requests.get(GITHUB_API_URL, headers=headers)
        
        if response.status_code == 200:
            print("✅ GitHub Pages já está ativado!")
            print(f"Status: {response.json().get('status', 'unknown')}")
            print(f"URL: {response.json().get('html_url', 'N/A')}")
            return True
        
        # Ativar GitHub Pages
        response = requests.put(GITHUB_API_URL, headers=headers, json=data)
        
        if response.status_code == 201:
            print("✅ GitHub Pages ativado com sucesso!")
            print(f"URL do site: https://{OWNER}.github.io/{REPO}/")
            return True
        elif response.status_code == 200:
            print("✅ Configuração do GitHub Pages atualizada!")
            return True
        else:
            print(f"❌ Erro ao ativar GitHub Pages: {response.status_code}")
            print(f"Resposta: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Erro: {str(e)}")
        return False

if __name__ == "__main__":
    # Tentar obter token de variável de ambiente
    token = os.environ.get("GITHUB_TOKEN")
    
    if not token:
        print("⚠️  Token do GitHub não encontrado na variável de ambiente GITHUB_TOKEN")
        print("\nPara usar este script:")
        print("1. Crie um Personal Access Token no GitHub:")
        print("   https://github.com/settings/tokens")
        print("2. Dê permissão 'repo' e 'admin:repo_hook'")
        print("3. Execute: $env:GITHUB_TOKEN='seu_token'; python ativar_github_pages.py")
        print("\nOu ative manualmente em:")
        print(f"https://github.com/{OWNER}/{REPO}/settings/pages")
        sys.exit(1)
    
    ativar_github_pages(token)




