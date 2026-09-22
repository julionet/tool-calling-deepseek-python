# Tool Calling com DeepSeek API

Um exemplo prático de implementação de **Tool Calling** (chamada de ferramentas/funções) utilizando a API do DeepSeek em Python. Este projeto demonstra como integrar modelos de IA com funções locais, permitindo que o modelo decida quando e como chamar ferramentas para resolver problemas.

## 📋 Descrição do Projeto

Este projeto implementa um sistema de chat interativo onde:

- 🤖 Um modelo de IA (DeepSeek) recebe perguntas em linguagem natural
- 🔧 O modelo analisa se precisa usar ferramentas/funções para responder
- ⚙️ Funções Python são executadas automaticamente quando solicitadas
- 💬 Os resultados são devolvidos ao modelo para gerar uma resposta final
- 🎯 O escopo é restrito a perguntas sobre clima e previsão do tempo

### Fluxo de Funcionamento

```
Pergunta do Usuário
        ↓
    Modelo IA
        ↓
  Precisa de Tool? → SIM → Executa Função Local
        ↓ (NÃO)            ↓
   Resposta Final ← Retorna Resultado
```

## 🚀 Características

- ✅ **Tool Calling Automático**: O modelo decide quando usar as ferramentas disponíveis
- ✅ **Compatibilidade OpenAI**: Usa o SDK `openai` (compatível com DeepSeek)
- ✅ **Histórico de Conversa**: Mantém contexto entre múltiplas mensagens
- ✅ **Cache de Prompts**: Suporte a cache de prompts do sistema (economia de tokens)
- ✅ **Restrição de Escopo**: Prompt de sistema força o modelo a responder apenas sobre clima
- ✅ **Tratamento Robusto**: Normaliza mensagens para evitar incompatibilidades de API
- ✅ **Fácil Extensão**: Adicione novas ferramentas facilmente

## 📦 Dependências

O projeto requer apenas duas bibliotecas:

```
openai>=1.40.0      # SDK OpenAI (compatível com DeepSeek)
python-dotenv>=1.0.0 # Carregamento de variáveis de ambiente
```

## 🔧 Instalação

### Pré-requisitos

- Python 3.8+
- Conta na DeepSeek com API key ativa
- Um terminal ou IDE Python

### Passos de Instalação

1. **Clone ou baixe o projeto:**
   ```bash
   git clone https://github.com/seu-usuario/tool-calling-deepseek-python.git
   cd tool-calling-deepseek-python
   ```

2. **Crie um ambiente virtual (opcional, mas recomendado):**
   ```bash
   python -m venv venv
   source venv/bin/activate  # No Windows: venv\Scripts\activate
   ```

3. **Instale as dependências:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure as variáveis de ambiente:**
   
   Copie o arquivo `.env.example` para `.env`:
   ```bash
   cp .env.example .env
   ```

   Edite o arquivo `.env` com suas credenciais:
   ```env
   DEEPSEEK_API_KEY=sua_chave_de_api_aqui
   BASE_URL=https://api.deepseek.com/v1
   MODEL=deepseek-flash
   ```

   > ⚠️ **Importante**: Nunca commit o arquivo `.env` com suas credenciais reais!

## 📖 Como Usar

### Executar o Chat Interativo

```bash
python tool_calling_example.py
```

Ao executar, você será solicitado a:

1. **Informar um prompt de sistema (opcional)**: Pressione Enter para usar apenas o prompt padrão (escopo de clima)
2. **Fazer perguntas**: Digite suas perguntas sobre clima e previsão do tempo

### Exemplos de Uso

**Exemplo 1 - Consulta Simples:**
```
Você: Qual é a temperatura em São Paulo?
Assistente: A temperatura em São Paulo é de 24°C, com condição nublada.
```

**Exemplo 2 - Pergunta Fora do Escopo (Bloqueada):**
```
Você: Qual é a capital do Brasil?
Assistente: Não posso responder sua pergunta
```

**Exemplo 3 - Múltiplas Cidades:**
```
Você: Como está o clima em São Paulo, Rio de Janeiro e Curitiba?
Assistente: [Chama get_weather 3 vezes e consolida os resultados]
```

## 📁 Estrutura do Projeto

```
tool-calling-deepseek-python/
├── tool_calling_example.py    # Script principal com lógica de tool calling
├── requirements.txt            # Dependências do projeto
├── .env.example               # Modelo de variáveis de ambiente
├── .env                       # Variáveis de ambiente (não fazer commit)
├── .gitignore                 # Arquivos a ignorar no Git
└── README.md                  # Este arquivo
```

## 🔑 Variáveis de Ambiente

| Variável | Descrição | Padrão |
|----------|-----------|--------|
| `DEEPSEEK_API_KEY` | Sua chave de API do DeepSeek | (obrigatório) |
| `BASE_URL` | URL da API do DeepSeek | (obrigatório) |
| `MODEL` | Modelo a usar | `deepseek-flash` |

## 🛠️ Componentes Principais

### 1. **Função de Ferramenta: `get_weather()`**

Simula uma consulta de clima (em produção, chamaria uma API real):

```python
def get_weather(city: str) -> dict:
    """Retorna temperatura e condição climática de uma cidade."""
```

**Cidades suportadas:**
- São Paulo: 24°C, nublado
- Rio de Janeiro: 30°C, ensolarado
- Curitiba: 15°C, chuvoso

### 2. **Schema de Ferramentas**

Define como o modelo deve chamar a ferramenta:

```python
TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Retorna a temperatura e condição climática atual de uma cidade.",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "Nome da cidade"}
                },
                "required": ["city"]
            }
        }
    }
]
```

### 3. **Função Principal: `send_message()`**

Implementa o loop de tool calling:

1. Envia mensagens ao modelo
2. Verifica se há `tool_calls` na resposta
3. Executa as funções necessárias
4. Devolve resultados ao modelo
5. Repete até obter resposta final em texto

### 4. **Restrição de Escopo**

`SCOPE_SYSTEM_PROMPT` garante que o modelo:
- Responda APENAS sobre clima e temperatura
- Use a ferramenta `get_weather` quando apropriado
- Retorne mensagem padrão para perguntas fora do escopo

## 💡 Conceitos-Chave

### Tool Calling (Chamada de Ferramentas)

É a capacidade do modelo de IA decidir chamar funções externas para:
- Obter informações em tempo real
- Executar cálculos complexos
- Acessar bases de dados
- Interagir com APIs

### Normalização de Mensagens

O código normaliza respostas do SDK para evitar incompatibilidades:

```python
# ❌ NÃO fazer (pode trazer campos extras)
messages.append(response.choices[0].message)

# ✅ FAZER (apenas campos esperados pela API)
messages.append({
    "role": "assistant",
    "content": assistant_message.content,
    "tool_calls": [...]
})
```

### Histórico de Conversa

Todas as mensagens (incluindo tool calls) são preservadas para:
- Manter contexto entre turnos
- Permitir conversas naturais e contínuas
- Otimizar cache de prompts

## 🔄 Extensibilidade

### Adicionar uma Nova Ferramenta

1. **Implemente a função Python:**
   ```python
   def get_forecast(city: str, days: int = 7) -> dict:
       """Retorna previsão do tempo para os próximos dias."""
       # sua lógica aqui
       return {"cidade": city, "previsao": [...]}
   ```

2. **Registre no mapa de ferramentas:**
   ```python
   AVAILABLE_TOOLS = {
       "get_weather": get_weather,
       "get_forecast": get_forecast,  # adicione aqui
   }
   ```

3. **Defina o schema JSON Schema:**
   ```python
   {
       "type": "function",
       "function": {
           "name": "get_forecast",
           "description": "Retorna previsão do tempo para uma cidade.",
           "parameters": {
               "type": "object",
               "properties": {
                   "city": {"type": "string"},
                   "days": {"type": "integer", "default": 7}
               },
               "required": ["city"]
           }
       }
   }
   ```

## 📊 Monitoramento de Cache

O script imprime informações sobre o cache de prompts:

```
[cache] hit=256 miss=1024 (prompt_tokens=1280)
```

- `hit`: Tokens reutilizados do cache
- `miss`: Novos tokens processados
- Esto ajuda a otimizar custos de API

## 🐛 Solução de Problemas

### Erro: `DEEPSEEK_API_KEY not found`

**Solução:** Verifique se o arquivo `.env` existe e contém a chave correta.

### Erro: `Tool not found`

**Solução:** Certifique-se de que o nome da ferramenta está registrado em `AVAILABLE_TOOLS`.

### Resposta: "Não posso responder sua pergunta"

**Comportamento esperado:** O modelo foi solicitado apenas responder perguntas sobre clima. Faça perguntas relacionadas a temperatura, condições climáticas, etc.

## 📚 Referências

- [Documentação DeepSeek API](https://api.deepseek.com/docs)
- [SDK OpenAI Python](https://github.com/openai/openai-python)
- [JSON Schema Specification](https://json-schema.org/)
- [OpenAI Tool Calling Guide](https://platform.openai.com/docs/guides/function-calling)

## 📝 Licença

Este projeto é fornecido como exemplo educacional. Você é livre para usar, modificar e distribuir conforme necessário.

## 👨‍💻 Autor

Desenvolvido como exemplo de integração com a API do DeepSeek.

## 🤝 Contribuições

Contribuições são bem-vindas! Sinta-se livre para:
- Reportar bugs
- Sugerir novas funcionalidades
- Melhorar a documentação
- Adicionar novos exemplos

---

**Última atualização:** 21 de setembro de 2026

Aproveite explorando o poder do Tool Calling com DeepSeek! 🚀
