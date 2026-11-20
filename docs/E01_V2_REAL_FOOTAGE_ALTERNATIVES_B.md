# E01 v2 — lote B de alternativas reais (S03, S08, S09)

**Status inicial: RESEARCH / NÃO APROVADO.** Continuação da PR #41, sem alterar o E01 original nem retirar o veto ao lote A.

Foram confirmadas quatro páginas oficiais Pexels, cada uma com botão Free Download e metadados de origem e licença. Os destinos CDN foram obtidos do redirecionamento oficial `/download/video/<id>/`; isso não prova os bytes até o teste cloud. Não apresentar as cenas como já obtidas nem como prontas para uso comercial.

| Cena | Candidato | Página oficial | Metadados exibidos |
|---|---|---|---|
| S03-B | Banco de parque refletindo chuva; risco de metáfora genérica | https://www.pexels.com/video/park-bench-reflection-after-rainfall-34479513/ | David Saurik; 2160×3840, 26 s |
| S08-B | Mãos lendo Bíblia; não é gesto literal de oração e deve-se avaliar texto visível | https://www.pexels.com/video/person-reading-the-bible-6860448/ | Tima Miroshnichenko; 2160×3840, 14 s |
| S09-B | Escrita à luz de vela; escultura identificável no cenário | https://www.pexels.com/video/hand-writing-near-wax-candle-13017069/ | Eugenia Remark; 2160×3840, 17 s |
| S09-C | Escrita em close vertical, com risco de estética corporativa | https://www.pexels.com/video/close-up-of-hand-writing-in-notebook-at-desk-32421244/ | Jakub Zerdzicki; 1080×1920, 19 s |

## Plano técnico

O workflow `.github/workflows/verbo-no-chao-e01-alternatives.yml` faz download temporário com host e tamanho limitados, hash SHA-256, ffprobe e decodificação integral FFmpeg, extrai 15%, 50% e 85% e registra métricas e folha 4×3 (12 quadros) para inspeção editorial. A folha só é artefato QA de curta duração, não um arquivo de vídeo autorizado. Sem segredo, conta ou API paga. Os MP4s **não** são persistidos nem postados.

**Próximo critério de aceitação:** assistir/inspecionar os fotogramas reais, verificar texto/marcas/rostos e o sentido de Habacuque 1:2–4; rejeitar fotos genéricas mesmo que 4K; manter direitos pendentes e publicação bloqueada. Se todas as alternativas forem incoerentes, revisar a abordagem e priorizar regravação própria de mãos sem rostos ou imagens individuais em resolução nativa.
