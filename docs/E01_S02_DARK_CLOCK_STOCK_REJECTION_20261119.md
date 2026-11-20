# E01 S02 — filmagem 4K alternativa avaliada e REJEITADA para esta cena

**Data de decisão:** 19/11/2026 · **Canal exclusivo:** VERBO NO CHÃO · **Aprovação preservada:** S01 chuva noturna · **S02:** ainda sem aprovação humana.

## Por que buscar outra fonte?

A S02 V1/Pexels #7034348 e sua `GRADE A` produziram uma transição mais coesa com a S01, mas o mostrador branco grande e o texto visível "QUARTZ" podem competir com as legendas. A luz/tonalidade melhorou, mas aprovação estética da cena não foi concedida. Antes de tratar o problema com mais filtros, buscamos alternativa **real em movimento** e gratuita.

A página [Pexels #29862379 — Sini Ko, Dramatic Clock Ticking in Dark Room](https://www.pexels.com/video/dramatic-clock-ticking-in-dark-room-29862379/) anuncia **3840×2160, 50 FPS, ~11 segundos**, classificada como grátis. Diferentemente de 1920×1080, o 4K horizontal suporta **recorte central nativo vertical de 1214×2160** sem upscale da altura final 1080×1920. Isso é resolução suficiente em tese, mas NÃO aprova o posicionamento do objeto nem comprova captura por câmera.

## Prova física

- [Run 44660021135](https://github.com/BORELLITO/verbo-no-chao-engine/actions/runs/44660021135): **SUCCESS** no teste com download real, contrato fechado e inspeção FFmpeg.
- MP4 original: **57.975.096 bytes**, 3840×2160, **11,74 segundos**, H.264; SHA `a6058b295f21cbfa5381d6a19263a1ed5606dcfb87a6579ae0aa4611e5130052`; decodificação integral FFmpeg PASS. Original eliminado no fim do runner.
- Prévia de revisão: **720×1280, 147 quadros, 30 fps, 4,9s**, 236.453 bytes, sem áudio, com watermark; SHA `3bb1c6efced29fbd5d48b235aec69af20d7e5c7bebf0b03fc8d09488d020ae94`. Revalidação independente de SHA, FFprobe, vídeo sem áudio e decodificação completa: PASS. ZIP de artefatos: teste de integridade PASS.
- 3 fotogramas reais: 0,5 / 2,4 / 4,5 s, luminância média **7,12 / 10,07 / 39,03**; diferenças médias **3,25 e 28,99**. O salto de diferenças decorre sobretudo de luz/exposição, não prova isoladamente movimento dos ponteiros. JPEG SHA `09b71d78c6d4a42dc95138bb4f99daad10ebef91c82b9e38951123f720fbfe43`.
- **Rejeição editorial específica:** às 0,5s o relógio quase não aparece; aos 4,5s o mostrador branco e a carcaça vermelha brilham sobre fundo esverdeado. Isso contraria a noite azul-preta sutil da S01 e não resolve a concorrência do mostrador com as legendas. Não declarar que o produto nunca serve para outra cena. Não fingir que metadata Pexels prova origem de câmera.
- **Estado formal:** `REJECTED_FOR_S02_EDITORIAL` em `contracts/e01_s02_dark_clock_29862379_editorial_decision_20261119_v1.json`, com provas, hashes e riscos. **Nunca promover este candidato automaticamente à cena S02**.

## Revisão paralela da S02 GRADE A existente

Foi criada uma **folha de auditoria com nove frames reais** cobrindo aproximadamente todo o clipe: 0,05 / 0,65 / 1,25 / 1,85 / 2,45 / 3,05 / 3,65 / 4,25 / 4,80 segundos. O vídeo exibe ponteiros em movimento, e o texto `QUARTZ` permanece legível sobre o mostrador; seu diâmetro grande atravessa parte da zona inferior de legendas. Não afirmar que `QUARTZ` identifica por si só um problema jurídico: é uma indicação genérica de movimento de relógio, mas **pode prejudicar a elegância da composição**. A questão de legibilidade só se resolve com prévia das legendas reais e auditoria editorial do corte.

JPEG de nove quadros, SHA `a589e5c417840ba9db31e665adf1a7c23ab6142b5dfde9db7108234563cf2b8c`. **S02 GRADE A segue candidata, sem aprovação do usuário.**

## Direitos — fonte primária

A [licença do Pexels](https://www.pexels.com/license/) afirma que o uso e edição de fotos/vídeos são gratuitos e não exige atribuição, mas proíbe, entre outros usos, sugerir endosso por pessoas ou marcas na imagem. Essa licença geral **não é certificado individual de titularidade ou ausência de direitos de terceiros**. Nenhum clipe recebeu liberação final.

## Evidências preservadas em Biblioteca pessoal

```text
/VERBO_NO_CHAO/E01_STOCK_QA_20261119/S02_DARK_CLOCK_ALTERNATIVE_REJECTED/
  S02_29862379_PREVIEW_REJEITADA.mp4
  S02_29862379_FRAMES_REJEITADOS.jpg
  S02_29862379_PROVA_FISICA.json

/VERBO_NO_CHAO/E01_STOCK_QA_20261119/S02_WAITING_CLOCK_REVIEW/
  S02_GRADE_A_9_FRAMES_AUDITORIA.jpg
```

**Conclusão:** melhora técnica de fonte (4K crop sem upscale) não bastou para a direção cinematográfica. S01 permanece aprovada; S02 permanece pendente; nenhuma alteração em roteiro, narração, 28 legendas, branch operacional, master, direitos ou publicação.

**Próxima prioridade:** criar uma **prévia S01/S02 com as legendas reais em sua zona de segurança** para verificar leitura sobre o relógio graduado, ou buscar outra tomada original com tempo/espera e área inferior livre; não continuar escurecendo indefinidamente a mesma imagem. Sem autorização de merge/postagem/gastos.
