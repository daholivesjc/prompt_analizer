# Avaliador de Prompts

Avalia prompts com base no `PROMPT_ENGINEERING_GUIDE.md` usando Gemini via OpenRouter.

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

# Usar outro modelo Gemini
python prompt_evaluator.py "..." --model google/gemini-2.5-flash-preview
```

## O que o avaliador faz

1. **Carrega o `PROMPT_ENGINEERING_GUIDE.md`** como base de conhecimento para o avaliador
2. **Envia para Gemini via OpenRouter** (credencial `OPEN_ROUTER` do `.env`)
3. **Avalia 8 dimensões** com nota 0–10, status (ok/atenção/crítico), gaps e sugestões específicas:
   - Clareza e Diretividade
   - Estrutura e Separação de Dados (XML tags)
   - Formato de Saída
   - Prevenção de Alucinações
   - Contexto e Role Prompting
   - Few-Shot / Exemplos
   - Chain of Thought / Precognição
   - Segurança e Guardrails
4. **Top 3 prioridades** de melhoria com ações concretas
5. **Prompt melhorado** pronto para uso
6. **Exportação JSON** opcional para integração programática
7. **Relatório colorido** no terminal com barras de progresso visuais
