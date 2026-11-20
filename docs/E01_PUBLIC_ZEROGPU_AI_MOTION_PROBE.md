# Experimental no-login cinematic moving-video probe — 2026-11-18

This workflow checks **whether an actual AI video can be generated automatically with no website interaction by the user**. It uses a public Hugging Face ZeroGPU Gradio Space implementing the **Wan2.2 TI2V-5B** model (Apache-2.0), only a generic fictional faceless character prompt. It sends no real user data, production voice, source images, private Drive files or credentials.

The GH Actions runner calls the Space's `/generate_video` Gradio endpoint once with dimensions 576×1024, 25 frames, 20 inference steps; validates returned bytes using SHA-256, FFprobe and full FFmpeg decoding. Artifacts expire after one day and are not committed to Git. The test lasts only about one second — far shorter than S01's 5.74 seconds — and **must not replace the E01 actual master or bypass the release gates**.

References:
- https://huggingface.co/spaces/OpenKing/wan2-video-generation/blob/main/app.py (endpoint, 3-min ZeroGPU limit and parameters)
- https://huggingface.co/Wan-AI/Wan2.2-TI2V-5B (model license Apache-2.0)
- https://huggingface.co/blog/Jacob123222/image-to-video-huggingface (Nov 11 2026, anonymous Gradio proof, failures due to quota/replicas)
- https://github.com/BORELLITO/corte-fino-engine/pull/41 (isolated draft PR)

Expect external constraints: anonymous ZeroGPU quota, shared queue, runtime reliability, and Gradio client compatibility. A failed action means **unavailable now**, not a failure of the existing E01 motor. Do not automatically resubmit, spend money, or replace source assets. A successful action proves only a short AI clip; it does not validate scene continuity, legibility, rights of third parties, commercial use or 1080x1920 native master.

**State before CI:** configured, unexecuted. **No generation and no money spent yet**.

## Resultado físico do experimento — 18/11/2026

- Workflow executado: https://github.com/BORELLITO/corte-fino-engine/actions/runs/44279375769
- Status: **FAILURE**, etapa de geração saiu com **código 124 (timeout externo)** depois de 500 segundos.
- O teste escreveu apenas `TEST_IN_PROGRESS` na evidência inicial. Não houve retorno de arquivo MP4, SHA de mídia ou decodificação FFmpeg; logo, **0 clipes gerados/comprovados**.
- Artifact temporário #14416114304 contém apenas relatório inicial `technical_proof.json`, não contém vídeo.
- O CI principal não foi alterado pela falha do provedor externo; a integração continua experimental e isolada.
- Não considerar o Wan ZeroGPU público como motor recorrente de vídeos ou contorno confiável a login de serviços comerciais.
- Não repetir automaticamente o trabalho caro de 500 segundos sem mudança fundamentada de endpoint/contrato.
- Google Flow exige sessão Google válida; Higgsfield exige plano Basic nos modelos testados; Creative Claw pede aprovação manual e saldo. **Nenhuma ferramenta conectada demonstrou geração cinematográfica repetível com custo financeiro zero e zero intervenção no estado atual.**
