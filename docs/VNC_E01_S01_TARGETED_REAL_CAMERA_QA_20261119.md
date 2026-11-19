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

## Resultado físico e editorial verificado (19/11/2026)
- GitHub Actions: https://github.com/BORELLITO/verbo-no-chao-engine/actions/runs/44592239132 — **SUCCESS** depois de corrigir a ausência inicial de FFmpeg no runner e usar `portable-ffmpeg==0.5.0`.
- Artifact de QA: ID `14563604068`, 3 folhas JPEG + JSON, retenção temporária de um dia. **Nenhum MP4 bruto nem credencial foi publicado**.
- Arquivos reais: **3/3 baixados, SHA256 calculados e decodificação integral por FFmpeg concluída**. Durações 13,93s; 16,30s; 26,76s; amostragem visual de 18 imagens no total. Isso comprova a integridade técnica, **não** o uso editorial.
- Pexels **16835716**, SHA256 `5052434451984e22fc4c098f73d9a1eb902a9830cf35403aa39918e56f45d2e4`: quadro visual mostra pessoa frontal lendo (livro aberto), em janela vista do exterior, movimento temporal muito limitado (diferença média de luminância 0,518). **REJEITADO S01**.
- Pexels **32788087**, SHA256 `1d2b0773699ad984730d7c1d4ff0930cebea136bfd6aefc062da8f664117c767`: silhueta de adulto de costas em roupa escura, mesa e luminária, movimento real (diferença média 4,362). Composição próxima da proposta, porém **sem janela com chuva visível e sem caderno fechado comprovado**. **APENAS REFERÊNCIA DE ESTILO; NÃO LIBERAR COMO S01**.
- Pexels **6944291**, SHA256 `206a172759ff982dd80b75ac43da2c0e25d2f3c9c89e8707e29479073f75718a`: ator frontal/de perfil com camiseta clara em iluminação amarela; sem mesa com caderno/janela/chuva (diferença de luminância 5,045). **REJEITADO S01**.
- Decisão formal, vinculada a hashes e frames: `contracts/e01_s01_stock_nov19_editorial_v1.json`. Guardião `agents/e01_s01_stock_nov19_editorial_gate.py` impede que fonte rejeitada seja declarada aprovada. Testes adversariais cobrem tentativas de promover asset, direitos e publicação.
- **Não houve assistência audiovisual à edição final nem master**. Nenhuma chamada paga, nenhuma geração adicional Agnes/LTX/Higgsfield, nenhum merge; os três MP4 temporários foram removidos.

### Próximo passo viável
A falha recorrente é a **composição completa do plano** e não a resolução nem o codec. Exigir uma única filmagem original da sala com chuva e caderno fechado ou uma geração IA com vídeo completo, elegibilidade gratuita e direitos confirmados antes de desbloquear S01. Não substituir por zoom de imagem, montagem de stock incompatível ou geração em serviços que exigem plano pago.
