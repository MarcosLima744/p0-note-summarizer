# Relatório de execução — síntese semanal de estudos

## Problema e escopo

A aplicação ajuda um estudante a revisar as anotações da semana e identificar o
que estudar depois. Recebe uma pasta com arquivos `.txt`, resume os conteúdos por
assunto e extrai pendências com referências aos trechos de origem. O resultado é
apresentado no terminal e salvo em Markdown.

O projeto utiliza Python e um único modelo local pelo Ollama. A configuração
padrão é `qwen3:4b-instruct`. O LLM interpreta anotações livres, agrupa assuntos e
reconhece pendências expressas de formas diferentes, incluindo dificuldades de
aprendizagem explícitas. Não deve inventar compromissos, prioridades ou prazos.

## Evolução por nível

| Nível | Implementado | Situação da validação e entrega |
| --- | --- | --- |
| Básico | Leitura dos TXT, chamada programática ao modelo, apresentação textual e dependências declaradas. | O autor confirmou o funcionamento real no macOS. O Git foi iniciado e há commits e remoto configurado. A tag `p0-basico` ainda não existe localmente. |
| Intermediário | Separação de configuração, entrada, solicitação, chamada, resposta e apresentação; mensagens de erro; `.env.example`, `.gitignore`, README e exemplos. | Falhas cobertas por testes locais/simulados. Faltam registrar uma branch integrada por PR e a tag `p0-intermediario`, além de explicitar os cenários de credencial ausente e inválida na simulação. |
| Avançado | Modelo, timeout, temperatura, contexto e limite de geração configuráveis; logs sem conteúdo das notas; lockfile, versões e testes sem inferência real. | Falta validar a versão atual com Qwen em ambiente limpo e completar as evidências finais. O nome da tag do Avançado está em branco no enunciado. |

Esses níveis descrevem responsabilidades já presentes no código. Não representam
três versões históricas entregues separadamente: o primeiro commit já contém o
protótipo com recursos das três etapas.

## Decisões principais

| Decisão | Alternativa considerada | Justificativa |
| --- | --- | --- |
| Ler uma pasta semanal com vários TXT, sem subpastas. | Receber um único arquivo. | Preserva a organização das anotações escolhida pelo autor e mantém o escopo pequeno. |
| Produzir resumo e tarefas apoiadas no texto. | Gerar sugestões livres de próximos estudos. | Facilita conferir a saída e reduz compromissos inventados. Dificuldades explícitas podem originar tarefas. |
| Usar Qwen local via Ollama, pela API nativa com HTTPX. | OpenAI Responses API, usada na primeira implementação. | Atende à preferência posterior do autor por execução local e dispensa chave de API. |
| Exigir arquivo e trecho literal para cada tarefa. | Aceitar apenas uma lista de tarefas em texto livre. | Permite validar referências e conferir a origem de cada pendência. |
| Interromper em erros de leitura, excesso do limite local ou resposta inválida, sem sobrescrever saídas. | Produzir uma síntese parcial ou substituir o resultado anterior. | Evita apresentar um resultado incompleto como se cobrisse todas as notas e preserva arquivos existentes. |

## Ambiente e execução

Ambiente utilizado no desenvolvimento: macOS, Python 3.13.12, HTTPX 0.28.1,
Pydantic 2.14.3 e python-dotenv 1.2.4. As versões exatas das dependências estão
em `uv.lock`. A versão instalada do Ollama e a identificação efetiva do modelo
utilizado na execução real ainda precisam ser registradas com `ollama --version`
e `ollama list`.

O autor confirmou que a aplicação está funcionando com o modelo local no macOS.
Essa confirmação substitui a pendência anterior de instalação e primeira execução.
A evidência dessa execução foi indicada pelo autor e conferida nos arquivos locais:

- Entrada: [anotações de 16/11](examples/semana/2026-11-16.txt) e
  [anotações de 17/11](examples/semana/2026-11-17.txt).
- Saída original: `output/semana.md`.
- Cópia preservada, sem alteração do conteúdo, para versionamento:
  [síntese real com Qwen](evidencias/execucao-qwen-semana.md).

O arquivo original fica em `output/`, pasta ignorada pelo Git. A cópia em
`evidencias/` permite incluir o resultado na entrega sem versionar todas as saídas.
Para reproduzir o caso, usando um destino novo:

```sh
uv run note-summarizer examples/semana --output output/reproducao-semana.md
```

Esse é um comando de reprodução, não um registro capturado do terminal original.
A conferência abaixo foi feita sobre o artefato existente, sem nova inferência.

O código foi escrito para macOS, Linux e Windows, usando caminhos portáveis e
HTTP local. O README agora apresenta instruções para os três sistemas. Linux e
Windows ainda não foram validados na prática.

## Testes e resultados

A suíte da versão atual foi executada novamente durante esta atualização:

```sh
uv run --offline --no-sync python -m unittest discover -s tests -q
```

Resultado: **15 testes aprovados**. Os cenários abaixo são verificações dentro
desses testes; não representam testes adicionais nem inferências reais.

| Teste | Entrada ou situação | Resultado esperado | Resultado obtido |
| --- | --- | --- | --- |
| Fluxo real | Execução com Ollama e modelo local pelo autor. | Apresentar uma síntese útil. | Funcionamento confirmado pelo autor no macOS; saída preservada em `evidencias/execucao-qwen-semana.md` e conferida contra as duas notas de entrada. |
| Fluxo local simulado | Notas e resposta estruturada simulada. | Apresentar e salvar Markdown. | Aprovado; conteúdo esperado presente no arquivo salvo. |
| Entrada vazia | Pasta sem TXT útil. | Impedir chamada e orientar o usuário. | Aprovado. |
| Leitura dos arquivos | TXT fora de ordem, vazio, Markdown e subpasta. | Ordenar os TXT diretos e ignorar os demais conteúdos. | Aprovado. |
| Entrada inválida | Codificação inválida ou soma acima do limite. | Encerrar com mensagem clara. | Aprovado. |
| Configuração inválida | Limites, temperatura ou endereço inválidos. | Rejeitar antes da chamada. | Aprovado. |
| Acesso recusado, simulado | Respostas HTTP 401 e 403. | Informar recusa sem expor detalhes do servidor. | Aprovado; ainda não há cenários distintos identificados como credencial ausente e inválida. |
| Modelo ausente, simulado | HTTP 404. | Orientar o download do modelo configurado. | Aprovado. |
| Serviço indisponível, simulado | HTTP 503. | Informar falha do serviço/carregamento. | Aprovado. |
| Comunicação e timeout, simulados | Exceções de conexão e leitura. | Encerrar com orientação compreensível. | Aprovado. |
| Resposta inválida, simulada | JSON inválido, conteúdo vazio ou geração incompleta. | Rejeitar sem salvar síntese. | Aprovado. |
| Referências inexistentes | Arquivo ou trecho inventado em resposta simulada. | Rejeitar a síntese. | Aprovado. |
| Proteção da saída | Destino existente ou dentro da pasta de entrada. | Impedir sobrescrita ou saída na entrada. | Aprovado. |
| Validação sem inferência | Execução com `--check`. | Não chamar o modelo nem criar saída. | Aprovado. |

A integração simulada usa transporte HTTP em memória: não requer servidor Ollama
nem baixa modelos. O serviço local padrão dispensa credenciais; o enunciado
permite simular esses cenários, mantendo uma execução real para o fluxo normal.
A saída de `examples/saida-esperada.md` continua sendo uma ilustração manual.

A conferência da saída real contra `examples/semana/` mostrou:

| Critério | Resultado observado |
| --- | --- |
| Cobertura dos assuntos | Resumo de funções/escopo, compreensão de listas e variáveis de ambiente. |
| Consolidação | Uma tarefa de revisar closures, com trechos das duas notas. |
| Pendência preservada | Resolver os exercícios de funções permaneceu na lista. |
| Conclusão reconhecida | A revisão de compreensão de listas aparece como concluída no resumo e não como tarefa pendente. |
| Referências | Os três trechos citados nas tarefas existem literalmente nos arquivos indicados. |
| Tarefas adicionais | Nenhuma tarefa sem apoio nas notas foi observada nessa saída. |

Essa evidência cobre um caso real, sem garantir o mesmo resultado em todas as
execuções. Ainda falta registrar uma execução real de `examples/sem-tarefas`,
para avaliar o comportamento quando não existem pendências.

## Falhas e limitações reais

- **Ollama indisponível na primeira tentativa:** a execução inicial pelo agente
  não conseguiu conectar ao servidor. O programa encerrou com código 1 e orientou
  abrir o aplicativo ou executar `ollama serve`. Posteriormente, o autor confirmou
  funcionamento local; a saída foi preservada em `evidencias/execucao-qwen-semana.md`.
- **Primeiro push sem commit:** o terminal apresentou `src refspec main does not
  match any`. A inspeção confirmou uma branch `main` ainda sem commits. A orientação
  foi criar o primeiro commit e repetir o push. O estado atual já apresenta dois
  commits e acompanhamento de `origin/main`.
- **README inicialmente centrado no macOS:** o autor apontou que o texto sugeria
  exclusividade da plataforma. Foram acrescentadas instruções para Linux e Windows,
  distinguindo compatibilidade prevista de validação efetivamente realizada.
- **Limites de interpretação e contexto:** validar um trecho literal não comprova
  a interpretação da tarefa. O limite de caracteres também não garante caber na
  janela de tokens; reduzir o contexto pode provocar truncamento pelo servidor.
  Essas limitações estão documentadas e exigem conferência da saída/configuração.

## Reprodutibilidade e versionamento

A primeira versão, com OpenAI, foi reinstalada e testada em uma cópia separada,
com novo ambiente virtual e cache de dependências. Uma tentativa com cache novo
falhou por resolução DNS do PyPI no ambiente restrito. Essa verificação não substitui
a validação em ambiente limpo da versão atual com Ollama/Qwen, ainda pendente.

Estado local do Git observado nesta atualização:

- Branch `main` acompanhando `origin/main`.
- Remoto: `https://github.com/MarcosLima744/p0-note-summarizer.git`.
- Commit inicial `dcba297`: protótipo com Qwen local.
- Commit `774c063`: ajuste da descrição de compatibilidade no README.
- Nenhuma tag local encontrada; PR e visibilidade pública ainda não verificados.

## Uso relevante de IA

Ferramenta utilizada: Codex, nesta sessão de desenvolvimento.

| Tarefa delegada | Resultado aproveitado | Correções ou alterações | Verificação |
| --- | --- | --- | --- |
| Entrevista para delimitar o problema. | Escopo de estudos, pasta semanal, resumo e tarefas referenciadas. | O autor escolheu múltiplos arquivos e excluiu sugestões livres. | Decisões confirmadas pelo autor antes da implementação. |
| Implementação, testes e documentação. | CLI Python, validações, Markdown e testes locais. | Integração inicial com OpenAI substituída por Ollama/Qwen a pedido do autor. | Suíte atual com 15 testes aprovados e funcionamento real confirmado pelo autor. |
| Revisão das instruções de uso. | README com instalação e execução. | Instruções ampliadas para Linux e Windows após observação do autor. | Conferência das instruções oficiais do Ollama e da alteração no arquivo. |
| Diagnóstico do erro de push. | Identificação da ausência do primeiro commit. | Orientação para criar o commit antes do push. | Estado posterior do Git com commits e acompanhamento do remoto. |

## Pendências e reflexão final

- Registrar as versões do Ollama/modelo e capturar o comando/log de uma execução.
- Acrescentar uma evidência real do caso sem tarefas; o caso semanal já foi conferido.
- Validar a versão atual em ambiente limpo seguindo apenas o README.
- Explicitar as simulações de credencial ausente e inválida.
- Registrar uma branch integrada por PR, confirmar acesso público e criar as tags.
- Gravar o vídeo, incluir o link e realizar as duas avaliações por pares no Moodle.
- O autor deve completar sua reflexão pessoal: principal aprendizado, competência
  mais desenvolvida e aspecto que ainda precisa aprimorar. Essa reflexão não foi
  fornecida e não foi inferida a partir do código.
