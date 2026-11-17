# Registro do protótipo

## Escopo e decisões atuais

1. **Pasta semanal de TXT:** escolhida pelo usuário em lugar de arquivo único;
   preserva o registro de notas sem banco ou interface gráfica.
2. **Resumo e tarefas sustentadas pelas notas:** dificuldades explícitas podem virar
   tarefas. Sugestões livres foram excluídas para facilitar a conferência.
3. **Qwen local pelo Ollama:** o usuário substituiu a escolha inicial de OpenAI
   por modelo local. A aplicação agora usa apenas Ollama, com padrão
   `qwen3:4b-instruct`, sem chave. HTTPX acessa a API nativa local com esquema JSON.
4. **Referências literais:** cada tarefa aponta arquivo e trecho existente.
   A validação detecta citações inexistentes, mas não comprova a interpretação.
5. **Falha integral e sem sobrescrita:** arquivos ilegíveis, limites locais excedidos
   ou respostas inválidas interrompem o fluxo em vez de gerar síntese parcial.

## Verificações da versão local

```sh
uv sync
uv run --offline --no-sync python -m unittest discover -s tests -v
uv run --offline --no-sync note-summarizer examples/semana --check
uv run --offline --no-sync note-summarizer examples/semana
```

Resultado: 15 testes aprovados; dois arquivos validados, total de 363 caracteres.
A execução normal não conseguiu conectar ao Ollama e apresentou mensagem clara,
com código de saída 1. Não foi encontrado executável `ollama` no PATH, nem aplicativo
nos diretórios padrão consultados. A inferência real permanece pendente.

Testes de HTTP 401/403, modelo ausente, indisponibilidade, comunicação, timeout,
resposta incompleta e formato inesperado são simulados com transporte HTTP em memória.
O serviço local padrão não exige credencial. Nenhum teste baixa modelo ou faz
inferência real. A síntese ilustrativa foi escrita manualmente.

## Histórico da primeira versão

A primeira versão utilizava OpenAI Responses API. Foram aprovados 14 testes,
sem chamada real por ausência de chave. Também foi validada em cópia de código
com novo ambiente virtual, usando cache de dependências. Uma tentativa com cache
novo falhou por resolução DNS do PyPI no ambiente restrito.
Esses resultados descrevem a versão anterior, não a integração atual com Ollama.

## Pendências

- Instalar e iniciar Ollama, baixar o Qwen e registrar suas versões.
- Executar os dois exemplos com o modelo real e avaliar fidelidade, consolidação,
  reconhecimento de tarefas concluídas e ausência de tarefas inventadas.
- Registrar tempo e adequação do modelo ao hardware disponível.
- Não presumir que o limite de caracteres garante caber no contexto do modelo;
  a configuração da janela de contexto precisa comportar entrada, esquema e saída.
- Git/GitHub, histórico, PR, tags, vídeo e avaliações no Moodle não foram realizados.
- Atualizar este registro com dificuldades e reflexão reais do aluno.

## Uso de IA

O desenho foi delimitado em entrevista com o usuário. A IA criou o protótipo,
seus testes e documentação, e adaptou a integração conforme a mudança para modelo
local. O aluno ainda deve revisar o código, experimentar com o Qwen real e registrar
sua própria reflexão e dificuldades na entrega final.
