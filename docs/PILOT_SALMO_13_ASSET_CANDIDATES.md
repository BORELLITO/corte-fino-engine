# Candidatos visuais — piloto Salmo 13

Estado: MASTER_PREVIEW_ASSEMBLED_PENDING_FINAL_RIGHTS_REVIEW
Data: 2026-11-17 (America/Sao_Paulo)

## Critério

O banco visual foi ampliado, baixado da biblioteca cloud e submetido a QA visual gratuito antes de qualquer montagem. A decisão prioriza coerência emocional, variedade suficiente, espaço seguro para legendas e ausência de repetição de clipe.

A regra de zero repetição é bloqueante: um mesmo asset não pode aparecer duas vezes no vídeo final, mesmo com crop, zoom, velocidade, espelhamento, reversão ou cor diferentes. Transformação não cria um novo clipe.

## Resultado do QA

- 12 assets persistidos na biblioteca cloud.
- 8 verticais nativos 9:16.
- 4 horizontais com reenquadramento controlado.
- Todos os 12 foram baixados por CDN, inspecionados com quadros de início/meio/fim e receberam SHA-256 local.
- S13-V09, S13-V10 e S13-V11 tiveram crop central 9:16 testado.
- Nenhum crédito Creative Claw foi consumido; a inspeção foi concluída por rota gratuita local.
- O lote foi montado no master de prévia; não é autorização de publicação.

## Seleção editorial

A seleção não força 10–12 planos quando isso criaria redundância. O núcleo aprovado contém 8 assets distintos, suficientes para um Short de aproximadamente 75 segundos com cortes respirados de 5–12 segundos. Reservas só entram se a montagem exigir uma função visual que não possa ser atendida sem repetir um asset.

| Asset | Função visual | Estado | Decisão |
|---|---|---|---|
| S13-V03 | abertura contemplativa; horizonte, neblina e raios de luz | PRIMARY | usar como entrada do arco |
| S13-V07 | interior de floresta com feixes de luz | PRIMARY | aprofundamento emocional |
| S13-V05 | água escura com reflexos quentes | PRIMARY | pausa/reflexão; detalhe com contraste |
| S13-V02 | paisagem rural aérea com luz de manhã | PRIMARY | transição para esperança |
| S13-V08 | árvore e campo banhados por luz | PRIMARY | expansão e calor |
| S13-V09 | clareira/caminho em neblina, crop 9:16 validado | PRIMARY | trecho de espera e vulnerabilidade |
| S13-V10 | caminho dourado sob árvore, crop 9:16 validado | PRIMARY | movimento em direção à conclusão |
| S13-V11 | estrada rural no campo, crop 9:16 validado | PRIMARY | fechamento visual de caminho |
| S13-V01 | amanhecer aéreo com estrada; próximo de V02/V03 | RESERVE | alternativa se a montagem precisar de uma variação de abertura |
| S13-V04 | amanhecer vertical com céu azul e construção ao fundo | RESERVE | usar somente se a transição azul for necessária; normalizar antes |
| S13-V06 | água cinza em textura próxima de V05 | RESERVE | alternativa técnica de água; não usar junto com V05 |
| S13-V12 | rua urbana azul no crepúsculo, contraste de paleta e contexto | REJECTED_HARMONY | não usar neste piloto |

## Regras de montagem

1. Cada plano final registra `asset_id`, página de origem e intervalo temporal usado.
2. O mesmo `asset_id` só pode aparecer uma vez no vídeo.
3. V05 e V06 são alternativas, não uma sequência.
4. V01, V02 e V03 são visualmente próximos; o montador deve evitar empilhar os três sem justificativa narrativa.
5. V09, V10 e V11 têm função de caminho distinta, mas não devem ser usados como três variações indiferenciadas.
6. O enquadramento 9:16 deve preservar área segura para legendas e não cortar o ponto focal.
7. Qualquer repetição, crop inadequado, logo, marca ou pessoa identificável bloqueia a montagem final.

## Próximo gate

- confirmar o roteiro/tempo de cada plano;
- gerar e validar narração comercialmente autorizada;
- revisar direitos de terceiros e logos nos quadros selecionados;
- normalizar V04 somente se ele for necessário;
- montar sem repetição e executar QA de áudio, legenda, safe area e elegibilidade para publicação.



## Uso efetivo no master

S13-V02, S13-V03, S13-V05, S13-V07, S13-V08, S13-V09, S13-V10 e S13-V11 aparecem uma única vez cada. O gate de repetição passou; o master usa 8 assets distintos e não usa S13-V12.