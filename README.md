# Síntese semanal de estudos

Aplicação Python local que transforma os arquivos `.txt` de uma semana em resumo
por assunto e lista de pendências, para ajudar a decidir o próximo estudo.
Utiliza um único modelo Qwen pelo Ollama.

## Compatibilidade

A aplicação foi escrita para funcionar em macOS, Linux e Windows, com Python
3.11+, uv e Ollama instalados. O código usa caminhos portáveis e se comunica com
o modelo pela API HTTP local; não depende de recursos exclusivos do macOS.

O ambiente utilizado no desenvolvimento e a execução real confirmada pelo autor
foram em macOS. Linux e Windows ainda precisam de validação prática. O desempenho
do modelo depende da memória, do processador e da aceleração disponível.

## Preparar o modelo

Instale o Ollama conforme seu sistema:

| Sistema | Instalação e inicialização |
| --- | --- |
| macOS | Instale o [aplicativo para macOS](https://ollama.com/download/mac) e abra-o. |
| Windows | Instale o [aplicativo para Windows](https://ollama.com/download/windows); ele executa o servidor em segundo plano. Veja os [requisitos do sistema](https://docs.ollama.com/windows). |
| Linux | Siga o [guia oficial de instalação](https://docs.ollama.com/linux) e inicie o serviço ou execute `ollama serve`. |

Com o servidor em execução, baixe o modelo em um terminal (PowerShell no Windows):

```sh
ollama pull qwen3:4b-instruct
```

O [qwen3:4b-instruct](https://ollama.com/library/qwen3:4b-instruct) tem download de
aproximadamente 2,5 GB. Memória para execução é adicional e depende do contexto.
O download requer internet; depois, o modelo roda no computador. O servidor padrão
fica em `http://localhost:11434`. Se preferir executar o servidor pelo terminal,
use `ollama serve` e mantenha esse terminal aberto. Não inicie outro servidor se
já houver uma instância em execução.

## Instalação e execução

Requer Python 3.11+ e [uv](https://docs.astral.sh/uv/getting-started/installation/).
Dentro da pasta do projeto, os comandos abaixo são os mesmos no terminal do
macOS/Linux e no PowerShell do Windows:

```sh
uv sync --locked
uv run note-summarizer examples/semana --check
uv run note-summarizer examples/semana --output output/semana.md
```

`--check` valida arquivos e configuração sem conectar ao Ollama, carregar modelo
ou criar saída. A execução normal mostra o resultado no terminal e salva Markdown.
Também funciona com `uv run python -m note_summarizer ...`.

O destino padrão é `output/sintese.md`. Arquivos existentes nunca são
sobrescritos: escolha outro nome nas execuções posteriores. A saída precisa ficar
fora da pasta de entrada.

## Configuração opcional

Os padrões já funcionam sem `.env`. Se desejar ajustá-los, copie `.env.example`
para `.env` **caso ainda não tenha esse arquivo** e edite os valores. Se já houver
um `.env` da versão anterior, as variáveis `OPENAI_*` não são mais utilizadas;
adicione as variáveis abaixo conforme necessário. Não é preciso gerar chave.

| Variável | Padrão | Uso |
| --- | --- | --- |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Endereço do servidor local, sem `/api` |
| `OLLAMA_MODEL` | `qwen3:4b-instruct` | Modelo local previamente baixado com `ollama pull` |
| `OLLAMA_TIMEOUT` | `300` | Timeout de rede, em segundos |
| `OLLAMA_MAX_OUTPUT_TOKENS` | `6000` | Limite de geração (`num_predict`) |
| `OLLAMA_CONTEXT_LENGTH` | `32768` | Janela de contexto (`num_ctx`), incluindo entrada e saída |
| `OLLAMA_TEMPERATURE` | `0` | Temperatura de geração, entre 0 e 2 |
| `NOTES_MAX_INPUT_CHARS` | `24000` | Limite local da soma de caracteres das notas |

O `.env` é carregado apenas a partir do diretório de execução; variáveis exportadas
prevalecem. A aplicação aceita somente endereços de loopback (`localhost`,
`127.0.0.1`, `::1`), sem proxies ou redirects. Não envia notas à OpenAI.

O limite de caracteres não equivale a uma contagem de tokens. Mantenha contexto
suficiente para entrada, esquema e saída: diminuir o contexto pode causar
truncamento pelo servidor. Contextos maiores consomem mais memória. Resposta
incompleta não é salva. Não há retries automáticos; cada execução faz uma chamada.

## Entrada e resultado

- Somente arquivos `.txt` diretamente na pasta, em UTF-8 (BOM opcional).
- Ordenação alfabética; sem leitura de subpastas ou links simbólicos.
- Arquivos vazios são ignorados. Pasta sem conteúdo útil impede a chamada.
- Datas no nome/conteúdo ajudam o modelo; ordem alfabética não prova cronologia.
- Erros de leitura e excesso do limite local interrompem o fluxo, sem cortar arquivos.

O resumo agrupa conteúdos estudados e dificuldades por assunto. As tarefas devem
ter apoio explícito nas notas, incluindo dificuldades como “não entendi closures”.
Repetições são consolidadas; tarefas claramente concluídas são excluídas;
conflitos são marcados para conferência. Não há sugestões externas nem criação de
prazos ou prioridades. Sem pendências: “Nenhuma tarefa identificada.”

Cada tarefa contém nome do arquivo e trecho literal. O programa valida a existência
dessas referências antes de salvar. Isso não comprova a interpretação semântica
do modelo: confira a síntese antes de planejar seus estudos.

A integração usa [`POST /api/chat`](https://docs.ollama.com/api/chat), sem streaming,
com o esquema Pydantic no campo `format`, conforme a documentação de
[saídas estruturadas](https://docs.ollama.com/capabilities/structured-outputs).
Logs em stderr contêm apenas contagens e etapas, sem textos ou respostas.

## Testes e avaliação

```sh
uv run python -m unittest discover -s tests -v
```

Os testes são locais, com arquivos temporários e transporte HTTP simulado. Não
requerem Ollama nem baixam modelos. Cobrem leitura, limites, configuração, referências,
saída, modelo ausente, falhas de acesso, resposta vazia/incompleta, comunicação e timeout.

Para avaliar a qualidade **com o modelo real**, execute os exemplos e confira:

| Entrada | Resultado esperado |
| --- | --- |
| `examples/semana` | Resumo de funções/escopo e configuração de API; tarefa de revisar closures consolidada com referências às duas notas; exercícios de funções pendentes; revisão de compreensão de listas excluída por ter sido concluída |
| `examples/sem-tarefas` | Resumo de listas/tuplas e nenhuma tarefa |

A avaliação semântica ainda depende de execução real. Os testes simulados não
comprovam que o Qwen consolidou tarefas ou reconheceu conclusões corretamente.
[examples/saida-esperada.md](examples/saida-esperada.md) é uma ilustração manual.

Se houver erro de conexão, abra o Ollama ou execute `ollama serve`. Para modelo
não encontrado, execute `ollama pull` com o mesmo nome de `OLLAMA_MODEL`. Para timeout,
aumente `OLLAMA_TIMEOUT`, reduza a entrada ou experimente um modelo menor.

## Organização e situação do P0

- `config.py`: variáveis de ambiente e validação.
- `notes.py`: leitura e validação do destino.
- `llm.py`: instruções, entrada e chamada ao Ollama.
- `summary.py`: estrutura da resposta, referências e Markdown.
- `cli.py`: argumentos e coordenação do fluxo.

As versões exatas estão em `uv.lock`. Ambiente usado: Python 3.13.12,
HTTPX 0.28.1, Pydantic 2.14.3 e python-dotenv 1.2.4. A versão do Ollama e o modelo
instalado deverão ser registrados quando ocorrer a execução real (`ollama --version`
e `ollama list`).

O diretório recebido não era um repositório Git. Histórico incremental, PR,
publicação no GitHub, tags/releases, vídeo e demais evidências acadêmicas ainda
precisam ser construídos. Os requisitos originais estão em `context/`; a tag do
Avançado está sem nome nesse material. Como o serviço local não exige autenticação,
os erros de credencial/acesso são demonstrados por respostas HTTP 401/403 simuladas.
Veja [RELATORIO_EXECUCAO.md](RELATORIO_EXECUCAO.md) para as verificações realizadas.
