# E01 S02 — relógio como metáfora da espera: prova física SEM aprovação editorial

**Data:** 19/11/2026 · **Projeto:** VERBO_NO_CHAO_EXCLUSIVO · **Versão candidata:** S02 V1.

## Decisão de S01 previamente registrada

O usuário disse **“Aprovado”** sobre a prévia concreta S01 Pexels #31069867, chuva noturna no vidro. O registro isolado `contracts/e01_s01_owner_visual_approval_20261119_v1.json` aprova **exclusivamente o visual da S01** de SHA `724ae91368af7d843f39195b34f77db50341aa7f92b0e5960a17061e9da3f961`. Master, licenças de terceiros, áudio/legendas e postagem continuam bloqueados. Não inventar aprovação das outras cenas.

## Nova S02 — “A dor da espera”, 5,74–10,62 s

**Proposta editorial ainda pendente:** passar de chuva noturna no vidro (S01) para um plano macro de relógio analógico real, sobre fundo escuro. Isso preserva a metáfora do tempo parado/espera sem falsificar continuidade de personagem/ambiente. O plano original mostrava uma mão repousando na mesa perto de um relógio; a ausência da mão é uma mudança S02 **ainda não aprovada**.

**Fonte:** [Pexels #7034348, Tima Miroshnichenko — Clock is Ticking](https://www.pexels.com/video/clock-is-ticking-7034348/). Página oferece licença geral `Free` e declara 1080×1920, 20 s, 25 fps. A amostra física foi obtida pelo safe downloader existente.

**Prova física:**
- Original MP4 H.264, 1080×1920, 20,2 segundos, **6.202.873 bytes**, SHA-256 `6a8f877c0e57a1397f4eb96ffc9a86d25e173019fb298ec0a6945b73973f2a40`, full decode FFmpeg **PASS**.
- Prévia marcada `PREVIA DE QA - NAO PUBLICAR`, sem áudio/legendas, 720×1280, 147 quadros, 30 fps, **4,9 s**, **203.410 bytes**, SHA-256 `31d9500f8d5d321d14f6da9b6c65c1a96eb230354c62f03ece51abf955813786`. Hash, FFprobe e decodificação completa repetidos localmente **PASS**.
- Três frames reais 0,5 / 2,4 / 4,5 s, diferença média 24,84 e 25,69 (relógio e/ou câmera apresentam movimento verdadeiro). Folha de contato JPEG SHA `28a0284ab8106274a60b937921f309572746c66ac44e3e342362b1712ad854b2`.
- [GitHub Actions 44644297546](https://github.com/BORELLITO/verbo-no-chao-engine/actions/runs/44644297546) **SUCCESS** no pipeline de revisão, que não publica, não faz merge nem arquiva o MP4 bruto.

**Ponto estético:** fundo preto harmoniza com as sombras da S01, mas o mostrador grande **branco** e os numerais nítidos podem quebrar a atmosfera azul noturna. Os três frames comprovam movimento; **não representam aprovação humana de toda a sequência**. S02 permanece em `PREVIEW_CANDIDATE_HUMAN_AESTHETIC_APPROVAL_PENDING`.

**Importante para sincronização:** S01 do roteiro termina nominalmente em 5,74 s e S02 em 10,62 s. Em 30 fps, os limites corretos de frame mais próximos são **172** e **319**; portanto a master deve usar 172 frames S01 e 147 frames S02, sem reutilizar cegamente os 173 frames da prévia aprovada de S01. As prévias são artefatos separados e não equivalem a uma master final.

## Evidência privada e próximos gates

Arquivos preservados na Biblioteca privada do ChatGPT em:
`/VERBO_NO_CHAO/E01_STOCK_QA_20261119/S02_WAITING_CLOCK_REVIEW/`

- `S02_7034348_PREVIA_NAO_APROVADA.mp4`
- `S02_7034348_FOTOGRAMAS_QA.jpg`
- `S02_7034348_RELATORIO_FISICO.json`

A fonte bruta não foi persistida em repositório ou Biblioteca. Contrato de pré-voo em `contracts/e01_s02_waiting_clock_stock_preflight_20261119_v1.json` e parecer em `contracts/e01_s02_waiting_clock_physical_visual_review_20261119_v1.json`.

**Próximo passo:** apresentar a prévia S02 junto à abertura S01, avaliar contraste/legibilidade e decidir estética. Somente então avançar para S03, sem assumir que aprovação da S01 vale para S02. Direitos individuais, master/áudio/legendas/publicação e merge continuam BLOQUEADOS.
