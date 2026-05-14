---
name: nodejs-best-practices
description: >
  Use para diagnosticar e corrigir problemas de runtime Node.js: conflito entre ESM
  e CommonJS, script `npm` que nao sobe, import que quebra em producao, dependencia
  no lugar errado, I/O sincronico em caminho concorrente, ou handler que trava o
  processo. Ative quando o usuario disser "ERR_REQUIRE_ESM", "Cannot use import
  statement outside a module", "meu script Node nao roda", "esse package.json esta
  estranho", "isso fica em dependency ou devDependency?", "por que esse handler
  trava?" ou pedir revisao de script/servico Node. Nao use para modelagem de banco,
  layout frontend, ou configuracao de bundler puramente visual sem impacto no runtime
  Node.
---

# Node.js Best Practices

## Contexto nao-obvio

Erros de Node raramente moram so no arquivo que falhou. Eles costumam aparecer na
fronteira entre `package.json`, comando de entrada, formato gerado pelo build,
versao do Node e dependencia instalada. A skill existe para forcar essa leitura por
boundary antes de editar codigo.

## Procedimento

1. Identifique o ponto real de execucao: comando afetado, pacote afetado em caso de
   monorepo, versao do Node, gerenciador de pacotes e arquivo de entrada. Isso vem
   antes da correcao porque muitos erros sao de bootstrap ou ambiente, nao de logica.
2. Classifique o problema em uma categoria: modulo/resolucao, dependencia,
   async/I/O, CPU/event loop, ou script de automacao. Nao trate tudo como "erro de
   import" ou "problema do npm".
3. Resolva o modelo de modulo antes do resto. Escolha um unico modelo por pacote
   (`ESM` ou `CJS`) e alinhe source, build e comando de execucao com essa escolha,
   porque misturas parciais geram correcoes cosmeticas e regressao no proximo entrypoint.
4. Revise dependencias com criterio de runtime. Pacotes usados em execucao ficam em
   `dependencies`; tipos, lint, test runner e bundler ficam em `devDependencies`.
   Isso importa porque drift de instalacao e imagem de deploy inchada parecem bug de
   codigo quando o problema e classificacao errada.
5. Inspecione concorrencia e latencia. Em caminhos HTTP, fila ou worker, prefira
   APIs async e paralelize apenas operacoes realmente independentes. Mantenha
   sequencial quando houver dependencia de ordem, limite externo ou side effect.
6. Trate trabalho CPU-bound explicitamente. Parsing pesado, compressao, crypto e
   loops longos podem bloquear o event loop; nesses casos proponha offload para
   worker, job ou etapa offline em vez de apenas "otimizar".
7. Valide no comando que falhava originalmente. Reexecutar `npm run ...`, `node ...`
   ou o processo de deploy relevante e parte da correcao, porque bugs de Node
   aparecem no bootstrap real, nao so no trecho editado.
8. Na resposta final, deixe explicitos: boundary afetado, modelo de runtime
   escolhido, risco evitado e comando que confirmou a correcao.

## Heuristicas de decisao

- Prefira `ESM` em codigo novo quando o pacote e o toolchain ja suportam esse
  modelo. Se o pacote inteiro ainda e `CJS`, manter consistencia costuma ser menos
  arriscado do que migrar so para silenciar um erro isolado.
- So aceite interop `ESM`/`CJS` como excecao consciente na borda do pacote. Mistura
  casual em arquivos internos tende a quebrar resolucao, mocking e bootstrap.
- `fs.readFileSync`, `crypto.*Sync` e `JSON.parse` grande em handler HTTP merecem
  suspeita imediata porque latencia local pequena pode virar fila sob concorrencia.
- Em script CLI de uso pontual, APIs sincronas podem ser aceitaveis se simplificarem
  o fluxo e nao houver impacto de concorrencia. O risco aqui nao e "sync ruim", e
  usar a mesma decisao em runtime servidor.
- Antes de culpar o Node, confirme se o output transpilado, extensao do arquivo, ou
  campo `type` do `package.json` nao estao se contradizendo.

## Anti-patterns a evitar

- Corrigir `ERR_REQUIRE_ESM` trocando um arquivo para `import` sem alinhar
  `package.json`, extensoes e comando de execucao.
- Jogar uma dependencia em `dependencies` "para garantir" quando ela so existe para
  build, lint ou tipos.
- Sequenciar `await` independentes em caminho quente sem motivo real, aumentando
  latencia e mascarando gargalos.
- Migrar para worker thread sem provar que o gargalo e CPU-bound; isso adiciona
  complexidade e pode esconder problema de I/O ou de consulta externa.
- Diagnosticar bundler/frontend puro com esta skill. Se o problema principal e Vite,
  Tailwind ou layout, use a skill do dominio correspondente; aqui o foco e quando o
  artefato final nao conversa com o runtime Node.

## Formato de saida esperado

Quando a skill orientar uma resposta analitica, organize a conclusao em quatro
blocos curtos:

1. `Boundary`: onde o problema realmente acontece.
2. `Causa raiz`: incompatibilidade, classificacao errada de dependencia, bloqueio de
   event loop, ou outro motivo comprovado.
3. `Correcao`: decisao aplicada e trade-off principal.
4. `Validacao`: comando ou fluxo que prova que o runtime voltou a funcionar.

## Exemplos

### Caso positivo
**Entrada:** "Depois de atualizar uma lib, meu script Node passou a dar `ERR_REQUIRE_ESM`."
**Saida esperada:** Identificar o pacote e o entrypoint afetados, escolher um modelo
de modulo coerente para o pacote, ajustar a borda de interoperabilidade se
necessario e validar no comando real que falhava.

### Caso positivo
**Entrada:** "Meu handler Express esta lento e as requisicoes ficam presas."
**Saida esperada:** Diferenciar I/O de CPU-bound, procurar APIs sincronas ou trabalho
pesado no request path, propor async/offload quando fizer sentido e explicar o risco
de bloquear o event loop.

### Caso negativo
**Entrada:** "Configura a paleta e o layout do meu app React."
**Por que nao:** O problema central e frontend/design, nao runtime Node.

### Caso negativo
**Entrada:** "Desenha a schema dessa tabela Postgres."
**Por que nao:** O foco e modelagem de dados; use `database-design`.

## Evals de trigger

Deve acionar:
- "to com `ERR_REQUIRE_ESM` depois de atualizar uma dependencia"
- "o Docker sobe, mas `npm start` quebra com `Cannot use import statement outside a module`"
- "isso entra em dependency ou devDependency?"
- "meu worker Node trava o processo quando recebe um arquivo grande"

Nao deve acionar:
- "configura o Tailwind desse dashboard"
- "faz a migration dessa tabela no Postgres"
- "me ajuda com o layout mobile dessa tela"
- "quero um bundler mais bonito pro frontend"

## Evals de workflow

### Cenario: conflito entre ESM e CJS
- [ ] output identifica o pacote ou entrypoint afetado
- [ ] output escolhe um unico modelo de modulo para o pacote
- [ ] output nao recomenda mistura interna casual de `require` e `import`
- [ ] output menciona validacao no comando real que falhava

### Cenario: latencia ou travamento em runtime Node
- [ ] output classifica o gargalo como I/O, CPU-bound, ou dependencia externa
- [ ] output explica por que o event loop pode estar bloqueando
- [ ] output propoe async, paralelizacao controlada ou offload de forma especifica
- [ ] output evita sugestao generica de "otimizar" sem mecanismo concreto
