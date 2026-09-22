"""
Exemplo simples de Tool Calling com a API do Claude (Anthropic).

O SDK do Claude permite definir e chamar ferramentas de forma elegante,
com suporte nativo para tool use e iteração automática até obter uma resposta final.

Fluxo:
  1. Enviamos a pergunta do usuário + a definição das tools disponíveis.
  2. Se o modelo decidir usar uma tool, ele retorna `tool_use` blocks.
  3. Executamos a função real localmente e devolvemos o resultado ao modelo
     como uma mensagem com role="user" e conteúdo de tool result.
  4. O modelo usa esse resultado para gerar a resposta final em linguagem natural.
"""

import json
import os

from dotenv import load_dotenv
from anthropic import Anthropic

load_dotenv()

client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

MODEL = os.environ.get("MODEL_CLAUDE", "claude-opus-5")

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
# 2. Definição das tools no formato que o Claude espera (Anthropic format).
# ---------------------------------------------------------------------------
TOOLS_SCHEMA = [
    {
        "name": "get_weather",
        "description": "Retorna a temperatura e condição climática atual de uma cidade.",
        "input_schema": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "Nome da cidade, ex: 'Curitiba'",
                }
            },
            "required": ["city"],
        },
    }
]


def send_message(messages: list, system_prompt: str = "") -> str:
    """Envia o histórico de mensagens ao modelo e resolve tool calls até obter texto final.

    `messages` é atualizado in-place, preservando o histórico da conversa
    (inclusive as chamadas de tool) para as próximas interações.

    Sistema de prompts:
    - O prompt de escopo é sempre incluído (SCOPE_SYSTEM_PROMPT)
    - Um prompt adicional do usuário pode ser fornecido
    """
    # Combina o prompt de escopo com o prompt adicional do usuário
    full_system_prompt = SCOPE_SYSTEM_PROMPT
    if system_prompt:
        full_system_prompt += f"\n\n{system_prompt}"

    while True:
        response = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            system=full_system_prompt,
            tools=TOOLS_SCHEMA,
            messages=messages,
        )

        # Adiciona a mensagem do assistente ao histórico
        messages.append({"role": "assistant", "content": response.content})

        # Exibe informações de uso (tokens)
        print(
            f"[usage] input_tokens={response.usage.input_tokens} "
            f"output_tokens={response.usage.output_tokens}"
        )

        # Verifica se há tool use blocks na resposta
        tool_use_blocks = [block for block in response.content if block.type == "tool_use"]

        if not tool_use_blocks:
            # Nenhuma tool foi chamada, extrair resposta final de texto
            for block in response.content:
                if hasattr(block, "text"):
                    return block.text
            return ""

        # Processa cada tool call
        tool_results = []
        for tool_use in tool_use_blocks:
            tool_name = tool_use.name
            tool_input = tool_use.input

            print(f"[tool call] {tool_name}({tool_input})")

            # Executa a função real
            func = AVAILABLE_TOOLS[tool_name]
            result = func(**tool_input)

            # Adiciona o resultado da tool para ser enviado ao modelo
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": tool_use.id,
                "content": json.dumps(result, ensure_ascii=False),
            })

        # Adiciona todos os resultados das tools como uma única mensagem do usuário
        messages.append({"role": "user", "content": tool_results})

        # Próxima iteração chama o modelo novamente com os resultados das tools


if __name__ == "__main__":
    print("Chat com tool calling (Claude). Digite 'sair' para encerrar.\n")

    system_prompt = input(
        "Prompt de sistema (opcional, pressione Enter para pular): "
    ).strip()

    messages = []

    while True:
        user_input = input("Você: ").strip()
        if user_input.lower() == "sair":
            print("Encerrando conversa.")
            break
        if not user_input:
            continue

        messages.append({"role": "user", "content": user_input})
        resposta = send_message(messages, system_prompt)
        print(f"Assistente: {resposta}\n")
