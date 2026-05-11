# Avaliador de Prompts

Avalia prompts com base no `PROMPT_ENGINEERING_GUIDE.md` usando Gemini via OpenRouter.
O guia cobre 30 seções — das técnicas fundamentais ao CASTROFF Framework, Tree-of-Thought,
protocolo de debugging e segurança avançada.

---

## Instalação

```bash
pip install openai python-dotenv
```

Crie um `.env` na raiz com sua chave do OpenRouter:

```
OPEN_ROUTER=sk-or-...
```

---

## Como usar

```bash
# Prompt via argumento
python prompt_evaluator.py "Analise este documento."

# Prompt via arquivo
python prompt_evaluator.py -f meu_prompt.txt

# Modo interativo (cola o prompt e dá Enter duas vezes)
python prompt_evaluator.py --interactive

# Salvar relatório em JSON
python prompt_evaluator.py "..." --json resultado.json

# Selecionar modelo Gemini
python prompt_evaluator.py "..." --model google/gemini-2.5-flash
python prompt_evaluator.py "..." --model google/gemini-2.5-pro
```

### Modelos disponíveis via OpenRouter

| Modelo | Indicado para |
|--------|---------------|
| `google/gemini-2.0-flash-001` | Padrão — rápido e eficiente |
| `google/gemini-2.5-flash` | Melhor raciocínio, custo moderado |
| `google/gemini-2.5-pro` | Máxima qualidade para prompts complexos |

---

## O que o avaliador faz

O script executa **2 chamadas ao modelo**:

1. **Análise** — avalia 10 dimensões com nota 0–10, status e sugestões
2. **Melhoria** — reescreve o prompt aplicando os top 3 gaps identificados

Ambas as chamadas usam o guia completo extraído (~44k chars) como base de conhecimento.

### 10 dimensões avaliadas

| Dimensão | O que avalia |
|----------|--------------|
| Clareza e Diretividade | Especificidade das instruções, eliminação de ambiguidade |
| Estrutura e Separação de Dados | Uso de XML tags, separação instrução/dado |
| Formato de Saída | JSON, Markdown, prefill, stop_sequences |
| Prevenção de Alucinações | Ancoragem, saída de emergência, restrição de conhecimento |
| Contexto e Role Prompting | Persona, audiência, tom, especificidade do papel |
| Few-Shot / Exemplos | Quantidade, representatividade, edge cases |
| Chain of Thought / Precognição | Raciocínio externalizado, passos explícitos |
| Raciocínio Avançado | Tree-of-Thought, Self-Ask, Reflection quando aplicáveis |
| Segurança e Guardrails | Injection, prompt leak, input validation |
| Produção e Robustez | Lost-in-the-middle, robustez a perturbações, saída de emergência |

### Saída do relatório

- Nota geral (0–10) com barra visual
- Resumo executivo em 2–3 frases
- Avaliação detalhada por dimensão (nota, gaps, sugestões)
- Top 3 prioridades de melhoria com ações concretas
- Prompt melhorado pronto para uso
- Exportação JSON opcional para integração programática

---

## Base de conhecimento — `PROMPT_ENGINEERING_GUIDE.md`

Guia com 30 seções compilado a partir de múltiplas fontes:

| Seções | Conteúdo |
|--------|----------|
| §1–§10 | Fundamentos: estrutura, clareza, role prompting, XML tags, CoT, few-shot, chaining |
| §11–§17 | Produção: anti-alucinação, consistência, critérios de sucesso, avaliação, latência, segurança |
| §18–§20 | Templates, anti-padrões, checklist de qualidade |
| §21–§22 | Tree-of-Thought, Self-Ask, Multi-Agent, Reflection, Iterative Refinement |
| §23–§24 | CASTROFF Framework (8 dimensões de auditoria), Protocolo de Debugging 6 etapas |
| §25–§26 | Segurança avançada (taxonomia de ataques, PAIR, injection indireta), gestão em produção |
| §27–§30 | Lost-in-the-Middle, robustez, ICL, prompting ético e inclusivo, templates avançados |

---

## Knowledge Base — `.claude/kb/prompt-engineering/`

35 arquivos organizados em concepts, patterns e specs para uso pelos agentes Claude Code:

```
concepts/   14 arquivos — técnicas fundamentais e avançadas
patterns/   17 arquivos — padrões de produção, segurança, debugging
specs/       2 arquivos — catálogos YAML machine-readable (técnicas e ataques)
```

---

## Estrutura do projeto

```
.
├── prompt_evaluator.py          # Script principal
├── PROMPT_ENGINEERING_GUIDE.md  # Guia de referência (30 seções, ~2300 linhas)
├── .env                         # OPEN_ROUTER=sk-or-... (não commitado)
├── .claude/
│   ├── agents/ai-ml/
│   │   └── ai-prompt-specialist.md   # Agente especializado (v3.0)
│   └── kb/prompt-engineering/        # Knowledge Base (35 arquivos)
└── docs/                        # Fontes dos materiais do guia
```
