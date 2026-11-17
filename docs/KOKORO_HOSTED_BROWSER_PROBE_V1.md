# VERBO NO CHÃO — Diagnóstico real do Kokoro Web no navegador

**Execução:** 17/11/2026 • **Escopo:** diagnóstico público passivo em Chrome no runner do GitHub • **Estado operacional de áudio:** `BLOCKED`

## Resultado real comprovado

Foi executada uma sessão real de Chrome com Playwright no site público
`https://kokoroweb.app/#demoContainer`.

No runner:
- `visit_succeeded = true`
- `selected_portuguese = true`
- `selected_alex = true`
- `matched_voice_response = false`
- `generate_clicked = false`, `tts_run = false`, `audio_generated = false`
- `errors = []`
- `status = BLOCKED_NO_MATCHED_HOSTED_VOICE_RESPONSE`

A sessão **não recebeu uma resposta identificável como `pm_alex.bin` ou `pm_alex.pt` com bytes verificáveis**, enquanto apenas se selecionava a voz. Esse resultado **não prova** que o site não usa esse arquivo, nem que houve diferença em relação ao fornecedor. A seleção visual do nome da voz não equivale a examinar os pesos de voz carregados ou o cache do Service Worker.

**Evidência operacional (workflow executado):**
https://github.com/BORELLITO/corte-fino-engine/actions/runs/44168520849

No GitHub Actions, o artefato `vnc-hosted-kokoro-passive-probe` contém o JSON real da inspeção. O relatório tem validade contextual para a sessão; **não é um atestado permanente do site, que pode mudar**. O artefato é retido por 14 dias.

## Como funciona

- `agents/hosted_browser_probe.py`: navega no domínio oficial público, lê a configuração básica da página, seleciona idioma e voz nos elementos HTML presentes, observa eventos de rede e limita armazenamento a metadados sanitizados.
- `.github/workflows/verbo-no-chao-hosted-runtime-probe.yml`: executa Chrome pré-instalado com biblioteca Playwright versionada, acionado por mudanças na própria camada e com limites de execução. Não fica monitorando continuamente; não usa cron nem chama API de síntese.
- `tests/test_hosted_browser_probe.py`: bloqueia falsa autorização de direitos, marcação enganosa de voz hospedada como verificada, URL insegura, segredos em queries e valores inconsistentes.

**Não há login, cookies exportados, screenshots privados, textos da conta, WAV, reprodução, publicação ou instalação local no telefone/PC.**

Apenas uma resposta que seja do arquivo de voz exato em domínio permitido, com tamanho controlado e SHA-256 esperado, pode ser anotada como resposta de rede correspondente ao upstream. Mesmo essa situação é classificada como `OBSERVED_VOICE_NETWORK_BYTES_MATCH_UPSTREAM_HOSTED_IDENTITY_UNCONFIRMED`, **não como voz ativa verificada**, pois uma resposta de rede não garante uso do recurso pelo motor de inferência, tampouco cobre cache ou versões históricas.

## Diagnóstico técnico

O domínio `kokoroweb.app` declara que a inferência acontece no navegador; a primeira síntese pode baixar aproximadamente 92–326 MB de modelo. Consulte https://kokoroweb.app/ .

A inspeção passiva não acionou a síntese e, por isso, não força o download nem o uso efetivo de `pm_alex`. Não é profissional inferir qual pack foi carregado somente pelos rótulos do seletor.

**Evidências separadas (que não se substituem):**

1. Hash real do `onnx-community/.../pm_alex.bin` baixado no GitHub Actions — ver PR #31.
2. Seleção de `Alex` no navegador real — este diagnóstico.
3. Arquivo efetivamente usado pela engine do navegador no momento da síntese — **ainda não comprovado**.
4. Licença e avisos das dependências/asset realmente utilizado — **ainda não comprovados integralmente**.
5. Revisão teológica humana, aprovação do roteiro, QA do WAV e autorização de publicação — **pendentes e independentes**.

## Próxima ação necessária

Um **smoke test técnico isolado** no navegador, com frase curta inventada exclusivamente para teste (não um roteiro do canal), inspecionando recursos/cache efetivamente usados na síntese, sem tratar esse áudio como material aprovado. Como isso força a obtenção de dezenas ou centenas de MB de modelos e pode depender da capacidade WebGPU/WASM do navegador, fazer apenas em sessão controlada e continuar em `BLOCKED` caso não haja evidência suficiente.

É importante manter aprovação editorial, direitos de voz, geração da master e publicação como gates separados. O Salmo 13 e os demais contratos não foram alterados.

## Governança de GitHub

Esta camada foi criada na branch `verbo-no-chao/hosted-runtime-probe-v1`, empilhada sobre a PR #31; a PR #25 permanece independente. O fluxo está restrito às branches `verbo-no-chao/**` e somente a alterações no próprio código/testes/workflow da prova, evitando visitas frequentes por alterações editoriais comuns. Em caso de rollback, descartar apenas esta camada; manter `bootstrap` e `main` congeladas.
