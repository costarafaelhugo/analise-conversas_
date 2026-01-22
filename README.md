# Analista de Conversas - QA Chatbot

Aplicação web para análise automatizada de qualidade de atendimento de chatbots usando a API do Google Gemini.

## 🚀 Instalação

1. Instale as dependências:
```bash
pip install -r requirements.txt
```

2. Execute a aplicação:
```bash
streamlit run app.py
```

## 📋 Pré-requisitos

- Python 3.8 ou superior
- Conta no Google AI Studio para obter uma API Key
- Arquivo de conversas no formato `.txt` ou `.csv`

## 🔑 Obter API Key do Google Gemini

1. Acesse: https://makersuite.google.com/app/apikey
2. Crie uma nova API Key
3. Cole a chave na barra lateral da aplicação

## 📁 Formato dos Arquivos

### Arquivo TXT
As conversas devem ser separadas por uma linha contendo `---` (três traços):

```
Cliente: Olá
Bot: Olá! Como posso ajudar?
---
Cliente: Preciso de ajuda
Bot: Claro, estou aqui!
```

### Arquivo CSV
O arquivo deve conter uma coluna chamada `conversa`:

```csv
conversa
"Cliente: Olá\nBot: Olá! Como posso ajudar?"
"Cliente: Preciso de ajuda\nBot: Claro, estou aqui!"
```

## 📊 Campos de Análise

A aplicação retorna os seguintes campos para cada conversa:

- **necessidade_transbordo**: Indica se houve necessidade de transbordo (Sim/Não)
- **transferencia**: Indica se o bot transferiu para fila humana (Sim/Não)
- **agente_agiu_corretamente**: Avalia se o bot agiu corretamente (Sim/Não)
- **motivo_transbordo**: Motivo do transbordo quando aplicável
- **problema_mapeado**: Problema identificado na conversa
- **precisa_atencao**: Indica se a conversa precisa de atenção especial (Sim/Não)
- **observacao**: Resumo curto da análise

## 🎯 Funcionalidades

- ✅ Upload de arquivos TXT ou CSV
- ✅ Análise automatizada usando Google Gemini
- ✅ Barra de progresso durante o processamento
- ✅ Visualização de resultados em tabela
- ✅ Filtro para conversas que precisam atenção
- ✅ Download do relatório em CSV ou Excel
- ✅ Estatísticas rápidas da análise

## 📝 Exemplo de Uso

1. Abra a aplicação no navegador
2. Insira sua Google API Key na barra lateral
3. Escolha o modelo Gemini (padrão: gemini-1.5-flash)
4. Faça upload do arquivo com as conversas
5. Clique em "Iniciar Análise"
6. Aguarde o processamento
7. Visualize os resultados e faça o download do relatório

## 🔧 Modelos Disponíveis

- `gemini-1.5-flash` (recomendado - mais rápido e econômico)
- `gemini-1.5-pro` (mais preciso, mais lento)
- `gemini-pro` (versão anterior)

## 📄 Licença

Este projeto é de uso interno.







