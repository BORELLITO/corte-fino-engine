# E01 v2 — curadoria de filmagem REAL: lote de pesquisa 1

**Estado:** `PAGE_METADATA_CURATED_FILES_NOT_ACQUIRED` — sem master, sem direitos liberados, sem publicação.

A continuidade canônica está em `verbo-no-chao/e01-v2-12-scene-visual-roughcut-v1`. Esta branch isolada mantém o roteiro, a narração de 70,425s, 28 legendas e o roughcut original intactos. Este lote procura **filmagem realmente gravada**, diferente de imagens geradas com movimento artificial.

## Candidatos encontrados em páginas oficiais Pexels (17/11/2026)

| Cena | Origem Pexels | Duração da página | Formato da página | Risco específico |
|---|---|---:|---|---|
| S03 — injustiça / ambiente social | https://www.pexels.com/video/rainy-day-in-a-quiet-urban-street-40417800/ | 12s | 2160×3840; 60fps | pessoas e letreiros comerciais |
| S05 — corredor simbólico | https://www.pexels.com/video/an-empty-hallway-6010698/ | 9s | 2160×3840; 25fps | é ambiente moderno, não arquitetura bíblica |
| S08 — fé sem fingimento | https://www.pexels.com/video/close-up-video-of-a-man-praying-7350189/ | 15s | 2160×3840; 25fps | pessoa e personagem visual não coincidem |
| S09 — reflexão escrita | https://www.pexels.com/video/a-person-writing-in-the-notebook-5904567/ | 10s | 2160×3840; 23.98fps | texto legível, mãos/identidade divergentes |

**Proveniência:** a página de cada vídeo exibia licença Free, autor, dimensões e botão Free Download; o endereço CDN foi observado pelo redirecionamento oficial `/download/video/<id>/`. Isso **não** comprova a integridade dos bytes MP4 nem eventuais direitos de terceiros. Nenhum arquivo foi transferido no momento desta curadoria.

A candidata S08 pode não servir: o enquadramento mostra um homem em oração em vez das mãos da figura anônima em ambiente doméstico do storyboard. A candidata S05 pode ser uma metáfora visual, **nunca** uma suposta reconstrução histórica da Judeia bíblica. Não incluir um plano apenas porque ele é 4K.

## Execução gratuita e segurança

- `python -m agents.e01_stock_candidates` valida os contratos sem rede, sem contas e sem credenciais.
- No GitHub Actions, workflow `verbo-no-chao-e01-stock-probe.yml` executa download **temporário** de no máximo 4 candidatos, com host/CDN allowlist, limite de 140 MiB por arquivo, `ffprobe`, hash SHA-256 e decodificação completa por FFmpeg.
- Arquivos MP4 não são commitados, publicados, disponibilizados em artifacts nem enviados ao usuário como se tivessem licença confirmada. Somente relatório técnico JSON sobrevive à execução.
- Mesmo que o probe seja positivo, `editorial_status=PENDING_FRAME_REVIEW`, `third_party_rights=PENDING_REVIEW`, `footage_approved_for_edit=false` e `publication_authorized=false`.
- Para integrar na montagem é indispensável avaliar início/meio/fim dos MP4, marcas, pessoas, contexto religioso, cor, composição, safe zones, texturas e continuidade; escolher apenas os melhores e vincular hash físico ao pacote durável e autorizado.
- Uso de Pexels: https://www.pexels.com/license/ ; a licença geral não substitui direitos de terceiros, release de imagem ou validação factual.
- A API Pexels não é necessária para este lote inicial: evita criar e armazenar chave sem autorização, reduz manutenção e mantém custo em zero na configuração pública padrão do Actions. Para escala futura, API gratuita com consentimento e segredo privado pode substituir a curadoria manual.

**Não confundir:** PASS em CI ou hash de stock jamais transforma um roughcut de 720×1280 em master 1080×1920 nem autoriza uso comercial de voz/trilha. Os outros bloqueios preexistentes continuam ativos.

Próximo gate: observar o relatório físico de bytes do Actions; comparar a real qualidade dos 4 clipes, substituir *somente* os planos que melhorarem E01 e avançar a montagem final depois do parecer de direitos e QA.


## Evidência física real posterior (18/11/2026, 01:58 UTC)

**GitHub Actions:** https://github.com/BORELLITO/corte-fino-engine/actions/runs/44219643779 — SUCCESS. O runner instalou FFmpeg/FFprobe, baixou os **4 MP4 reais para disco temporário**, mediu duração, dimensões e codec H.264, calculou SHA-256 e decodificou integralmente os quatro arquivos sem erro. O relatório foi preservado em artifact GitHub ID `14389892333` (retenção: sete dias). Nenhum vídeo bruto foi enviado como artifact nem inserido no repositório.

As medidas e hashes registrados em `contracts/e01_v2_stock_physical_probe_evidence_v1.json` permitem comparar futuramente a mesma origem CDN (re-download obrigatório e SHA idêntico). O guardião `agents/e01_stock_probe_evidence.py` rejeita evidências incompletas, mudança de origem ou falsas aprovações e tem testes adversariais.

**Limite explícito:** os MP4 foram destruídos com o diretório temporário do runner. Não existe biblioteca de stock durável nem 1080×1920 master gerado. Sem inspeção de quadros/pessoas/logos e sem documentação adicional dos direitos, seguem como `PENDING_FRAME_REVIEW` / `PENDING_REVIEW`, e a publicação continua proibida.
## Upgrade: auditoria técnica de 12 frames sem expor MP4 (candidato)

O arquivo `agents/e01_stock_frame_qa.py` recaptura os quatro filmes sob hash fixado, decodifica integralmente com FFmpeg, extrai três quadros de cada clipe (15%, 50%, 85% do tempo), mede brilho/contraste/diferença visual e monta **somente uma folha de contato reduzida** de QA interno. A folha identifica as cenas e tem aviso "NÃO PUBLICAR". MP4s permanecem no diretório temporário e são descartados. O artefato de QA tem retenção de dois dias e não contém originais.

O workflow roda as verificações baratas em commits usuais. O download e extração completos só serão executados em commit explicitamente marcado `[stock-frame-qa]` ou disparo manual, evitando repetir consumo de CPU, rede e minutos de Actions em cada ajuste editorial. A validação computacional não reconhece confiavelmente logotipos, identidades, texto embutido, contexto bíblico ou direitos. A leitura de quadros por um revisor e a conferência de termos continuam necessárias. Não promover a `READY_FOR_PUBLICATION_AUTHORIZATION` com essa auditoria.
## Resultado editorial do contato real de 12 frames

**Fontes da decisão:** arquivo `contracts/e01_v2_stock_editorial_review_v1.json`, prova visual SHA-256 `54e3f9b9ba891565b1fae13146cda41804c68269b564551b574abcd709bb367b`, run https://github.com/BORELLITO/corte-fino-engine/actions/runs/44222503550. Três fotogramas por clipe, nas posições de 15%, 50% e 85%; **não representa assistir aos vídeos inteiros**. Prova de sincronismo de legenda e direitos continua bloqueada.

| Cena | Decisão | Motivo |
|---|---|---|
| S03 | REJECTED_HARMONY | Rua chuvosa mostra atividade urbana comum, sem comunicar a injustiça da frase; gera preenchimento visual sem função |
| S05 | CONDITIONAL_METAPHOR | Corredor escuro e quente combina com a tensão, desde que seja tratado apenas como metáfora, não arquitetura bíblica factual |
| S08 | REJECTED_HARMONY | Close-up inclui rosto/óculos de ator diferente, contradiz o protagonista anônimo estabelecido |
| S09 | REJECTED_HARMONY | Escrita em escritório iluminado com laptop/pessoa exposta destoa de quarto íntimo escuro |

Apenas S05 continua como **candidato condicional, ainda não habilitado para master**. Portanto nenhum dos quatro está liberado para montagem definitiva. O validador `agents/e01_stock_editorial_decision.py` impede reintrodução acidental dos três rejeitados ou falsa promoção do condicional.

### Substituições em pesquisa (não baixadas, não aprovadas)

- S03: buscar sinais de tensão humana e abandono sem estereotipar pobreza; monitorar `https://www.pexels.com/video/park-bench-reflection-after-rainfall-34479513/` como alternativa simbólica (4K vertical), mas só após assistir e provar adequação.
- S08: preferir **mãos anônimas** em quarto escuro, sem rosto, rosário ou outras identidades religiosas; a pesquisa por oração tende a retornar figuras não compatíveis, portanto não forçar imagens.
- S09: candidato `https://www.pexels.com/video/hand-writing-near-wax-candle-13017069/` com luz de vela e mão em escrita (4K vertical) precisa de QA físico e verificação de texto/escultura identificável. Alternativa `https://www.pexels.com/video/close-up-view-of-a-man-writing-on-a-notebook-6037432/` é quase vertical, requer crop e QA.

Esses links são somente **referências pesquisadas**, sem downloads ou hashes, e não participam do catálogo de mídia aprovado. Não criar novos direitos por suposição.
