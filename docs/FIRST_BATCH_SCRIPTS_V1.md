# VERBO NO CHÃO — Primeira safra de roteiros originais (v1)

Estado: `DRAFT_REVIEW_REQUIRED` • `PENDING_INDEPENDENT_REVIEW`  
Escopo: três pautas originais da semana 01 — **nenhuma publicação ou geração de áudio autorizada**.

## Decisão técnica

O fluxo do GitHub executa:
`editorial_production` → `script_production` → 8 auditorias especializadas → coordenador.

O estágio `script_production` não depende de LLM externo, gasto ou contas: transforma três drafts editoriais versionados em **arquivos reais**, verificando a autenticidade do plano de 90 dias pelo hash SHA-256 declarado no relatório anterior. O estágio seguinte roda verificadores independentes de fontes/contexto e estrutura/retensão de roteiro. Os documentos ficam em artefatos do GitHub Actions por 14 dias, não são escritos como decisões aprovadas no repositório.

## Pacote produzido no workflow

- `operations/first_batch_scripts.json` — os três roteiros em seis blocos, contexto bíblico, referências de pesquisa, avaliação automatizada e bloqueios.
- `editorial-deliveries/first_batch_scripts.md` — material legível para revisão de contexto e narrativa.
- `editorial-deliveries/first_batch_report.json` — hashes dos arquivos, contagem e resultados dos gates.

Nome do artefato: `vnc-first-batch-scripts`. Nenhum arquivo de mídia, voz ou legenda é gerado nesta etapa.

## Pautas e verificação editorial

| Episódio | Referência | Gancho/título de trabalho | Estimativa por texto | Correção de contexto indispensável |
|---|---|---|---:|---|
| VNC-W01-E1 | Habacuque 1:2-4 | Quando você pergunta e nada muda | ~75 s | A denúncia envolve violência e injustiça social, não somente frustração individual |
| VNC-W01-E2 | Lamentações 3:19-26 | A esperança que não apaga a dor | ~80 s | O luto decorre da destruição de Jerusalém, não de um simples problema de ânimo |
| VNC-W01-E3 | Lucas 18:1-8 | Persistir sem transformar oração em cobrança | ~81 s | A viúva insiste por justiça; Deus é contrastado com o juiz injusto |

**Os tempos acima são estimativas textuais**, não áudio renderizado ou medido. Os três roteiros atendem ao alvo de 75 s dentro da tolerância do revisor automatizado; a duração final só será comprovada após gerar voz com licença comercial demonstrada.

## Fontes de contexto consultadas

São referências bibliográficas para revisão, não autorização de copiar conteúdo:

**Habacuque:**
- https://bibleproject.com/guides/book-of-habakkuk/
- https://classic.net.bible.org/passage.php?passage=hab+1%3A2-4

**Lamentações:**
- https://bibleproject.com/guides/book-of-lamentations/
- https://www.workingpreacher.org/commentaries/revised-common-lectionary/ordinary-13-2/commentary-on-lamentations-322-33-2

**Lucas:**
- https://www.workingpreacher.org/commentaries/revised-common-lectionary/ordinary-29-3/commentary-on-luke-181-8-4
- https://www.workingpreacher.org/commentaries/revised-common-lectionary/ordinary-29-3/commentary-on-luke-181-8-3

Riscos de interpretação são armazenados por episódio. Nenhuma citação literal de tradução bíblica foi inserida intencionalmente. **Verificação automatizada não comprova originalidade absoluta nem exegese correta**; a revisão independente continua obrigatória.

## Travas

- Originalidade do canal VERBO NO CHÃO, sem importar ativos ou motores editoriais de outros canais.
- `contracts/new_script_source_policy.json` é uma política nova, separada do contrato de fonte exclusivo do piloto Salmo 13.
- Piloto Salmo 13 e sua prévia são preservados e continuam bloqueados para publicação.
- Roteiros: `DRAFT_REVIEW_REQUIRED`; revisão bíblica: `PENDING_INDEPENDENT_REVIEW`.
- Citação literal de tradução moderna sem licença permanece bloqueada; comentários externos não podem ser copiados.
- Autorização de publicação, gravação de voz, gastos, licenças e publicação permanecem separadas.
- Sem data real de postagem; três Shorts por semana seguem uma hipótese não aprovada.
- Hashes de origem do plano são checados; ausência de arquivo/material ou alteração do plano rejeita a produção.
- Duplicação exata do roteiro, falsificação de aprovação, referências incompatíveis e promessas proibidas bloqueiam.

## Critérios de aceite de engenharia

- Testes unitários do contrato, novas regras e regressão do piloto devem passar.
- CI deve entregar estratégia, plano, três scripts e relatório dos oito especialistas sem alteração da branch `main`.
- O especialista de fontes verifica contexto e bibliografia registrada (não navega a internet sozinho no CI).
- O especialista de roteiros valida estrutura e duração, mas **não aprova áudio ou publicação**.
- O coordenador continua `BLOCKED` enquanto falta prova audiovisual, direitos/licenças, títulos/capas ou métricas.
- Merge apenas na ordem de dependência `PR #26` → `PR #27` → PR desta camada. A PR #25 de evidências físicas é independente e também ainda aguarda integração.

## Próximo gate após este PR

Revisar a fidelidade bíblica e a originalidade narrativa de cada roteiro, preparar o primeiro script candidato **sem promovê-lo automaticamente**, verificar direitos do pack exato de voz e só então executar geração de áudio e montagem com integridade física. Uma eventual aprovação do roteiro não autoriza publicação.
