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
