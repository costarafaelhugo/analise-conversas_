# Solução para Problemas no Deploy do Streamlit Cloud

## Problemas Identificados:

1. ❌ "This repository does not exist"
2. ❌ "This branch does not exist"  
3. ❌ "This file does not exist"
4. ❌ "This subdomain contains profanity"

## Soluções:

### 1. Autorizar o Streamlit Cloud a acessar o repositório

O repositório pode ser privado ou o Streamlit Cloud precisa de permissão:

**Passo a Passo:**
1. No formulário de deploy, clique no link "Paste GitHub URL" ao lado de "Repository"
2. Cole a URL completa: `https://github.com/OmniChat/analise-conversas-after-sales`
3. OU autorize o Streamlit Cloud:
   - Vá em: https://github.com/settings/applications
   - Procure por "Streamlit" ou "Authorized OAuth Apps"
   - Se não estiver autorizado, você será redirecionado para autorizar

### 2. Verificar se o repositório é público

Se o repositório for privado:
- Opção A: Torne o repositório público temporariamente
  - Vá em: https://github.com/OmniChat/analise-conversas-after-sales/settings
  - Role até "Danger Zone"
  - Clique em "Change visibility" → "Make public"
  
- Opção B: Use Streamlit Cloud com repositório privado (requer plano pago)

### 3. Corrigir o nome do subdomínio

O nome "analistadeconvesas" foi rejeitado. Use um dos seguintes:

**Sugestões de nomes:**
- `analise-conversas`
- `analista-conversas`
- `qa-chatbot`
- `conversas-analise`
- `analise-qa`
- `chatbot-qa`

### 4. Verificar se os arquivos estão na branch main

Execute no terminal:
```bash
git branch
git log --oneline -5
```

Certifique-se de que:
- Está na branch `main`
- O arquivo `app.py` está commitado
- O push foi feito com sucesso

## Configuração Correta no Formulário:

- **Repository:** `OmniChat/analise-conversas-after-sales` (ou use a URL completa)
- **Branch:** `main`
- **Main file path:** `app.py`
- **App URL:** Use um dos nomes sugeridos acima (sem espaços, apenas letras, números e hífens)

## Verificação Final:

Após corrigir, verifique:
1. ✅ Repositório acessível pelo Streamlit Cloud
2. ✅ Branch `main` existe e tem o arquivo `app.py`
3. ✅ Nome do subdomínio aceito
4. ✅ Clique em "Deploy"




