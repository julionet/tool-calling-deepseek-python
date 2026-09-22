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
    base_url=os.environ["BASE_URL"],
)

MODEL = os.environ.get("MODEL", "deepseek-flash")

# Restrição de escopo: este prompt é sempre incluído (além de qualquer prompt de
# sistema informado pelo usuário) para instruir o modelo a recusar perguntas fora
# do tema de clima, sempre com a mesma frase fixa.
SCOPE_SYSTEM_PROMPT = (
    "Você é um assistente especializado exclusivamente em clima e previsão do tempo. "
    "Responda apenas perguntas relacionadas a clima, temperatura ou condições climáticas, "
    "usando a ferramenta get_weather quando necessário. "
    "Se a pergunta do usuário não for sobre esse assunto, responda EXATAMENTE e apenas: "
    "\"Não posso responder sua pergunta\" — sem nenhum texto adicional."
)


# ---------------------------------------------------------------------------
# 1. Implementação real da(s) tool(s) — código Python comum.
# ---------------------------------------------------------------------------
def get_weather(city: str) -> dict:
    """Simula uma consulta de clima. Em produção, chamaria uma API real."""
    fake_db = {
        "são paulo": {"temperatura_c": 24, "condicao": "nublado"},
        "rio de janeiro": {"temperatura_c": 30, "condicao": "ensolarado"},
        "curitiba": {"temperatura_c": 15, "condicao": "chuvoso"},
    }
    dados = fake_db.get(city.strip().lower())
    if dados is None:
        return {"cidade": city, "erro": "Não foram encontradas informações para a cidade informada."}
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

    Importante: nunca guardamos o objeto de resposta do SDK diretamente em
    `messages`. Ele traz campos extras do SDK/provedor (ex: `refusal`,
    `reasoning_content`) que não fazem parte do formato de mensagem esperado
    de volta pela API. Por isso, normalizamos cada resposta do assistente em
    um dict simples, com apenas os campos que a API espera receber de volta.
    """
    while True:
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=TOOLS_SCHEMA,
            tool_choice="auto",
        )
        assistant_message = response.choices[0].message

        usage = response.usage
        print(
            f"[cache] hit={usage.prompt_cache_hit_tokens} "
            f"miss={usage.prompt_cache_miss_tokens} "
            f"(prompt_tokens={usage.prompt_tokens})"
        )

        if assistant_message.tool_calls:
            # Normaliza a mensagem do assistente para o formato de dict esperado pela API,
            # preservando os tool_calls (necessários para associar as respostas da tool a seguir).
            messages.append(
                {
                    "role": "assistant",
                    "content": assistant_message.content,
                    "tool_calls": [
                        {
                            "id": tool_call.id,
                            "type": tool_call.type,
                            "function": {
                                "name": tool_call.function.name,
                                "arguments": tool_call.function.arguments,
                            },
                        }
                        for tool_call in assistant_message.tool_calls
                    ],
                }
            )

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

            continue  # próxima iteração chama o modelo de novo já com o resultado da tool

        # Resposta final em texto: normaliza e encerra o loop.
        messages.append({"role": "assistant", "content": assistant_message.content})
        return assistant_message.content


if __name__ == "__main__":
    print("Chat com tool calling (DeepSeek). Digite 'sair' para encerrar.\n")

    system_prompt = input(
        "Prompt de sistema (opcional, pressione Enter para pular): "
    ).strip()

    messages = [{"role": "system", "content": SCOPE_SYSTEM_PROMPT}]
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
