# VERBO NO CHÃO — E01 S01 | LTX Video Fast official ZeroGPU, one-shot real-motion proof

## Decisão
- Agnes 2.5 Flash: UMA tentativa autorizada, preço promocional validado, API recusou na admissão `provider_quota_or_queue_unavailable` (HTTP 429 ou 503), sem `video_id`, sem MP4; não repetir nem apagar lock Agnes.
- Rota alternativa: Space **oficial** `Lightricks/ltx-video-distilled` em Hugging Face ZeroGPU, fonte `https://huggingface.co/spaces/Lightricks/ltx-video-distilled/blob/main/app.py`, rotulado `Running on Zero` quando pesquisado.
- API Gradio oficial `/text_to_video`; 13 entradas estritamente fixadas, sem mídia externa, sem login, sem HF_TOKEN, sem pagamento, sem chamada a serviço pago.
- Diferente de LTX-2.3 (prova física anterior 2.04 s / reteste 5.8s sem cota), este LTX Video 13B v0.9.8 permite 0.3 a 8.5 s, 30fps. Pedido fixado em **6.0 s 512×896**, que, se devolvido completo, cobre S01 de 5.74s. Baixa resolução é apenas prova técnica/estética, nunca master 1080×1920.
- Fonte bibliográfica para capacidade técnica: `https://huggingface.co/Lightricks/LTX-Video-0.9.8-13B-distilled` e app.py acima.
- Licença do modelo: marca no cartão HF como `other`, aponta para licença específica Lightricks 13B 0.9.8. Uso comercial e distribuição do output dependem de revisão da licença e de eventuais direitos de terceiros. **Não afirmar aprovação comercial**.

## Execução isolada e segura
- Branch exclusiva `verbo-no-chao/e01-ltx-video-fast-free-proof-20261119-v1`, criada do operacional `verbo-no-chao/e01-stock-curation-gate-v1`; não modificar main, PR Agnes #53, contrato audiovisual aprovado, WAV, legendas nem direitos.
- Uma tentativa acionada exclusivamente por **adição do workflow** `.github/workflows/verbo-no-chao-e01-ltxfast-one-shot-20261119.yml`. Não existe `workflow_dispatch`, agendamento ou repetição.
- Antes da chamada Gradio, consulta read-only ao estado do Space e cria `operations/vnc_e01_s01_ltxfast_one_shot_20261119.json` via GitHub REST. Esse arquivo durável consome a tentativa antes do pedido. Em falha na criação do lock, **nenhuma geração**.
- Sem chaves API, sem envio de fotos do usuário, sem voz, sem dados pessoais ou contato com terceiros. O prompt é uma narrativa original fictícia, sem identificáveis.
- Se vier arquivo MP4: medições `ffprobe`, SHA256, duração mínima 5.74s, retrato 512×896, 23.8–30.2fps, codec H.264/HEVC e decodificação integral FFmpeg. `PASS` computacional **não** aprova conteúdo: chuva, caderno **fechado**, pessoa de costas, luz/noir, gesto real, continuidade e direitos dependem de análise visual.
- Um único artifact GitHub de prévia **não master**, 1 dia de retenção, contendo relatório e, somente se passar gates, MP4 fictício gerado. O repositório é público, logo não incluir mídia privada, real ou credencial. A prévia pode ser acessível a quem tiver acesso ao artifact; não tratar como publicação.
- Sempre que o provedor não devolver arquivo, falhar claramente `BLOCKED_NO_SCENE_MEDIA` (exit 2). Nenhum fallback pago, nenhum retry, nenhum vídeo sintético preenchendo o tempo.
- O lock e CI permanecem públicos, mas nenhum URL privado/sessão Gradio é registrado.
- Reconciliar qualquer suporte futuro da cena S01 sem ultrapassar 1 nova tentativa por autorização.
- Status até execução: somente código/teste/protocolo, **0 MP4 novo confirmado**.

## Gates de saída
- Cena precisa mostrar um único adulto anônimo de costas, casaco grafite, mesa simples, um caderno FECHADO e chuva realista na janela, **sem rosto**; corpo e câmera em movimento.
- A primeira S01 continua `TO_BE_CREATED_OR_LICENSED`, `approved_for_export=false`, `publication_authorized=false` no contrato canônico até bytes/inspeção e direitos comprovados.
- Mesmo se a prévia for boa, não publicar; S02/S06/S07/S08/S09/S11/S12 ainda precisam do mesmo ator/mundo.
