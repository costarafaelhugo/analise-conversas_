# Deploy da Aplicação Streamlit

## Deploy no Streamlit Cloud (Recomendado)

### Passo a Passo:

1. **Acesse o Streamlit Cloud:**
   - Vá para: https://share.streamlit.io/
   - Faça login com sua conta GitHub

2. **Conecte o Repositório:**
   - Clique em "New app"
   - Selecione o repositório: `OmniChat/analise-conversas-after-sales`
   - Branch: `main`
   - Main file path: `app.py`

3. **Configure a Aplicação:**
   - App name: (deixe o padrão ou escolha um nome)
   - Clique em "Deploy"

4. **Aguarde o Deploy:**
   - O Streamlit Cloud irá instalar as dependências do `requirements.txt`
   - A aplicação estará disponível em: `https://<app-name>.streamlit.app`

### Notas Importantes:

- A aplicação será atualizada automaticamente quando você fizer push para a branch `main`
- Não é necessário configurar variáveis de ambiente para a API Key do OpenAI (o usuário insere na interface)
- A aplicação é totalmente funcional e permite upload de arquivos CSV/TXT

## URL da Aplicação

Após o deploy, você receberá uma URL no formato:
```
https://<app-name>.streamlit.app
```




