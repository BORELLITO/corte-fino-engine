# Regras de trabalho permanentes — VERBO NO CHÃO (v1, 20/11/2026)

Definidas pelo dono do projeto. Valem para todo episódio e toda etapa. Fonte versionada: `contracts/vnc_working_rules_v1.json`; verificação: `tests/test_vnc_working_rules.py`.

## R1 — Exemplo palpável em toda entrega
O usuário aprova vendo. Toda entrega traz imagem, vídeo curto ou prova renderizada do resultado.
- Os exemplos ficam em `previews/<episódio>/` e são listados em `contracts/<episódio>_preview_manifest_v1.json` com bytes e sha256.
- O repositório é público: prévias não podem conter áudio da voz nem clipes de terceiros. Usar fundo neutro e marcar "PRÉVIA TÉCNICA / NÃO É CLIPE".
- A prévia não é aprovação. `approved_by_user` só vira `true` por decisão do usuário.

## R2 — Revisar e refinar todos os clipes
A cada mudança de voz, tempo ou legenda, todos os clipes são reavaliados (`agents/e01_v3_clip_review.py`):
- duração do clipe cobre a cena mais 1,0 s de folga;
- ação principal fora da faixa protegida da legenda (`contracts/e01_v3_caption_band_v1.json`);
- cenas de 8 s ou mais exigem segundo plano real ou movimento justificado;
- rejeição posterior supera candidato anterior do mesmo arquivo (mesmo sha256);
- cena sem clipe viável é declarada `NO_VIABLE_CLIP_ACQUISITION_NEEDED`;
- nada é aprovado sem revisão de quadros reais, direitos e decisão do usuário.
