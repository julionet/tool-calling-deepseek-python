# Comparação: Tool Calling com DeepSeek vs Claude

Este documento compara as duas implementações de Tool Calling presentes neste projeto, destacando as diferenças e similaridades entre a **API do DeepSeek** e a **API do Claude (Anthropic)**.

## 📊 Visão Geral

| Aspecto | DeepSeek | Claude |
|---------|----------|--------|
| **Arquivo** | `tool_calling_example.py` | `tool_calling_claude_example.py` |
| **SDK** | OpenAI-compatível | Anthropic SDK nativo |
| **URL Base** | `https://api.deepseek.com/v1` | Gerenciado automaticamente |
| **Chave de API** | `DEEPSEEK_API_KEY` | `ANTHROPIC_API_KEY` |
| **Modelo Padrão** | `deepseek-flash` | `claude-opus-5` |

## 🔧 Principais Diferenças

### 1. Inicialização do Cliente

**DeepSeek (OpenAI-compatível):**
```python
from openai import OpenAI

client = OpenAI(
    api_key=os.environ["DEEPSEEK_API_KEY"],
    base_url=os.environ["BASE_URL"],
)
```

**Claude (Anthropic):**
```python
from anthropic import Anthropic

client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
```

### 2. Definição de Tools (Schema)

**DeepSeek (JSON Schema com tipo "function"):**
```python
{
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "...",
        "parameters": {
            "type": "object",
            "properties": {...},
            "required": [...]
        }
    }
}
```

**Claude (Formato Anthropic nativo):**
```python
{
    "name": "get_weather",
    "description": "...",
    "input_schema": {
        "type": "object",
        "properties": {...},
        "required": [...]
    }
}
```

### 3. Requisição da API

**DeepSeek:**
```python
response = client.chat.completions.create(
    model=MODEL,
    messages=messages,
    tools=TOOLS_SCHEMA,
    tool_choice="auto",
)
```

**Claude:**
```python
response = client.messages.create(
    model=MODEL,
    max_tokens=1024,
    system=full_system_prompt,
    tools=TOOLS_SCHEMA,
    messages=messages,
)
```

### 4. Tratamento de Tool Calls

**DeepSeek (com tool_calls):**
```python
if assistant_message.tool_calls:
    for tool_call in assistant_message.tool_calls:
        func_name = tool_call.function.name
        func_args = json.loads(tool_call.function.arguments)
        
        # Executar e adicionar resultado como "tool" role
        messages.append({
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": json.dumps(result, ensure_ascii=False),
        })
```

**Claude (com tool_use blocks):**
```python
tool_use_blocks = [block for block in response.content if block.type == "tool_use"]

if tool_use_blocks:
    tool_results = []
    for tool_use in tool_use_blocks:
        tool_name = tool_use.name
        tool_input = tool_use.input
        
        result = func(**tool_input)
        
        tool_results.append({
            "type": "tool_result",
            "tool_use_id": tool_use.id,
            "content": json.dumps(result, ensure_ascii=False),
        })
    
    # Retornar como "user" role com tool_results
    messages.append({"role": "user", "content": tool_results})
```

### 5. Gerenciamento de Prompts do Sistema

**DeepSeek:**
```python
messages = [{"role": "system", "content": SCOPE_SYSTEM_PROMPT}]
if system_prompt:
    messages.append({"role": "system", "content": system_prompt})
```

**Claude:**
```python
full_system_prompt = SCOPE_SYSTEM_PROMPT
if system_prompt:
    full_system_prompt += f"\n\n{system_prompt}"

response = client.messages.create(
    ...
    system=full_system_prompt,  # Parâmetro separado
    ...
)
```

### 6. Informações de Uso (Tokens)

**DeepSeek:**
```python
print(
    f"[cache] hit={usage.prompt_cache_hit_tokens} "
    f"miss={usage.prompt_cache_miss_tokens} "
    f"(prompt_tokens={usage.prompt_tokens})"
)
```

**Claude:**
```python
print(
    f"[usage] input_tokens={response.usage.input_tokens} "
    f"output_tokens={response.usage.output_tokens}"
)
```

## ✅ Similaridades

1. **Mesma Lógica de Tool Calling**: Ambas implementam o padrão de chamar ferramentas quando necessário
2. **Histórico de Conversa**: Ambas mantêm o histórico de mensagens para contexto contínuo
3. **Restrição de Escopo**: Ambas usam um prompt de sistema para restringir respostas
4. **Execução de Funções**: Ambas executam a mesma função `get_weather()`
5. **Normalização de Resultados**: Ambas convertam resultados para JSON

## 🚀 Como Usar Cada Uma

### DeepSeek

```bash
# Instalar dependências
pip install -r requirements.txt

# Configurar .env
DEEPSEEK_API_KEY=sua_chave_aqui
BASE_URL=https://api.deepseek.com/v1
MODEL=deepseek-flash

# Executar
python tool_calling_example.py
```

### Claude

```bash
# Instalar dependências
pip install -r requirements.txt

# Configurar .env
ANTHROPIC_API_KEY=sua_chave_claude_aqui

# Executar
python tool_calling_claude_example.py
```

## 📈 Comparação de Funcionalidades

| Funcionalidade | DeepSeek | Claude |
|---|---|---|
| Tool Calling automático | ✅ | ✅ |
| Multiple tool calls | ✅ | ✅ |
| Cache de prompts | ✅ | ❌* |
| Suporte a vision | ✅ | ✅ |
| Streaming | ✅ | ✅ |
| max_tokens necessário | ❌ | ✅ |
| Histórico de conversa | ✅ | ✅ |

*Claude oferece suporte a cache através de `cache_control` (requer configuração adicional)

## 💰 Considerações de Custo

- **DeepSeek**: Geralmente mais econômico, especialmente para modelos menores
- **Claude**: Preço premium, mas com modelos mais avançados (Opus 5)

## 🔄 Migrando de Uma para Outra

### De DeepSeek para Claude

1. Trocar imports:
   ```python
   # De:
   from openai import OpenAI
   # Para:
   from anthropic import Anthropic
   ```

2. Atualizar schema de tools (remover "type": "function")

3. Ajustar loop de tool calling para usar `tool_use_blocks`

4. Separar system prompt em parâmetro dedicado

### De Claude para DeepSeek

1. Trocar imports:
   ```python
   # De:
   from anthropic import Anthropic
   # Para:
   from openai import OpenAI
   ```

2. Adicionar "type": "function" ao schema

3. Ajustar loop de tool calling para usar `tool_calls`

4. Incluir system prompt no histórico de mensagens

## 📚 Referências Rápidas

### DeepSeek
- [Documentação Oficial](https://api-docs.deepseek.com/)
- [SDK OpenAI (usado por DeepSeek)](https://github.com/openai/openai-python)
- [Tool Calling Guide](https://api-docs.deepseek.com/guides/function_calling)

### Claude
- [Documentação Anthropic](https://docs.anthropic.com/)
- [SDK Python](https://github.com/anthropics/anthropic-sdk-python)
- [Tool Use Guide](https://docs.anthropic.com/en/docs/build-a-system-with-claude/tool-use)

## 🎯 Quando Usar Cada Uma

### Use DeepSeek quando:
- 💰 Custo é uma prioridade
- ⚡ Velocidade de resposta é crítica
- 🔄 Já usa padrão OpenAI em seu projeto

### Use Claude quando:
- 🧠 Qualidade da resposta é prioridade
- 🎯 Precisa de raciocínio mais avançado
- 🔒 Segurança/conformidade é crítica

## 📝 Conclusão

Ambas as implementações são válidas e funcionam bem. A escolha depende de seus requisitos específicos:

- **DeepSeek** é excelente para prototipagem rápida e custo-efetividade
- **Claude** oferece melhor qualidade e recursos avançados

Você pode até usar ambas no mesmo projeto para comparar resultados!

---

**Última atualização:** 21 de setembro de 2026
