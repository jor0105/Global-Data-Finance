---
name: powershell-windows
description: >
  Use para escrever, depurar ou adaptar scripts PowerShell e comandos Windows.
  Ative quando o usuário pedir ".ps1", "PowerShell deu erro", "meu pipeline
  não funciona", "qual o equivalente disso no Windows", "pwsh está quebrando
  acentos", "como chamar um .exe no PowerShell" ou automação Windows com
  compatibilidade 5.1/7+.
---

# PowerShell & Windows Patterns

## Procedimento

### 1. Confirme runtime, alvo e piso de compatibilidade

Antes de mudar o script, descubra se ele roda em Windows PowerShell 5.1,
PowerShell 7+ (`pwsh`) ou precisa funcionar nos dois. Essa decisão muda sintaxe,
encoding, cmdlets disponíveis e até o comportamento da integração com processos
externos.

```powershell
$PSVersionTable.PSVersion
$PSEdition
```

Quando a compatibilidade estiver ambígua, favoreça o subconjunto que roda em 5.1
e declare o requisito mínimo se o script depender de recursos novos.

```powershell
#Requires -Version 5.1
# ou
#Requires -Version 7.0
```

**Por quê:** `??`, `?.`, operador ternário e `ForEach-Object -Parallel` não
existem em 5.1. Se o alvo real for 5.1, usar sintaxe de 7+ quebra antes de a
automação começar.

### 2. Faça o script falhar cedo e de forma observável

Para automação, ative modo estrito e promova erros não-terminantes para
terminantes.

```powershell
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

try {
    $response = Invoke-RestMethod -Uri $Uri -ErrorAction Stop
}
catch {
    Write-Error "Falha na chamada HTTP: $_"
    exit 1
}
```

Quando chamar executáveis nativos, trate o código de saída explicitamente.

```powershell
& git diff --quiet
if ($LASTEXITCODE -ne 0) {
    Write-Error 'git diff retornou falha'
    exit $LASTEXITCODE
}
```

**Por quê:** muitos cmdlets emitem erros não-terminantes por padrão. Sem
`$ErrorActionPreference = 'Stop'`, o script pode continuar com estado parcial e
falhar só muito depois, dificultando diagnóstico.

### 3. Preserve pipeline de objetos; não parseie texto formatado

PowerShell passa objetos no pipeline. Prefira filtrar por propriedades reais em
vez de reaproveitar saída formatada de `dir`, `findstr` ou `Format-*`.

```powershell
Get-Process |
    Where-Object { $_.CPU -gt 10 } |
    Select-Object Name, CPU

Get-ChildItem -Path $Root -Filter '*.log' -File |
    Select-Object -ExpandProperty FullName
```

**Anti-patterns comuns:**

```powershell
# ERRADO: parseia texto formatado
dir | findstr ".log"

# ERRADO: mostra no console, mas não devolve dados para o pipeline
Get-ChildItem | ForEach-Object { Write-Host $_.Name }
```

```powershell
# CORRETO: usa propriedades do objeto
Get-ChildItem -Path $Root -Filter '*.log' -File |
    ForEach-Object { $_.Name }
```

**Por quê:** a camada de formatação do PowerShell não é API estável. `Write-Host`
também envia saída só para a tela; se outro comando precisar consumir esses
dados, o pipeline fica vazio.

### 4. Seja explícito com paths, quoting e argumentos de executáveis

Use `-LiteralPath` quando o caminho vier de input externo ou puder conter
caracteres especiais. Monte caminhos com `Join-Path` e passe argumentos nativos
como lista, não como uma string concatenada.

```powershell
$filePath = Join-Path $Root 'meu arquivo.txt'
$content = Get-Content -LiteralPath $filePath -Encoding UTF8

$rgArgs = @('--glob', '*.log', 'ERROR', $filePath)
& rg.exe @rgArgs
```

```powershell
$name = 'Jordan'
"Hello, $name"
'Hello, $name'
"Temp: $($env:TEMP)"
```

Evite `Invoke-Expression` para montar linhas de comando.

**Por quê:** strings concatenadas quebram fácil com espaços, aspas e caracteres
especiais. Arrays de argumentos preservam fronteiras entre parâmetros e reduzem
erros difíceis de reproduzir.

### 5. Torne encoding e I/O explícitos, principalmente em 5.1

Windows PowerShell 5.1 tem defaults heterogêneos: `Out-File` e redirecionamento
costumam cair em UTF-16 LE, enquanto integração com programas nativos depende da
code page atual. PowerShell 7+ melhora isso com UTF-8 por padrão em grande parte
dos casos, mas ainda vale ser explícito quando o arquivo vai cruzar fronteiras.

```powershell
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

$content = Get-Content -LiteralPath $InputPath -Encoding UTF8
Set-Content -LiteralPath $OutputPath -Value $content -Encoding UTF8
```

Quando encoding importar, prefira `Set-Content` ou `Out-File -Encoding ...` a
redirecionamento cru com `>` ou `>>`.

**Por quê:** acentos quebrados, CSV ilegível e diffs binários falsos quase sempre
vêm de defaults implícitos de encoding, especialmente quando 5.1 e executáveis
nativos entram no fluxo.

### 6. Use operadores e comparações de PowerShell, não de Bash/C

Quando estiver convertendo comandos ou corrigindo scripts misturados, troque
operadores emprestados de outras shells pela sintaxe nativa do PowerShell.

```powershell
if ($value -eq 'expected') { 'ok' }
if ($a -gt 0 -and $b -lt 10) { 'ok' }

'ABC' -eq 'abc'   # True
'ABC' -ceq 'abc'  # False
```

```powershell
# ERRADO
if ($value == 'expected') { 'ok' }
if ($a > 0 && $b < 10) { 'ok' }
```

**Por quê:** `-eq`, `-ne`, `-gt`, `-lt`, `-and` e `-or` fazem parte da gramática
esperada do PowerShell. Misturar sintaxe de Bash, JavaScript ou C introduz erro
de parsing e também mascara que comparações de string são case-insensitive por
padrão.

## Compatibilidade 5.1 vs 7+

| Feature | Windows PowerShell 5.1 | PowerShell 7+ |
| --- | --- | --- |
| Plataforma | Windows | Windows, Linux, macOS |
| Encoding padrão | heterogêneo / legado | UTF-8 na maior parte dos casos |
| `??` e `?.` | ❌ | ✅ |
| Operador ternário | ❌ | ✅ |
| `ForEach-Object -Parallel` | ❌ | ✅ |

Se o pedido não disser a versão, assuma que compatibilidade ampla importa e evite
recursos exclusivos de 7+ até provar o contrário.

## Exemplos

### Caso positivo

**Entrada:** Usuário cola um `.ps1` que chama API, continua após erro e salva um
arquivo com acentos quebrados.

**Saída esperada:** Corrigir com `Set-StrictMode`, `$ErrorActionPreference =
'Stop'`, `try/catch`, `-ErrorAction Stop` nas bordas relevantes e escrita com
encoding explícito.

### Caso negativo

**Entrada:** Usuário pede um script Bash para Linux ou um ajuste específico de
shell POSIX.

**Por quê não:** O problema depende de semântica de Bash/Linux. Use a skill
`bash-linux`; quoting, pipeline e tratamento de erro mudam bastante entre os
ambientes.

## Evals de trigger

Deve acionar:

- "meu .ps1 falha no pipeline"
- "qual o equivalente disso no Windows sem usar bash?"
- "pwsh 7 grava arquivo com acento quebrado"
- "como chamar um .exe no PowerShell sem quebrar os argumentos?"
- "PowerShell 5 continua mesmo quando o comando dá erro"

Não deve acionar:

- "script bash no Linux"
- "esse arquivo .bat puro está quebrado e eu não quero migrar para PowerShell"
- "comando SQL"
- "me ajuda com Python async"

## Evals de workflow

### Cenário 1

**Entrada:** usuário pede para corrigir um script PowerShell 5.1 que baixa dados
de uma API e grava JSON com encoding errado.

**Assertions:**

- [ ] a solução ativa `$ErrorActionPreference = 'Stop'`
- [ ] a solução usa `try/catch`
- [ ] a solução evita depender de `>` quando encoding importa
- [ ] a solução grava arquivo com `-Encoding` explícito

### Cenário 2

**Entrada:** usuário quer iterar `.log` com espaços no nome e passar cada arquivo
para `rg.exe`.

**Assertions:**

- [ ] a solução usa `Get-ChildItem` ou propriedades de objeto em vez de parsear `dir`
- [ ] a solução usa `-LiteralPath`, `FullName` ou outro caminho seguro para espaços
- [ ] a solução não usa `Write-Host` para produzir os dados do pipeline
- [ ] a chamada ao executável nativo não depende de uma string concatenada única
