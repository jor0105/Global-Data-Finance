---
name: bash-linux
description: >
  Use para debugar, escrever ou otimizar scripts Bash e comandos Linux.
  Ative quando o usuário disser "preciso de um script bash", "como eu encadeio esses comandos?",
  "meu pipe está quebrando", "trata esse erro no bash", ou pedir ajuda para iterar arquivos,
  variáveis ou estruturar automações no terminal Linux.
---

# Bash & Linux Patterns

## Procedimento

### 1. Safety First (Unofficial Strict Mode)

Sempre inicie scripts Bash importantes com:

```bash
#!/usr/bin/env bash
set -euo pipefail
```

**Por quê:**

- `-e`: Evita falhas silenciosas em cadeia (sai imediatamente se qualquer comando falhar e retornar != 0).
- `-u`: Trata variáveis não definidas como erro. Evita catástrofes como `rm -rf /$VAR/` quando `$VAR` está vazia.
- `-o pipefail`: Garante que se um comando no meio de um pipe falhar, o pipe inteiro falhará. Por padrão, o Bash retorna apenas o código de saída do último comando do pipe.

### 2. Error Handling e Clean Up

Sempre crie mecanismos de `trap` para recursos temporários e envie mensagens de erro para o `stderr`.

```bash
# Executar limpeza em caso de erro ou término (try/finally do Bash)
cleanup() {
    rm -rf "$TMP_DIR"
    echo "Limpou recursos." >&2
}
trap cleanup EXIT ERR

# Verificar se um comando existe antes de usar
if ! command -v jq &> /dev/null; then
    echo "Erro: jq não está instalado." >&2
    exit 1
fi
```

**Por quê:** Enviar erros para `stdout` em vez de `stderr` (`>&2`) corrompe pipes que consumam a saída do seu script. Sempre isole mensagens de diagnóstico do retorno de dados reais.

### 3. Piping e Redirecionamento

Utilize redirecionamento de forma eficiente e agrupe execuções se necessário.

```bash
# Redirecionar stdout e stderr para o mesmo lugar
comando > log.txt 2>&1

# Não logar nada
comando > /dev/null 2>&1

# Passar variável como input (Herestring)
grep "error" <<< "$LOG_DATA"

# Agrupar comandos em uma subshell (executa no mesmo contexto de pipe/redirecionamento)
(cd /tmp && tar -xzf archive.tar.gz && ./install)
```

**Anti-pattern: Cat inútil**
Nunca use `cat` apenas para enviar um arquivo para um comando que já aceita arquivos como argumento.

```bash
# ERRADO
cat file.txt | grep "error"

# CORRETO
grep "error" file.txt
```

**Por quê:** O "cat inútil" gera um processo adicional desnecessário e consome recursos sem agregar valor, além de ser considerado um anti-pattern clássico em bash.

### 4. Manipulação Segura de Variáveis

Assegure-se de lidar com espaços em nomes de arquivos e variáveis indefinidas.

```bash
# Sempre use aspas duplas ao referenciar variáveis
rm "$FILE"        # CORRETO — lida com espaços no nome "meu arquivo.txt"
rm $FILE          # ERRADO — passará "meu" e "arquivo.txt" como dois argumentos distintos

# Default values
echo "${VAR:-default}"  # Usa "default" se VAR estiver vazia/não definida

# String replacement
echo "${VAR/foo/bar}"   # Substitui primeira ocorrência de foo por bar
echo "${VAR//foo/bar}"  # Substitui todas
```

**Por quê:** O bash faz _word splitting_ por padrão. Uma variável não protegida por aspas duplas pode ser quebrada em vários argumentos se contiver espaços, causando falhas imprevisíveis.

### 5. Estruturas de Controle Seguras

Evite parsear o output de `ls`. Use `find` com delimitadores nulos para iterar por arquivos com caracteres especiais de forma previsível.

```bash
# For loop seguro com find/xargs (lida com espaços e quebras de linha)
find . -name "*.log" -print0 | while IFS= read -r -d '' file; do
    echo "Processando $file"
done

# If para checagem de condicional
if [[ -f "$FILE" ]]; then
    echo "Arquivo regular existe"
elif [[ -d "$DIR" ]]; then
    echo "Diretório existe"
fi
```

**Dica:** Sempre use `[[ ]]` no Bash em vez de `[ ]`.
**Por quê:** `[[ ]]` é a estrutura de teste nativa do Bash. Ela suporta operadores regex (`=~`), não sofre de word splitting inesperado e não falha se variáveis estiverem vazias, ao contrário do clássico `[ ]` (POSIX).

## Exemplos

### Caso positivo

**Entrada:** Usuário pede um script para apagar todos os arquivos `.tmp` em um diretório, logando se falhar.
**Saída esperada:** Fornecer um script usando `#!/usr/bin/env bash`, `set -euo pipefail`, e utilizando `find . -name "*.tmp" -delete`, validando previamente se o diretório existe com `[[ -d "$DIR" ]]`.

### Caso negativo

**Entrada:** Usuário envia um script PowerShell (`.ps1`) com erro de sintaxe.
**Por quê não:** Tarefa de automação em Windows foge do escopo da skill `bash-linux`. O problema e as permissões de terminal mudam radicalmente de ambiente. Direcione ou ative o contexto da skill `powershell-windows`.

## Evals de trigger

Deve acionar:

- "escreve um script para limpar os logs antigos"
- "por que meu laço for iterando as linhas desse txt está quebrando os espaços?"
- "me ajuda com um shell script"
- "cria um script bash para o CI"
- "o que faz a flag pipefail no bash?"
- "meu pipe com xargs está quebrando, consegue ajustar?"

Não deve acionar:

- "quero fazer um script python que chama o terminal" (use `python-patterns`)
- "como configuro meu servidor nginx?" (use `server-management`)
- "meu bat/powershell ta dando erro" (use `powershell-windows`)
- "cria um Dockerfile multi-stage" (use `deployment-procedures`)

## Evals de workflow

### Cenário 1

**Entrada:** usuário pede um script para apagar `*.tmp` e registrar falhas em `stderr`.

**Assertions:**

- [ ] o script inclui `#!/usr/bin/env bash`
- [ ] o script inclui `set -euo pipefail`
- [ ] mensagens de erro usam `>&2`

### Cenário 2

**Entrada:** usuário pede para iterar arquivos `.log` que podem ter espaços no nome.

**Assertions:**

- [ ] a solução evita `for file in $(ls ...)`
- [ ] a solução usa `find ... -print0` com `read -r -d ''`
- [ ] a variável de arquivo é usada entre aspas
