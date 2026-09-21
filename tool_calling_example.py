"""
Exemplo simples de Tool Calling com a API do DeepSeek.

A API do DeepSeek é compatível com o formato da OpenAI, então usamos o
SDK oficial `openai`, apenas trocando a `base_url`.

Fluxo:
  1. Enviamos a pergunta do usuário + a definição das tools disponíveis.
  2. Se o modelo decidir usar uma tool, ele retorna `tool_calls` em vez de texto.
  3. Executamos a função real localmente e devolvemos o resultado ao modelo
     como uma mensagem de role="tool".
  4. O modelo usa esse resultado para gerar a resposta final em linguagem natural.
"""

import json
import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    api_key=os.environ["DEEPSEEK_API_KEY"],
    base_url="https://api.deepseek.com",
)

MODEL = "deepseek-flash"


# ---------------------------------------------------------------------------
# 1. Implementação real da(s) tool(s) — código Python comum.
# ---------------------------------------------------------------------------
def get_weather(city: str) -> dict:
    """Simula uma consulta de clima. Em produção, chamaria uma API real."""
    fake_db = {
        "sao paulo": {"temperatura_c": 24, "condicao": "nublado"},
        "rio de janeiro": {"temperatura_c": 30, "condicao": "ensolarado"},
        "curitiba": {"temperatura_c": 15, "condicao": "chuvoso"},
    }
    dados = fake_db.get(city.strip().lower(), {"temperatura_c": 20, "condicao": "indefinido"})
    return {"cidade": city, **dados}


# Mapa nome-da-tool -> função Python real
AVAILABLE_TOOLS = {
    "get_weather": get_weather,
}

# ---------------------------------------------------------------------------
# 2. Definição das tools no formato que o DeepSeek/OpenAI espera (JSON Schema).
# ---------------------------------------------------------------------------
TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Retorna a temperatura e condição climática atual de uma cidade.",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "Nome da cidade, ex: 'Curitiba'",
                    }
                },
                "required": ["city"],
            },
        },
    }
]


def send_message(messages: list) -> str:
    """Envia o histórico de mensagens ao modelo e resolve tool calls até obter texto final.

    `messages` é atualizado in-place, preservando o histórico da conversa
    (inclusive as chamadas de tool) para as próximas interações.
    """
    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        tools=TOOLS_SCHEMA,
        tool_choice="auto",
    )
    assistant_message = response.choices[0].message
    messages.append(assistant_message)

    # O modelo pode encadear múltiplas rodadas de tool calls antes de responder em texto.
    while assistant_message.tool_calls:
        for tool_call in assistant_message.tool_calls:
            func_name = tool_call.function.name
            func_args = json.loads(tool_call.function.arguments)

            print(f"[tool call] {func_name}({func_args})")

            func = AVAILABLE_TOOLS[func_name]
            result = func(**func_args)

            # Devolvemos o resultado da tool ao modelo, associado ao mesmo tool_call.id
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result, ensure_ascii=False),
                }
            )

        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=TOOLS_SCHEMA,
            tool_choice="auto",
        )
        assistant_message = response.choices[0].message
        messages.append(assistant_message)

    return assistant_message.content


if __name__ == "__main__":
    print("Chat com tool calling (DeepSeek). Digite 'sair' para encerrar.\n")

    system_prompt = input(
        "Prompt de sistema (opcional, pressione Enter para pular): "
    ).strip()

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})

    while True:
        user_input = input("Você: ").strip()
        if user_input.lower() == "sair":
            print("Encerrando conversa.")
            break
        if not user_input:
            continue

        messages.append({"role": "user", "content": user_input})
        resposta = send_message(messages)
        print(f"Assistente: {resposta}\n")
