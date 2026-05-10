#!/usr/bin/env python3
"""
Avaliador de Prompts com Gemini via OpenRouter.
Analisa prompts com base no PROMPT_ENGINEERING_GUIDE.md e gera relatório de gaps e melhorias.

Uso:
  python prompt_evaluator.py "Seu prompt aqui"
  python prompt_evaluator.py -f meu_prompt.txt
  python prompt_evaluator.py --interactive
"""

import argparse
import json
import os
import sys
import textwrap
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# ---------------------------------------------------------------------------
# Configuração
# ---------------------------------------------------------------------------

GUIDE_PATH = Path(__file__).parent / "PROMPT_ENGINEERING_GUIDE.md"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
GEMINI_MODEL = "google/gemini-2.0-flash-001"
GUIDE_MAX_CHARS = 18000  # resumo focado nas regras, não no tutorial completo

DIMENSIONS = [
    "clareza_e_diretividade",
    "estrutura_e_separacao",
    "formato_de_saida",
    "prevencao_de_alucinacoes",
    "contexto_e_papel",
    "few_shot_e_exemplos",
    "chain_of_thought",
    "seguranca_e_guardrails",
]

DIMENSION_LABELS = {
    "clareza_e_diretividade": "Clareza e Diretividade",
    "estrutura_e_separacao": "Estrutura e Separação de Dados",
    "formato_de_saida": "Formato de Saída",
    "prevencao_de_alucinacoes": "Prevenção de Alucinações",
    "contexto_e_papel": "Contexto e Role Prompting",
    "few_shot_e_exemplos": "Few-Shot / Exemplos",
    "chain_of_thought": "Chain of Thought / Precognição",
    "seguranca_e_guardrails": "Segurança e Guardrails",
}

# ---------------------------------------------------------------------------
# Prompt do avaliador
# ---------------------------------------------------------------------------

EVALUATOR_SYSTEM = """Você é um especialista sênior em Engenharia de Prompts com profundo conhecimento
das melhores práticas para LLMs. Sua função é avaliar prompts de forma técnica, objetiva e construtiva,
identificando gaps e propondo melhorias concretas.

Você tem acesso a um guia completo de engenharia de prompts que serve como base de conhecimento para sua avaliação."""

ANALYSIS_PROMPT_TEMPLATE = """
## Guia de Referência para Avaliação

{guide_content}

---

## Prompt a Avaliar

```
{prompt_to_evaluate}
```

---

## Tarefa

Avalie o prompt acima com base no guia de referência. Retorne APENAS um JSON válido
(sem markdown, sem texto fora do JSON):

{{
  "nota_geral": <número de 0 a 10, com uma casa decimal>,
  "resumo_executivo": "<2-3 frases sobre o prompt e seu nível geral>",
  "dimensoes": {{
    "clareza_e_diretividade": {{
      "nota": <0-10>,
      "status": "<ok|atenção|crítico>",
      "gaps": ["<gap principal>"],
      "sugestoes": ["<sugestão concreta>"]
    }},
    "estrutura_e_separacao": {{
      "nota": <0-10>,
      "status": "<ok|atenção|crítico>",
      "gaps": ["<gap principal>"],
      "sugestoes": ["<sugestão concreta>"]
    }},
    "formato_de_saida": {{
      "nota": <0-10>,
      "status": "<ok|atenção|crítico>",
      "gaps": ["<gap principal>"],
      "sugestoes": ["<sugestão concreta>"]
    }},
    "prevencao_de_alucinacoes": {{
      "nota": <0-10>,
      "status": "<ok|atenção|crítico>",
      "gaps": ["<gap principal>"],
      "sugestoes": ["<sugestão concreta>"]
    }},
    "contexto_e_papel": {{
      "nota": <0-10>,
      "status": "<ok|atenção|crítico>",
      "gaps": ["<gap principal>"],
      "sugestoes": ["<sugestão concreta>"]
    }},
    "few_shot_e_exemplos": {{
      "nota": <0-10>,
      "status": "<ok|atenção|crítico>",
      "gaps": ["<gap principal>"],
      "sugestoes": ["<sugestão concreta>"]
    }},
    "chain_of_thought": {{
      "nota": <0-10>,
      "status": "<ok|atenção|crítico>",
      "gaps": ["<gap principal>"],
      "sugestoes": ["<sugestão concreta>"]
    }},
    "seguranca_e_guardrails": {{
      "nota": <0-10>,
      "status": "<ok|atenção|crítico>",
      "gaps": ["<gap principal>"],
      "sugestoes": ["<sugestão concreta>"]
    }}
  }},
  "top3_prioridades": [
    {{"prioridade": 1, "dimensao": "<dimensão mais crítica>", "acao": "<ação concreta>"}},
    {{"prioridade": 2, "dimensao": "<dimensão>", "acao": "<ação>"}},
    {{"prioridade": 3, "dimensao": "<dimensão>", "acao": "<ação>"}}
  ]
}}

Regras:
- Seja técnico e específico — evite generalizações como "melhore a clareza"
- Se uma dimensão não se aplica, atribua nota 7 e status "ok"
- "crítico" apenas para gaps que comprometem significativamente o resultado
"""

IMPROVEMENT_PROMPT_TEMPLATE = """
## Guia de Referência

{guide_content}

---

## Prompt Original

```
{prompt_to_evaluate}
```

---

## Diagnóstico (resultado da avaliação)

{diagnosis}

---

## Tarefa

Com base no diagnóstico acima, reescreva o prompt aplicando as principais melhorias.
Retorne APENAS um JSON válido (sem markdown, sem texto fora do JSON):

{{
  "prompt_melhorado": "<versão reescrita e melhorada do prompt original>",
  "explicacao_melhorias": ["<melhoria 1>", "<melhoria 2>", "<melhoria 3>"]
}}
"""


# ---------------------------------------------------------------------------
# Cliente OpenRouter
# ---------------------------------------------------------------------------

def build_client() -> OpenAI:
    api_key = os.getenv("OPEN_ROUTER")
    if not api_key:
        sys.exit("[ERRO] Variável OPEN_ROUTER não encontrada no .env")
    return OpenAI(
        api_key=api_key,
        base_url=OPENROUTER_BASE_URL,
        default_headers={
            "HTTP-Referer": "https://prompt-evaluator.local",
            "X-Title": "Prompt Evaluator",
        },
    )


def load_guide() -> str:
    if not GUIDE_PATH.exists():
        sys.exit(f"[ERRO] Guia não encontrado: {GUIDE_PATH}")
    content = GUIDE_PATH.read_text(encoding="utf-8")

    # Extrai apenas as seções relevantes para avaliação (descarta exemplos de código extensos)
    keep_sections = [
        "## 3. Regra de Ouro",
        "## 4. Role Prompting",
        "## 5. Separação de Dados",
        "## 6. Formatação de Saída",
        "## 7. Precognição",
        "## 8. Few-Shot",
        "## 10. Estrutura Completa",
        "## 11. Prevenção de Alucinações",
        "## 12. Consistência de Saída",
        "## 17. Segurança e Guardrails",
        "## 19. Anti-Padrões",
        "## 20. Checklist",
    ]

    lines = content.splitlines()
    selected: list[str] = []
    capturing = False

    for line in lines:
        is_section_start = any(line.startswith(s) for s in keep_sections)
        is_next_h2 = line.startswith("## ") and not is_section_start

        if is_section_start:
            capturing = True
        elif is_next_h2 and capturing:
            capturing = False

        if capturing:
            selected.append(line)

    guide = "\n".join(selected)

    # Garante que não ultrapassa o limite configurado
    return guide[:GUIDE_MAX_CHARS]


def _parse_json(raw: str) -> dict:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("```", 1)[1]
        if raw.startswith("json"):
            raw = raw[4:]
    if raw.endswith("```"):
        raw = raw[: raw.rfind("```")]
    return json.loads(raw.strip())


def _chat(client: OpenAI, user_message: str) -> str:
    response = client.chat.completions.create(
        model=GEMINI_MODEL,
        temperature=0.1,
        max_tokens=4096,
        messages=[
            {"role": "system", "content": EVALUATOR_SYSTEM},
            {"role": "user", "content": user_message},
        ],
    )
    return response.choices[0].message.content.strip()


def call_gemini(client: OpenAI, guide: str, prompt: str) -> dict:
    # Chamada 1: análise das dimensões (saída compacta, sem prompt reescrito)
    analysis_msg = ANALYSIS_PROMPT_TEMPLATE.format(
        guide_content=guide,
        prompt_to_evaluate=prompt,
    )
    raw_analysis = _chat(client, analysis_msg)
    result = _parse_json(raw_analysis)

    # Chamada 2: prompt melhorado (entrada menor, saída focada)
    diagnosis = json.dumps(result.get("top3_prioridades", []), ensure_ascii=False)
    improvement_msg = IMPROVEMENT_PROMPT_TEMPLATE.format(
        guide_content=guide[:8000],  # guia menor para esta chamada
        prompt_to_evaluate=prompt,
        diagnosis=diagnosis,
    )
    raw_improvement = _chat(client, improvement_msg)
    improvement = _parse_json(raw_improvement)

    result["prompt_melhorado"] = improvement.get("prompt_melhorado", "")
    result["explicacao_melhorias"] = improvement.get("explicacao_melhorias", [])
    return result


# ---------------------------------------------------------------------------
# Renderização do relatório
# ---------------------------------------------------------------------------

RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"

RED = "\033[91m"
YELLOW = "\033[93m"
GREEN = "\033[92m"
CYAN = "\033[96m"
MAGENTA = "\033[95m"
BLUE = "\033[94m"
WHITE = "\033[97m"


def color_for_status(status: str) -> str:
    return {"ok": GREEN, "atenção": YELLOW, "crítico": RED}.get(status, WHITE)


def color_for_score(score: float) -> str:
    if score >= 8:
        return GREEN
    if score >= 6:
        return YELLOW
    return RED


def bar(score: float, width: int = 20) -> str:
    filled = int(round(score / 10 * width))
    empty = width - filled
    color = color_for_score(score)
    return f"{color}{'█' * filled}{DIM}{'░' * empty}{RESET}"


def wrap(text: str, width: int = 70, indent: str = "    ") -> str:
    return textwrap.fill(text, width=width, initial_indent=indent, subsequent_indent=indent)


def hr(char: str = "─", width: int = 72) -> str:
    return DIM + char * width + RESET


def print_report(data: dict, prompt_original: str) -> None:
    nota = data["nota_geral"]
    nota_color = color_for_score(nota)

    print()
    print(hr("═"))
    print(f"{BOLD}{CYAN}  RELATÓRIO DE AVALIAÇÃO DE PROMPT{RESET}")
    print(hr("═"))
    print()

    # Nota geral
    print(f"  {BOLD}NOTA GERAL{RESET}  {nota_color}{BOLD}{nota:.1f}{RESET}/10  {bar(nota)}")
    print()
    print(f"  {BOLD}Resumo:{RESET}")
    print(wrap(data["resumo_executivo"], width=72))
    print()
    print(hr())

    # Dimensões
    print(f"\n  {BOLD}AVALIAÇÃO POR DIMENSÃO{RESET}\n")

    for dim_key in DIMENSIONS:
        dim = data["dimensoes"].get(dim_key, {})
        label = DIMENSION_LABELS.get(dim_key, dim_key)
        score = dim.get("nota", 0)
        status = dim.get("status", "ok")
        sc = color_for_status(status)
        status_icon = {"ok": "✓", "atenção": "!", "crítico": "✗"}.get(status, "?")

        print(f"  {sc}{BOLD}[{status_icon}] {label}{RESET}")
        print(f"      Nota: {color_for_score(score)}{score}/10{RESET}  {bar(score, 15)}")

        gaps = dim.get("gaps", [])
        if gaps:
            print(f"      {YELLOW}Gaps:{RESET}")
            for g in gaps:
                print(wrap(f"• {g}", width=68, indent="        "))

        sugestoes = dim.get("sugestoes", [])
        if sugestoes:
            print(f"      {CYAN}Sugestões:{RESET}")
            for s in sugestoes:
                print(wrap(f"→ {s}", width=68, indent="        "))
        print()

    print(hr())

    # Top 3 prioridades
    print(f"\n  {BOLD}TOP 3 PRIORIDADES DE MELHORIA{RESET}\n")
    for item in data.get("top3_prioridades", []):
        p = item["prioridade"]
        color = [RED, YELLOW, CYAN][p - 1] if p <= 3 else WHITE
        print(f"  {color}{BOLD}#{p} {item['dimensao']}{RESET}")
        print(wrap(item["acao"], width=70))
        print()

    print(hr())

    # Prompt melhorado
    print(f"\n  {BOLD}PROMPT MELHORADO{RESET}\n")
    melhorado = data.get("prompt_melhorado", "")
    for line in melhorado.splitlines():
        print(f"  {GREEN}{line}{RESET}")
    print()

    # Explicação das melhorias
    explicacao = data.get("explicacao_melhorias", "")
    if explicacao:
        print(f"  {BOLD}Principais melhorias aplicadas:{RESET}")
        # Aceita string (com quebras de linha) ou lista de strings
        if isinstance(explicacao, list):
            items = explicacao
        else:
            items = [l.strip() for l in explicacao.splitlines() if l.strip()]
        for item in items:
            print(wrap(item, width=70, indent="  "))
    print()
    print(hr("═"))
    print(f"  {DIM}Modelo: {GEMINI_MODEL} via OpenRouter{RESET}")
    print(hr("═"))
    print()


# ---------------------------------------------------------------------------
# Exportação JSON
# ---------------------------------------------------------------------------

def save_json(data: dict, output_path: Path) -> None:
    output_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n  {GREEN}Relatório JSON salvo em: {output_path}{RESET}\n")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Avaliador de Prompts com Gemini via OpenRouter",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""
            Exemplos:
              python prompt_evaluator.py "Resuma este texto"
              python prompt_evaluator.py -f meu_prompt.txt
              python prompt_evaluator.py --interactive
              python prompt_evaluator.py "..." --json resultado.json
        """),
    )
    parser.add_argument(
        "prompt",
        nargs="?",
        help="Texto do prompt a avaliar",
    )
    parser.add_argument(
        "-f", "--file",
        type=Path,
        metavar="ARQUIVO",
        help="Lê o prompt de um arquivo .txt",
    )
    parser.add_argument(
        "-i", "--interactive",
        action="store_true",
        help="Modo interativo: digita o prompt no terminal",
    )
    parser.add_argument(
        "--json",
        type=Path,
        metavar="SAIDA.json",
        help="Salva o resultado completo em JSON",
    )
    parser.add_argument(
        "--model",
        default=GEMINI_MODEL,
        help=f"Modelo Gemini via OpenRouter (padrão: {GEMINI_MODEL})",
    )
    return parser


def get_prompt_text(args: argparse.Namespace) -> str:
    if args.interactive:
        print(f"\n{CYAN}Cole o prompt abaixo e pressione Enter duas vezes quando terminar:{RESET}\n")
        lines = []
        try:
            while True:
                line = input()
                if line == "" and lines and lines[-1] == "":
                    break
                lines.append(line)
        except EOFError:
            pass
        return "\n".join(lines).strip()

    if args.file:
        if not args.file.exists():
            sys.exit(f"[ERRO] Arquivo não encontrado: {args.file}")
        return args.file.read_text(encoding="utf-8").strip()

    if args.prompt:
        return args.prompt.strip()

    sys.exit("[ERRO] Forneça um prompt via argumento, -f arquivo ou --interactive")


def main() -> None:
    parser = build_arg_parser()
    args = parser.parse_args()

    global GEMINI_MODEL
    GEMINI_MODEL = args.model

    prompt_text = get_prompt_text(args)

    if not prompt_text:
        sys.exit("[ERRO] Prompt vazio.")

    print(f"\n{DIM}Carregando guia de referência...{RESET}")
    guide = load_guide()

    print(f"{DIM}Conectando ao Gemini via OpenRouter ({GEMINI_MODEL})...{RESET}")
    client = build_client()

    print(f"{DIM}Avaliando prompt ({len(prompt_text)} caracteres) em 2 chamadas...{RESET}\n")

    try:
        result = call_gemini(client, guide, prompt_text)
    except json.JSONDecodeError as e:
        print(f"\n[ERRO] Resposta do modelo não é JSON válido: {e}")
        print("[DICA] O modelo pode ter excedido o limite de tokens. Tente --model google/gemini-2.5-flash")
        sys.exit(1)
    except Exception as e:
        sys.exit(f"[ERRO] Falha na chamada à API: {e}")

    print_report(result, prompt_text)

    if args.json:
        save_json(result, args.json)


if __name__ == "__main__":
    main()
