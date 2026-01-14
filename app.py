import streamlit as st
import pandas as pd
import re
import json
import time
from io import StringIO, BytesIO
from typing import List, Dict
from datetime import datetime

# Configuração da página
st.set_page_config(
    page_title="Analista de Conversas - QA Chatbot",
    page_icon="🤖",
    layout="wide"
)

# Título da aplicação
st.title("🤖 Analista de Conversas - QA Chatbot")
st.markdown("---")

# Sidebar - Configurações
st.sidebar.header("⚙️ Configurações")

# Seleção do método de análise
metodo_analise = st.sidebar.radio(
    "Método de Análise",
    options=["Local (Regras de Negócio)", "OpenAI API"],
    index=0,
    help="Escolha como deseja analisar as conversas: Local (rápido, sem API) ou OpenAI (IA avançada)"
)

# Configurações para OpenAI API
api_key = None
model_name = None
delay_entre_requisicoes = 1  # Valor padrão

if metodo_analise == "OpenAI API":
    st.sidebar.markdown("---")
    st.sidebar.subheader("🔑 Configurações OpenAI")
    
    # Importar openai apenas se necessário
    try:
        import openai
    except ImportError:
        st.sidebar.error("❌ Biblioteca openai não instalada. Execute: pip install openai")
        st.stop()
    
    api_key = st.sidebar.text_input(
        "OpenAI API Key",
        value="",
        type="password",
        help="Insira sua chave da API do OpenAI"
    )
    
    model_name = st.sidebar.selectbox(
        "Modelo OpenAI",
        options=["gpt-4o-mini", "gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"],
        index=0,
        help="Selecione o modelo do OpenAI (gpt-4o-mini é mais rápido e econômico)"
    )
    
    # Configuração de delay entre requisições
    delay_entre_requisicoes = st.sidebar.slider(
        "Delay entre requisições (segundos)",
        min_value=1,
        max_value=30,
        value=5,
        step=1,
        help="Aumente este valor se estiver recebendo erros de rate limit. Recomendado: 5-10 segundos para contas gratuitas, 3-5 para contas pagas."
    )
    
    st.sidebar.info("💡 **Dica**: Se receber erros de rate limit, aumente o delay ou use análise Local.")
else:
    st.sidebar.info("💡 **Análise Local**: Usa regras de negócio pré-definidas. Rápida e sem necessidade de API.")

# Configuração geral - Limite de conversas
st.sidebar.markdown("---")
st.sidebar.subheader("📊 Configurações de Processamento")

# Inicializar limite de conversas no session state
if 'limite_conversas' not in st.session_state:
    st.session_state['limite_conversas'] = None

# Verificar se há conversas carregadas no session state para mostrar o máximo
max_conversas = 1000  # Valor padrão
help_text = "Deixe vazio para analisar todas as conversas. Útil para testar com poucas conversas ou processar em lotes menores para evitar rate limits."

if 'conversas_carregadas_count' in st.session_state:
    max_conversas = max(1000, st.session_state['conversas_carregadas_count'])
    help_text = f"Deixe vazio para analisar todas as {st.session_state['conversas_carregadas_count']} conversas carregadas. Útil para testar com poucas conversas ou processar em lotes menores para evitar rate limits."

limite_conversas = st.sidebar.number_input(
    "Número máximo de conversas a analisar",
    min_value=1,
    max_value=max_conversas,
    value=None,
    step=1,
    help=help_text
)

# Salvar no session state
st.session_state['limite_conversas'] = limite_conversas if limite_conversas else None

# Mostrar informação sobre o limite
if limite_conversas:
    st.sidebar.info(f"📌 Limite ativo: **{limite_conversas} conversas**")
else:
    st.sidebar.info("📌 Sem limite: **Todas as conversas** serão analisadas")

# Função para extrair JSON do texto (para OpenAI)
def extract_json_from_text(text: str) -> Dict:
    """Extrai JSON do texto retornado pelo Gemini"""
    text = text.strip()
    
    # Tenta encontrar JSON entre ```json e ```
    json_block = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
    if json_block:
        try:
            return json.loads(json_block.group(1))
        except json.JSONDecodeError:
            pass
    
    # Tenta encontrar JSON entre chaves (múltiplas linhas)
    json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass
    
    # Tenta parsear todo o texto como JSON
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    
    return None

# Função para criar prompt do sistema (para Gemini)
def criar_prompt_sistema(conversa: str) -> str:
    """Cria o prompt estruturado para análise da conversa via Gemini"""
    prompt = f"""Você é um analista especializado em qualidade de atendimento de chatbots. 

Analise a seguinte conversa entre um Cliente e um Bot e retorne APENAS um objeto JSON válido com os seguintes campos (sem formatação markdown, apenas JSON puro):

{{
    "necessidade_transbordo": "Sim" ou "Não",
    "transferencia": "Sim" ou "Não",
    "agente_agiu_corretamente": "Sim" ou "Não",
    "motivo_transbordo": "string",
    "problema_mapeado": "string",
    "precisa_atencao": "Sim" ou "Não",
    "observacao": "string"
}}

REGRAS DE ANÁLISE:

1. **necessidade_transbordo** (Sim/Não):
   - "Sim" se: Cliente pede humano, Bot entra em looping, Cliente nega recebimento (divergência), Bot dá erro, Cliente muito frustrado.
   - "Não" se: Bot resolveu ou apenas deu informação correta e cliente saiu.

2. **transferencia** (Sim/Não): 
   - "Sim" apenas se o bot transferiu para fila humana. 
   - Se mandou link externo (SAC/Formulário), é "Não".

3. **agente_agiu_corretamente** (Sim/Não):
   - "Não" se: Bot entrou em looping, deu informação falsa, contradisse a si mesmo, ou pediu avaliação (nota 1-5) quando o cliente digitou texto.
   - "Sim" caso contrário.

4. **motivo_transbordo**: 
   - Exemplos: "Solicitação do cliente", "Looping eterno", "Divergência de status", "Cliente inseguro", "Erro técnico", "N/A" (se não houver necessidade de transbordo).

5. **problema_mapeado**: 
   - Exemplos: "Tudo certo", "Pedido atrasado", "Pedido entregue para outro", "Falha em acionar tools", "Dúvida Vale Troca".

6. **precisa_atencao** (Sim/Não): 
   - Marcar "Sim" para bugs graves (looping), alucinações ou falhas de processo críticas.
   - "Não" caso contrário.

7. **observacao**: 
   - Um resumo curto e detalhado da análise (máximo 2 frases), descrevendo os problemas encontrados.

CONVERSA A SER ANALISADA:
{conversa}

IMPORTANTE: Retorne APENAS o JSON, sem nenhum texto adicional antes ou depois."""
    
    return prompt

# Função para analisar uma conversa via OpenAI API
def analisar_conversa_openai(conversa: str, modelo: str, api_key_openai: str = None) -> Dict:
    """Analisa uma conversa usando a API do OpenAI"""
    try:
        # Importar openai
        try:
            import openai
        except ImportError:
            return {
                "necessidade_transbordo": "Erro",
                "transferencia": "Erro",
                "agente_agiu_corretamente": "Erro",
                "motivo_transbordo": "Biblioteca não instalada",
                "problema_mapeado": "Erro de dependência",
                "precisa_atencao": "Sim",
                "observacao": "Erro: Biblioteca openai não está instalada. Execute: pip install openai"
            }
        
        # Verificar API Key
        if not api_key_openai:
            return {
                "necessidade_transbordo": "Erro",
                "transferencia": "Erro",
                "agente_agiu_corretamente": "Erro",
                "motivo_transbordo": "API Key não fornecida",
                "problema_mapeado": "Erro de configuração",
                "precisa_atencao": "Sim",
                "observacao": "Erro: OpenAI API Key não foi configurada. Configure na barra lateral."
            }
        
        # Configurar cliente OpenAI
        client = openai.OpenAI(api_key=api_key_openai)
        
        # Verificar se a conversa não está vazia
        if not conversa or len(conversa.strip()) < 10:
            return {
                "necessidade_transbordo": "Não",
                "transferencia": "Não",
                "agente_agiu_corretamente": "Sim",
                "motivo_transbordo": "N/A",
                "problema_mapeado": "Conversa muito curta",
                "precisa_atencao": "Não",
                "observacao": "Conversa sem conteúdo suficiente para análise"
            }
        
        # Criar prompt
        prompt = criar_prompt_sistema(conversa)
        
        # Gerar conteúdo com retry e backoff exponencial para rate limiting
        response = None
        max_retries = 5  # Aumentado para 5 tentativas
        
        for tentativa in range(max_retries):
            try:
                response = client.chat.completions.create(
                    model=modelo,
                    messages=[
                        {"role": "system", "content": "Você é um analista especializado em qualidade de atendimento de chatbots. Retorne APENAS JSON válido, sem texto adicional."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.1,
                    response_format={"type": "json_object"}  # Forçar resposta JSON
                )
                break  # Sucesso, sair do loop
            except Exception as e:
                error_msg = str(e)
                error_type = type(e).__name__
                
                # Verificar se é erro de rate limit
                is_rate_limit = (
                    "429" in error_msg or 
                    "rate_limit" in error_msg.lower() or 
                    "rate limit" in error_msg.lower() or
                    "rate_limit_exceeded" in error_type or
                    "quota" in error_msg.lower() or
                    "too_many_requests" in error_msg.lower()
                )
                
                if is_rate_limit:
                    if tentativa < max_retries - 1:
                        # Backoff exponencial: 10s, 20s, 40s, 80s
                        wait_time = 10 * (2 ** tentativa)
                        # Limitar a 60 segundos máximo
                        wait_time = min(wait_time, 60)
                        
                        # Tentar extrair retry-after do header se disponível
                        if hasattr(e, 'response') and hasattr(e.response, 'headers'):
                            retry_after = e.response.headers.get('retry-after')
                            if retry_after:
                                try:
                                    wait_time = int(retry_after) + 2
                                except:
                                    pass
                        
                        time.sleep(wait_time)
                        continue  # Tentar novamente
                    else:
                        # Última tentativa falhou
                        raise Exception(f"Rate limit excedido após {max_retries} tentativas. Aguarde alguns minutos antes de tentar novamente.")
                else:
                    # Outro tipo de erro, não tentar novamente
                    raise e
        
        if response is None or not response.choices or not response.choices[0].message.content:
            return {
                "necessidade_transbordo": "Erro",
                "transferencia": "Erro",
                "agente_agiu_corretamente": "Erro",
                "motivo_transbordo": "Sem resposta do modelo",
                "problema_mapeado": "Erro na API",
                "precisa_atencao": "Sim",
                "observacao": "O modelo não retornou uma resposta válida"
            }
        
        texto_resposta = response.choices[0].message.content.strip()
        resultado_json = extract_json_from_text(texto_resposta)
        
        if resultado_json is None:
            return {
                "necessidade_transbordo": "Erro",
                "transferencia": "Erro",
                "agente_agiu_corretamente": "Erro",
                "motivo_transbordo": "Erro ao processar resposta",
                "problema_mapeado": "Erro ao processar resposta",
                "precisa_atencao": "Sim",
                "observacao": f"Erro ao extrair JSON. Resposta: {texto_resposta[:150]}"
            }
        
        # Validar e padronizar campos
        resultado_json["necessidade_transbordo"] = str(resultado_json.get("necessidade_transbordo", "Não")).strip()
        resultado_json["transferencia"] = str(resultado_json.get("transferencia", "Não")).strip()
        resultado_json["agente_agiu_corretamente"] = str(resultado_json.get("agente_agiu_corretamente", "Sim")).strip()
        resultado_json["motivo_transbordo"] = str(resultado_json.get("motivo_transbordo", "N/A")).strip()
        resultado_json["problema_mapeado"] = str(resultado_json.get("problema_mapeado", "Não identificado")).strip()
        resultado_json["precisa_atencao"] = str(resultado_json.get("precisa_atencao", "Não")).strip()
        resultado_json["observacao"] = str(resultado_json.get("observacao", "Sem observação")).strip()
        
        return resultado_json
        
    except Exception as e:
        error_msg = str(e)
        
        # Verificar se é erro de rate limit
        is_rate_limit = (
            "429" in error_msg or 
            "quota" in error_msg.lower() or 
            "rate limit" in error_msg.lower() or 
            "rate_limit" in error_msg.lower() or
            "rate_limit_exceeded" in error_msg.lower() or
            "too_many_requests" in error_msg.lower()
        )
        
        if is_rate_limit:
            return {
                "necessidade_transbordo": "Erro",
                "transferencia": "Erro",
                "agente_agiu_corretamente": "Erro",
                "motivo_transbordo": "Rate limit excedido",
                "problema_mapeado": "Limite de requisições atingido",
                "precisa_atencao": "Sim",
                "observacao": "⚠️ Rate limit da API OpenAI excedido. Soluções: 1) Aumente o delay entre requisições na sidebar (recomendado: 10-15s), 2) Adicione créditos na sua conta OpenAI, 3) Use análise Local ao invés de OpenAI API, 4) Aguarde alguns minutos e tente novamente."
            }
        
        if len(error_msg) > 200:
            error_msg = error_msg[:200] + "..."
        
        return {
            "necessidade_transbordo": "Erro",
            "transferencia": "Erro",
            "agente_agiu_corretamente": "Erro",
            "motivo_transbordo": f"Erro: {error_msg}",
            "problema_mapeado": f"Erro: {error_msg}",
            "precisa_atencao": "Sim",
            "observacao": f"Erro na análise: {error_msg}"
        }

# Função para analisar uma conversa localmente usando regras de negócio
def analisar_conversa_local(conversa: str) -> Dict:
    """Analisa uma conversa usando regras de negócio locais (sem API)"""
    try:
        # Verificar se a conversa não está vazia
        if not conversa or len(conversa.strip()) < 10:
            return {
                "necessidade_transbordo": "Não",
                "transferencia": "Não",
                "agente_agiu_corretamente": "Sim",
                "motivo_transbordo": "N/A",
                "problema_mapeado": "Conversa muito curta",
                "precisa_atencao": "Não",
                "observacao": "Conversa sem conteúdo suficiente para análise"
            }
        
        conversa_lower = conversa.lower()
        conversa_original = conversa
        
        # Normalizar a conversa para análise
        linhas = conversa.split('\n')
        
        # 1. NECESSIDADE DE TRANSBORDO
        necessidade_transbordo = "Não"
        motivo_transbordo = "N/A"
        
        # Padrões que indicam necessidade de transbordo
        pede_humano_patterns = [
            r'falar\s+com\s+(?:um\s+)?(?:atendente|humano|pessoa|operador)',
            r'quero\s+(?:falar\s+)?com\s+(?:um\s+)?(?:atendente|humano|pessoa)',
            r'preciso\s+de\s+(?:um\s+)?(?:atendente|humano|pessoa)',
            r'atendente\s+(?:humano|pessoa)',
            r'transferir\s+para\s+(?:um\s+)?(?:atendente|humano|pessoa)'
        ]
        
        looping_patterns = [
            r'(?:repete|repetiu|repetindo|loop)',
            r'mesma\s+(?:coisa|mensagem|resposta)',
            r'já\s+(?:falei|disse|respondi)',
            r'não\s+entende'
        ]
        
        erro_bot_patterns = [
            r'erro',
            r'não\s+funcionou',
            r'não\s+está\s+funcionando',
            r'bug',
            r'problema\s+técnico',
            r'falha'
        ]
        
        cliente_frustrado_patterns = [
            r'irritado|irritada',
            r'estou\s+bravo|estou\s+brava',
            r'não\s+resolveu',
            r'incompetente',
            r'horrível|péssimo'
        ]
        
        # Verificar necessidade de transbordo
        pede_humano = any(re.search(pattern, conversa_lower) for pattern in pede_humano_patterns)
        tem_looping = any(re.search(pattern, conversa_lower) for pattern in looping_patterns)
        tem_erro = any(re.search(pattern, conversa_lower) for pattern in erro_bot_patterns)
        cliente_frustrado = any(re.search(pattern, conversa_lower) for pattern in cliente_frustrado_patterns)
        
        # Verificar divergência (cliente nega recebimento ou status)
        divergencia_patterns = [
            r'não\s+recebi',
            r'não\s+foi\s+entregue',
            r'está\s+errado',
            r'não\s+é\s+isso',
            r'diferente\s+do\s+que\s+comprei',
            r'pedido\s+errado'
        ]
        tem_divergencia = any(re.search(pattern, conversa_lower) for pattern in divergencia_patterns)
        
        if pede_humano:
            necessidade_transbordo = "Sim"
            motivo_transbordo = "Solicitação do cliente"
        elif tem_looping:
            necessidade_transbordo = "Sim"
            motivo_transbordo = "Looping eterno"
        elif tem_divergencia:
            necessidade_transbordo = "Sim"
            motivo_transbordo = "Divergência de status"
        elif tem_erro:
            necessidade_transbordo = "Sim"
            motivo_transbordo = "Erro técnico"
        elif cliente_frustrado:
            necessidade_transbordo = "Sim"
            motivo_transbordo = "Cliente frustrado"
        
        # 2. TRANSFERÊNCIA
        transferencia = "Não"
        # Verificar se bot transferiu para fila humana (não link externo)
        transferencia_patterns = [
            r'transferindo\s+para\s+(?:um\s+)?(?:atendente|humano|equipe)',
            r'vou\s+transferir\s+você',
            r'conectando\s+com\s+(?:um\s+)?atendente'
        ]
        
        link_externo_patterns = [
            r'https?://',
            r'www\.',
            r'\.com\.br',
            r'formulário|formulario',
            r'sac|contato',
            r'troque\.app',
            r'crocs\.com\.br/contato'
        ]
        
        tem_transferencia = any(re.search(pattern, conversa_lower) for pattern in transferencia_patterns)
        tem_link = any(re.search(pattern, conversa_lower) for pattern in link_externo_patterns)
        
        if tem_transferencia and not tem_link:
            transferencia = "Sim"
        elif tem_link:
            transferencia = "Não"  # Link externo não conta como transferência
        
        # 3. AGENTE AGIU CORRETAMENTE
        agente_correto = "Sim"
        
        # Verificar problemas que indicam que o bot agiu incorretamente
        if tem_looping:
            agente_correto = "Não"
        elif tem_erro:
            agente_correto = "Não"
        elif tem_divergencia:
            agente_correto = "Não"
        
        # Verificar se bot pediu avaliação quando cliente digitou texto
        avaliacao_pattern = r'(?:avaliar|nota|avalie|de\s+1\s+a\s+5)'
        cliente_texto_antes = False
        bot_pediu_avaliacao = False
        
        for i, linha in enumerate(linhas):
            if re.search(avaliacao_pattern, linha.lower()) and ('bot' in linha.lower() or 'atendente' in linha.lower() or 'whizz' in linha.lower()):
                bot_pediu_avaliacao = True
                # Verificar se cliente digitou texto antes
                for j in range(max(0, i-3), i):
                    if 'cliente' in linhas[j].lower() and len(linhas[j]) > 20:
                        cliente_texto_antes = True
                        break
                break
        
        if bot_pediu_avaliacao and cliente_texto_antes:
            agente_correto = "Não"
        
        # 4. PROBLEMA MAPEADO
        problema_mapeado = "Tudo certo"
        
        # Padrões de problemas
        if re.search(r'pedido\s+atrasado|atrasado|demora', conversa_lower):
            problema_mapeado = "Pedido atrasado"
        elif re.search(r'entregue\s+para\s+outro|endereço\s+errado|destinatário', conversa_lower):
            problema_mapeado = "Pedido entregue para outro"
        elif re.search(r'troca|vale\s+troca|devolução', conversa_lower):
            problema_mapeado = "Dúvida Vale Troca"
        elif re.search(r'ferramenta|tool|integração', conversa_lower):
            problema_mapeado = "Falha em acionar tools"
        elif tem_looping:
            problema_mapeado = "Looping do bot"
        elif tem_erro:
            problema_mapeado = "Erro técnico"
        elif tem_divergencia:
            problema_mapeado = "Divergência de informações"
        
        # 5. PRECISA ATENÇÃO
        precisa_atencao = "Não"
        if tem_looping or tem_erro or (agente_correto == "Não" and necessidade_transbordo == "Sim"):
            precisa_atencao = "Sim"
        
        # 6. OBSERVAÇÃO - Descrição detalhada e contextualizada dos problemas encontrados
        detalhes_problemas = []
        
        # Capturar contexto específico da conversa
        contexto_cliente = []
        contexto_bot = []
        
        for linha in linhas[:20]:  # Analisar primeiras 20 linhas para contexto
            linha_lower = linha.lower()
            if 'cliente' in linha_lower and len(linha.strip()) > 15:
                contexto_cliente.append(linha.strip()[:100])
            elif any(termo in linha_lower for termo in ['bot', 'atendente', 'whizz']) and len(linha.strip()) > 15:
                contexto_bot.append(linha.strip()[:100])
        
        # Detalhar problemas específicos encontrados com contexto
        
        # Necessidade de transbordo
        if necessidade_transbordo == "Sim":
            detalhes_transbordo = [f"TRANSBORDO NECESSÁRIO - Motivo: {motivo_transbordo}"]
            
            if pede_humano:
                detalhes_transbordo.append("Cliente solicitou explicitamente atendimento humano")
            
            if tem_looping:
                # Contar respostas do bot para detectar repetição
                respostas_bot = [linha for linha in linhas if any(termo in linha.lower() for termo in ['bot', 'atendente', 'whizz'])]
                if len(respostas_bot) > 3:
                    # Verificar similaridade entre respostas
                    similar_count = 0
                    for i in range(len(respostas_bot)-1):
                        if i < len(respostas_bot)-1:
                            palavras_linha1 = set(respostas_bot[i].lower().split())
                            palavras_linha2 = set(respostas_bot[i+1].lower().split())
                            palavras_comuns = palavras_linha1 & palavras_linha2
                            if len(palavras_comuns) > 5 and len(respostas_bot[i].split()) > 5:
                                similar_count += 1
                    
                    if similar_count > 0:
                        detalhes_transbordo.append(f"Bot entrou em looping: detectadas {similar_count + 1} respostas repetitivas/conflitantes. Cliente relatou que o bot 'não entende' ou repete a mesma informação.")
                    else:
                        detalhes_transbordo.append("Bot entrou em looping - respostas repetitivas detectadas na conversa. Cliente indicou que bot repete mesma informação ou não avança no atendimento.")
                else:
                    detalhes_transbordo.append("Bot entrou em looping - padrões de repetição detectados. Cliente mencionou que bot não está entendendo ou repete respostas.")
            
            if tem_divergencia:
                if re.search(r'não\s+recebi|não\s+foi\s+entregue', conversa_lower):
                    detalhes_transbordo.append("Cliente relatou que NÃO RECEBEU o pedido, mas sistema/bot indicou como entregue - DIVERGÊNCIA CRÍTICA detectada")
                elif re.search(r'pedido\s+errado|produto\s+errado|diferente\s+do\s+que\s+comprei', conversa_lower):
                    detalhes_transbordo.append("Cliente recebeu PRODUTO/PEDIDO DIFERENTE do que solicitou - divergência entre pedido e entrega")
                elif re.search(r'está\s+errado|não\s+é\s+isso|informação\s+errada', conversa_lower):
                    detalhes_transbordo.append("Cliente contestou informações do bot dizendo que estão ERRADAS - divergência de dados/fatos")
            
            if tem_erro:
                if re.search(r'link\s+não\s+funciona|site\s+não\s+abre|não\s+consegui\s+acessar|link\s+não\s+funciona', conversa_lower):
                    detalhes_transbordo.append("ERRO TÉCNICO: Cliente relatou que link/formulário indicado pelo bot NÃO FUNCIONA. Bot direcionou para recurso inacessível.")
                elif re.search(r'erro\s+técnico|bug|falha\s+do\s+sistema|sistema\s+não\s+funciona', conversa_lower):
                    detalhes_transbordo.append("ERRO TÉCNICO detectado no sistema/bot durante a conversa")
                else:
                    detalhes_transbordo.append("Falha técnica ou erro na operação do bot detectado")
            
            if cliente_frustrado:
                detalhes_transbordo.append("Cliente demonstrou FRUSTRAÇÃO/INSATISFAÇÃO evidente durante a interação")
            
            detalhes_problemas.append(" | ".join(detalhes_transbordo))
        
        # Detalhar sobre transferência
        if transferencia == "Sim":
            detalhes_problemas.append("Bot realizou TRANSFERÊNCIA para fila humana (ação correta)")
        elif necessidade_transbordo == "Sim" and transferencia == "Não":
            if tem_link:
                detalhes_problemas.append("⚠️ PROBLEMA: Cliente precisava de transbordo, mas bot apenas direcionou para LINK EXTERNO/SAC ao invés de transferir para fila humana diretamente")
            else:
                detalhes_problemas.append("⚠️ PROBLEMA: Cliente necessitava de transbordo mas NÃO FOI TRANSFERIDO pelo bot")
        
        # Detalhar comportamento incorreto do bot
        if agente_correto == "Não":
            problemas_bot_detalhados = []
            
            if tem_looping:
                problemas_bot_detalhados.append("Bot entrou em LOOPING - repetiu mesmas respostas/mensagens, demonstrando falha no fluxo conversacional")
            
            if tem_erro:
                problemas_bot_detalhados.append("Bot apresentou ERRO TÉCNICO durante atendimento")
            
            if bot_pediu_avaliacao and cliente_texto_antes:
                problemas_bot_detalhados.append("Bot solicitou AVALIAÇÃO (nota 1-5) quando cliente havia digitado TEXTO DESCRITIVO - falha no reconhecimento de intent/fluxo")
            
            if tem_divergencia:
                problemas_bot_detalhados.append("Bot forneceu INFORMAÇÕES DIVERGENTES da realidade relatada pelo cliente")
            
            if not tem_looping and not tem_erro and not tem_divergencia and agente_correto == "Não":
                problemas_bot_detalhados.append("Bot não agiu de forma adequada para a situação do cliente")
            
            if problemas_bot_detalhados:
                detalhes_problemas.append(f"❌ BOT AGIU INCORRETAMENTE: {' | '.join(problemas_bot_detalhados)}")
        
        # Detalhar problema mapeado com contexto
        if problema_mapeado != "Tudo certo":
            detalhes_problema_mapeado = []
            
            if problema_mapeado == "Pedido atrasado":
                detalhes_problema_mapeado.append("PROBLEMA MAPEADO: PEDIDO ATRASADO - Cliente está aguardando entrega que excede prazo esperado")
            elif problema_mapeado == "Pedido entregue para outro":
                detalhes_problema_mapeado.append("PROBLEMA MAPEADO: PEDIDO ENTREGUE EM ENDEREÇO/DESTINATÁRIO INCORRETO - situação de logística")
            elif problema_mapeado == "Dúvida Vale Troca":
                detalhes_problema_mapeado.append("PROBLEMA MAPEADO: DÚVIDA SOBRE PROCESSO DE TROCA/DEVOLUÇÃO - cliente precisa de orientação sobre política de troca")
            elif problema_mapeado == "Falha em acionar tools":
                detalhes_problema_mapeado.append("PROBLEMA MAPEADO: FALHA TÉCNICA - Bot não conseguiu acionar ferramentas/integrações necessárias para resolver a demanda")
            elif problema_mapeado == "Looping do bot":
                detalhes_problema_mapeado.append("PROBLEMA MAPEADO: LOOPING DO BOT - Bot ficou preso em ciclo de respostas repetitivas, não avançando no atendimento")
            elif problema_mapeado == "Erro técnico":
                detalhes_problema_mapeado.append("PROBLEMA MAPEADO: ERRO TÉCNICO - Falha no sistema ou no funcionamento do bot")
            elif problema_mapeado == "Divergência de informações":
                detalhes_problema_mapeado.append("PROBLEMA MAPEADO: DIVERGÊNCIA DE INFORMAÇÕES - Dados fornecidos pelo bot não correspondem à situação real do cliente")
            
            if detalhes_problema_mapeado:
                detalhes_problemas.append(detalhes_problema_mapeado[0])
        
        # Indicar se precisa atenção especial
        if precisa_atencao == "Sim":
            detalhes_problemas.append("🚨 PRECISA ATENÇÃO ESPECIAL - Bug grave, looping ou falha crítica detectada")
        
        # Construir observação final detalhada
        if len(detalhes_problemas) > 0:
            observacao = " | ".join(detalhes_problemas)
        elif necessidade_transbordo == "Sim":
            observacao = f"Transbordo necessário: {motivo_transbordo}. Problema identificado: {problema_mapeado}. Bot {'transferiu corretamente' if transferencia == 'Sim' else 'não transferiu para fila humana'}."
        elif problema_mapeado != "Tudo certo":
            observacao = f"Problema identificado: {problema_mapeado}. Bot agiu corretamente durante o atendimento, mas há questão específica a resolver relacionada ao problema mapeado."
        else:
            observacao = "✅ Conversa processada normalmente. Bot forneceu informações adequadas, atendeu corretamente e cliente não demonstrou necessidade de transbordo ou problemas críticos."
        
        return {
            "necessidade_transbordo": necessidade_transbordo,
            "transferencia": transferencia,
            "agente_agiu_corretamente": agente_correto,
            "motivo_transbordo": motivo_transbordo,
            "problema_mapeado": problema_mapeado,
            "precisa_atencao": precisa_atencao,
            "observacao": observacao
        }
        
    except Exception as e:
        return {
            "necessidade_transbordo": "Erro",
            "transferencia": "Erro",
            "agente_agiu_corretamente": "Erro",
            "motivo_transbordo": f"Erro na análise: {str(e)[:100]}",
            "problema_mapeado": "Erro no processamento",
            "precisa_atencao": "Sim",
            "observacao": f"Erro ao analisar conversa: {str(e)[:150]}"
        }

# Função para processar arquivo TXT
def processar_txt(conteudo: str) -> List[str]:
    """Processa arquivo TXT separado por '---'"""
    conversas = []
    partes = conteudo.split("---")
    
    for parte in partes:
        parte_limpa = parte.strip()
        if parte_limpa:
            conversas.append(parte_limpa)
    
    return conversas

# Função para processar arquivo CSV
def processar_csv(conteudo: str) -> List[str]:
    """Processa arquivo CSV com coluna 'conversa' ou 'Conversa'"""
    try:
        # Tentar diferentes métodos de leitura do CSV
        df = None
        
        # Método 1: Tentar com engine python (melhor para células multilinha)
        try:
            df = pd.read_csv(StringIO(conteudo), quotechar='"', skipinitialspace=True, 
                           on_bad_lines='skip', engine='python', keep_default_na=False)
        except Exception as e1:
            # Método 2: Tentar com engine padrão C
            try:
                df = pd.read_csv(StringIO(conteudo), quotechar='"', skipinitialspace=True, 
                               on_bad_lines='skip', keep_default_na=False)
            except Exception as e2:
                # Método 3: Tentar sem especificar quotechar
                try:
                    df = pd.read_csv(StringIO(conteudo), skipinitialspace=True, 
                                   on_bad_lines='skip', keep_default_na=False)
                except Exception as e3:
                    # Método 4: Usar csv module manualmente (silenciosamente)
                    try:
                        import csv
                        from io import StringIO
                        reader = csv.DictReader(StringIO(conteudo))
                        rows = list(reader)
                        if rows:
                            df = pd.DataFrame(rows)
                    except Exception as e4:
                        # Se todos os métodos falharam, mostrar erro
                        pass
        
        if df is None or df.empty:
            st.error("❌ Não foi possível processar o arquivo CSV ou está vazio!")
            return []
        
        # Procurar coluna de conversa (case-insensitive)
        coluna_conversa = None
        for col in df.columns:
            col_limpa = col.strip().lower()
            if col_limpa == "conversa":
                coluna_conversa = col
                break
        
        if coluna_conversa is None:
            st.error(f"❌ Coluna 'conversa' não encontrada no CSV!")
            st.info(f"📋 Colunas disponíveis no arquivo: {', '.join(df.columns.tolist()[:10])}")
            if len(df.columns) > 10:
                st.info(f"... e mais {len(df.columns) - 10} coluna(s)")
            return []
        
        # Extrair conversas, removendo valores nulos e vazios
        conversas = df[coluna_conversa].dropna().tolist()
        # Converter para string e remover conversas vazias
        conversas_processadas = []
        for conv in conversas:
            conv_str = str(conv).strip()
            if conv_str and conv_str.lower() not in ['nan', 'none', '']:
                conversas_processadas.append(conv_str)
        
        return conversas_processadas
    
    except Exception as e:
        st.error(f"❌ Erro ao processar CSV: {str(e)}")
        import traceback
        with st.expander("🔍 Detalhes do erro (clique para expandir)"):
            st.code(traceback.format_exc())
        return []

# Interface principal
st.header("📤 Upload de Arquivo")

uploaded_file = st.file_uploader(
    "Selecione um arquivo (.txt ou .csv)",
    type=["txt", "csv"],
    help="Para .txt: conversas separadas por '---'. Para .csv: deve ter coluna 'Conversa' ou 'conversa' (case-insensitive)"
)

conversas_carregadas = []

if uploaded_file is not None:
    # Ler conteúdo do arquivo
    if uploaded_file.name.endswith('.txt'):
        try:
            conteudo = str(uploaded_file.read(), "utf-8")
            conversas_carregadas = processar_txt(conteudo)
            st.session_state['conversas_carregadas_count'] = len(conversas_carregadas)
            st.success(f"✅ {len(conversas_carregadas)} conversa(s) carregada(s) do arquivo TXT")
        except Exception as e:
            st.error(f"❌ Erro ao ler arquivo TXT: {str(e)}")
            conversas_carregadas = []
    
    elif uploaded_file.name.endswith('.csv'):
        try:
            # Tentar diferentes encodings
            bytes_data = uploaded_file.read()
            conteudo = None
            
            for encoding in ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']:
                try:
                    conteudo = bytes_data.decode(encoding)
                    break
                except:
                    continue
            
            if conteudo is None:
                conteudo = bytes_data.decode('utf-8', errors='ignore')
            
            conversas_carregadas = processar_csv(conteudo)
            if conversas_carregadas:
                st.session_state['conversas_carregadas_count'] = len(conversas_carregadas)
                st.success(f"✅ {len(conversas_carregadas)} conversa(s) carregada(s) do arquivo CSV")
                # Mostrar prévia da primeira conversa para debug
                if len(conversas_carregadas) > 0:
                    st.info(f"📝 Prévia da primeira conversa (primeiros 300 caracteres): {conversas_carregadas[0][:300]}...")
            else:
                st.warning("⚠️ Nenhuma conversa foi encontrada no arquivo CSV. Verifique se a coluna 'Conversa' existe.")
        except Exception as e:
            st.error(f"❌ Erro ao ler arquivo CSV: {str(e)}")
            import traceback
            st.error(f"Detalhes: {traceback.format_exc()}")
            conversas_carregadas = []
    
    # Mostrar prévia das conversas e informações sobre limite
    if conversas_carregadas:
        # Mostrar informações sobre quantas conversas serão analisadas
        limite = st.session_state.get('limite_conversas', None)
        total_carregadas = len(conversas_carregadas)
        
        if limite and limite < total_carregadas:
            st.warning(f"⚠️ **Limite configurado**: Das {total_carregadas} conversas carregadas, apenas as primeiras **{limite}** serão analisadas. Para analisar todas, deixe o campo 'Número máximo de conversas' vazio na sidebar.")
        else:
            st.success(f"✅ **Todas as {total_carregadas} conversas** serão analisadas.")
        
        with st.expander("👁️ Prévia das conversas carregadas"):
            for idx, conversa in enumerate(conversas_carregadas[:3], 1):
                st.markdown(f"**Conversa {idx}:**")
                st.text(conversa[:500] + "..." if len(conversa) > 500 else conversa)
                st.markdown("---")
            
            if len(conversas_carregadas) > 3:
                st.info(f"*E mais {len(conversas_carregadas) - 3} conversa(s)...*")

# Função wrapper que escolhe o método de análise
def analisar_conversa(conversa: str, metodo: str, modelo: str = None, api_key_openai: str = None) -> Dict:
    """Wrapper que escolhe o método de análise baseado na seleção do usuário"""
    if metodo == "Local (Regras de Negócio)":
        return analisar_conversa_local(conversa)
    elif metodo == "OpenAI API":
        if modelo is None:
            return {
                "necessidade_transbordo": "Erro",
                "transferencia": "Erro",
                "agente_agiu_corretamente": "Erro",
                "motivo_transbordo": "Modelo não especificado",
                "problema_mapeado": "Erro de configuração",
                "precisa_atencao": "Sim",
                "observacao": "Erro: Modelo OpenAI não foi especificado"
            }
        return analisar_conversa_openai(conversa, modelo, api_key_openai)
    else:
        return analisar_conversa_local(conversa)  # Fallback para local

# Processamento
st.header("🔄 Processamento")

# Mostrar método selecionado
if metodo_analise == "OpenAI API":
    if not api_key:
        st.warning("⚠️ Por favor, configure a OpenAI API Key na barra lateral antes de iniciar a análise.")
    else:
        st.info(f"🔍 **Método selecionado:** {metodo_analise} | **Modelo:** {model_name}")
        
        # Aviso sobre rate limits se houver muitas conversas
        if conversas_carregadas and len(conversas_carregadas) > 50:
            st.warning(f"⚠️ **Atenção**: Você tem {len(conversas_carregadas)} conversas para analisar. Para evitar rate limits, recomendamos:")
            st.markdown("""
            - **Aumentar o delay entre requisições** na sidebar (10-15 segundos para contas gratuitas)
            - **Verificar créditos** na sua conta OpenAI (platform.openai.com)
            - **Considerar usar análise Local** para grandes volumes (mais rápido e sem limites)
            """)
else:
    st.info(f"🔍 **Método selecionado:** {metodo_analise} (Análise rápida usando regras de negócio)")

if conversas_carregadas and st.button("🚀 Iniciar Análise", type="primary", use_container_width=True):
    if len(conversas_carregadas) == 0:
        st.error("❌ Nenhuma conversa encontrada para analisar!")
    else:
        # Verificar se API Key está configurada quando necessário
        if metodo_analise == "OpenAI API" and not api_key:
            st.error("❌ Por favor, configure a OpenAI API Key na barra lateral!")
            st.stop()
        
        # Aplicar limite de conversas se configurado
        limite = st.session_state.get('limite_conversas', None)
        conversas_para_analisar = conversas_carregadas
        
        if limite and limite < len(conversas_carregadas):
            conversas_para_analisar = conversas_carregadas[:limite]
            st.info(f"📊 **Limite aplicado**: Analisando apenas as primeiras {limite} de {len(conversas_carregadas)} conversas carregadas.")
        else:
            st.info(f"📊 Analisando todas as {len(conversas_carregadas)} conversas carregadas.")
        
        # Inicializar lista de resultados
        resultados = []
        
        # Barra de progresso
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Iterar sobre as conversas (limitadas)
        total_conversas = len(conversas_para_analisar)
        for idx, conversa in enumerate(conversas_para_analisar, 1):
            metodo_texto = "OpenAI API" if metodo_analise == "OpenAI API" else "Local"
            status_text.text(f"📊 Analisando conversa {idx}/{total_conversas} ({metodo_texto})...")
            
            # Analisar conversa usando o método selecionado
            if metodo_analise == "OpenAI API":
                resultado = analisar_conversa(conversa, metodo_analise, model_name, api_key)
                # Delay configurável para evitar rate limiting
                time.sleep(delay_entre_requisicoes)
            else:
                resultado = analisar_conversa(conversa, metodo_analise)
            
            resultado["conversa_numero"] = idx
            resultado["conversa"] = conversa[:200] + "..." if len(conversa) > 200 else conversa
            resultados.append(resultado)
            
            # Atualizar progresso
            progress = idx / total_conversas
            progress_bar.progress(progress)
        
        status_text.text("✅ Análise concluída!")
        
        # Criar DataFrame com resultados
        df_resultados = pd.DataFrame(resultados)
        
        # Reordenar colunas
        colunas_ordenadas = [
            "conversa_numero",
            "necessidade_transbordo",
            "transferencia",
            "agente_agiu_corretamente",
            "motivo_transbordo",
            "problema_mapeado",
            "precisa_atencao",
            "observacao",
            "conversa"
        ]
        
        # Verificar se todas as colunas existem antes de reordenar
        colunas_existentes = [col for col in colunas_ordenadas if col in df_resultados.columns]
        if len(colunas_existentes) == len(colunas_ordenadas):
            df_resultados = df_resultados[colunas_ordenadas]
        
        # Salvar no session state
        st.session_state['df_resultados'] = df_resultados
        st.session_state['resultados_processados'] = True

# Exibição dos resultados
if 'resultados_processados' in st.session_state and st.session_state['resultados_processados']:
    st.header("📊 Resultados da Análise")
    
    df_resultados = st.session_state['df_resultados']
    
    # Estatísticas rápidas
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total de Conversas", len(df_resultados))
    
    with col2:
        precisam_atencao = len(df_resultados[df_resultados["precisa_atencao"] == "Sim"])
        st.metric("Precisam Atenção", precisam_atencao, delta=None)
    
    with col3:
        transbordos = len(df_resultados[df_resultados["necessidade_transbordo"] == "Sim"])
        st.metric("Transbordos", transbordos)
    
    with col4:
        agentes_corretos = len(df_resultados[df_resultados["agente_agiu_corretamente"] == "Sim"])
        st.metric("Agente Correto", agentes_corretos, delta=f"{agentes_corretos/len(df_resultados)*100:.1f}%")
    
    # Dataframe com destaque
    st.subheader("Tabela de Resultados")
    
    # Preparar dataframe para exibição com destaque
    df_display = df_resultados.copy()
    
    # Exibir dataframe
    st.dataframe(
        df_display,
        use_container_width=True,
        height=400,
        hide_index=True
    )
    
    # Filtro para destacar conversas que precisam atenção
    st.info("💡 **Dica:** Use o filtro abaixo para visualizar apenas as conversas que precisam de atenção especial.")
    
    filtro_atencao = st.checkbox("Mostrar apenas conversas que precisam atenção", value=False)
    
    if filtro_atencao:
        df_filtrado = df_display[df_display['precisa_atencao'] == 'Sim']
        if not df_filtrado.empty:
            st.dataframe(
                df_filtrado,
                use_container_width=True,
                height=300,
                hide_index=True
            )
            st.warning(f"⚠️ {len(df_filtrado)} conversa(s) precisa(m) de atenção!")
        else:
            st.success("✅ Nenhuma conversa precisa de atenção especial!")
    
    # Botões de download
    st.subheader("💾 Download do Relatório")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # CSV
        csv = df_resultados.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="📥 Download CSV",
            data=csv,
            file_name=f"relatorio_qa_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    with col2:
        # Excel - criar em memória
        excel_buffer = BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            df_resultados.to_excel(writer, index=False, sheet_name='Resultados')
        excel_data = excel_buffer.getvalue()
        
        st.download_button(
            label="📥 Download Excel",
            data=excel_data,
            file_name=f"relatorio_qa_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: gray;'>
        <p>Analista de Conversas - QA Chatbot | Powered by Google Gemini</p>
    </div>
    """,
    unsafe_allow_html=True
)

