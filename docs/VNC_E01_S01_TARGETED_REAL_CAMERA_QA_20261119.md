# VERBO NO CHÃO — E01 S01 | busca direcionada de vídeo real (19/11/2026)

## Decisão editorial que orienta a busca
A S01 aprovada do episódio baseado em Habacuque 1:2–4 tem 5,74s e exige **um único adulto anônimo de costas, casaco grafite, interior modesto à noite, janela com chuva visível, caderno FECHADO na mesa, movimento real e luz âmbar**. O contrato `contracts/e01_v2_12_scene_visual_plan_v1.json` continua canônico. Nenhum stock conhecido foi aprovado para S01; NÃO mudar o roteiro para encaixar mídia barata.

## Candidatos novos (pesquisa pública)
| Página oficial Pexels | Autor registrado na página | Duração e formato publicados | Risco editorial |
|---|---|---|---|
| https://www.pexels.com/video/a-man-sitting-in-a-dark-room-with-a-lamp-16835716/ | khanhhoangminh | 13s, 1920×1080, 24fps | homem lendo, provavelmente livro aberto, chuva/caderno não confirmados |
| https://www.pexels.com/video/silhouette-of-man-working-in-a-dimly-lit-study-32788087/ | Salih Sezgen | 16s, 3840×2160, 30fps | ambiente de estudo, possível composição artificial/gráfica, sem chuva confirmada |
| https://www.pexels.com/video/a-man-having-problems-6944291/ | cottonbro studio | 27s, 4096×2160, 25fps | clima emocional próximo, mas pessoa pode estar frontal e não há caderno/chuva |

Duração, resolução, autor e licença publicados NÃO comprovam que o arquivo real corresponde editorialmente. Ver https://www.pexels.com/license/ para licença Pexels, que permite uso em redes sociais e edição, porém proíbe retratar pessoa identificável negativamente ou insinuar endosso. Em narração sobre sofrimento/injustiça, o risco de associação indevida deve ser verificado de modo conservador.

## Execução física controlada
- Branch isolada `verbo-no-chao/e01-s01-stock-semantic-qa-20261119-v1`, derivada da branch principal operacional do VNC. Não misturar com PR #53 Agnes nem PR #54 LTX.
- Workflow único `.github/workflows/verbo-no-chao-e01-s01-stock-semantic-once.yml`, sem agenda, sem `workflow_dispatch`, sem credenciais, sem despesas. A infraestrutura utiliza o FFmpeg portátil que o projeto já havia validado.
- Programa `agents/e01_s01_stock_semantic_probe.py`: baixa somente IDs fixados via redirecionamento Pexels → `videos.pexels.com` com bloqueio de hosts não permitidos e limite 160 MiB por arquivo; verifica container, áudio opcional, FPS/duração, SHA256, decodifica completamente, mede variação temporal. Mantém arquivos originais somente no armazenamento temporário do runner e os remove.
- Extrai três momentos (15%, 50%, 85%) do enquadramento integral e três cortes verticais (ESQUERDA/CENTRO/DIREITA) para mostrar a perda de contexto no 9:16. Artefato de imagens e relatório técnico por 1 dia apenas, sem MP4 bruto.
- Se algum host, download, codec ou captura falhar, a filmagem continua `BLOCKED_PHYSICAL_QA`; se passar, vira apenas `PHYSICAL_VIDEO_VERIFIED_EDITORIAL_REVIEW_PENDING`. Nenhum script promove direitos, autoriza publicação ou copia essa mídia para master.

## Resultado esperado e limites
Comparar visualmente as seis amostras de cada fonte para decidir se merece assistir integralmente ao clipe. Se um ator real estiver frontal, o caderno estiver aberto ou a chuva inexistir, rejeitar S01 em vez de inventar esses elementos por edição não autorizada. Uma cena compatível ainda exigirá avaliação do vídeo inteiro, verificação dos direitos das pessoas e posterior montagem em contexto.

**Estado até avaliação do artifact:** `NO_S01_VIDEO_APPROVED`. Sem master, sem publicação, sem alterações dos hashes do roteiro, WAV, 28 legendas, contrato do storyboard ou PRs existentes.
