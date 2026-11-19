# VERBO NO CHÃO — E01 | curadoria stock multifonte, sem geração de vídeo

**Data:** 2026-11-19. **Estado editorial:** PÁGINAS CONFIRMADAS, fontes físicas e direitos individuais só após QA. **Nenhum master aprovado nem publicado.**

## Motivo da mudança
A abordagem antiga exigia 8 cenas ROOM_A com a mesma pessoa, roupa, quarto, caderno e chuva — praticamente impossível com stock independente. Esta branch propõe **montagem cinematográfica simbólica**, não continuidade literal de ator. O texto, duração 70,425s, locução SHA256 `4f2ee1ff0171ddedb7c64e0dce2300c53a0ef105ef12d643a7af6b0a4621942e`, 28 legendas e as 12 janelas de timecode **não são modificados**. Isso é uma direção visual experimental, não uma aprovação retroativa do storyboard original.

## Fontes de vídeos prontas encontradas, por trecho
| Cena | Faixa | Fonte primária candidata | Por que funciona | Risco / QA |
|---|---:|---|---|---|
| S01 — pergunta sem resposta | 0–5,74s | [Pexels 32788087](https://www.pexels.com/video/silhouette-of-man-working-in-a-dimly-lit-study-32788087/); [Pexels 4458845](https://www.pexels.com/video/rainy-nights-4458845/); [Pexels 6376122](https://www.pexels.com/video/a-white-notebook-on-the-table-6376122/) | 3 planos verdadeiros: pessoa de costas, chuva, caderno fechado | autores/salas diferentes; caderno branco e não preto; verificar crop e dramaturgia |
| S02 — dor da espera | 5,74–10,62s | [Pexels 36448548](https://www.pexels.com/video/vintage-alarm-clock-on-wooden-desk-36448548/) | relógio em mesa iluminada quente | verificar movimento do ponteiro e corte 9:16 |
| S03 — violência e injustiça | 10,62–16,76s | [Pexels 9943158](https://www.pexels.com/video/a-back-view-of-a-person-walking-in-the-dark-9943158/) | figura anônima solitária em ambiente sombrio | solidão não é injustiça; não apresentar como evidência de evento real |
| S04 — contexto de Habacuque | 16,76–22,58s | [Pexels 11530045](https://www.pexels.com/video/a-person-flipping-pages-of-an-old-book-11530045/) | velas e manuscrito/livro antigo, luz baixa | metáfora, não reconstituição histórica real; escrita legível |
| S05 — lei perdeu a força | 22,58–30,2s | [Pexels 36893300](https://www.pexels.com/video/man-walking-in-historical-arched-corridor-36893300/) | figura em corredor de pedra | não afirmar ser Judeia antiga; crop |
| S06 — nenhuma resposta fácil | 30,2–36s | [Pexels 6376122](https://www.pexels.com/video/a-white-notebook-on-the-table-6376122/) | objeto fechado e intervalo contemplativo | eventual repetição de S01, baixa ação, cor incompatível |
| S07 — não normalizar o mal | 36–43,16s | [Pexels 6756336](https://www.pexels.com/video/a-man-standing-in-darkness-6756336/) | homem silhouetado à janela | não afirmar ser o ator de S01 |
| S08 — fé sem fingimento | 43,16–49,8s | [Pexels 9737896](https://www.pexels.com/video/close-up-of-hands-of-woman-praying-9737896/) | mãos em prece, rosto opcional fora da tela | avaliar associações religiosas e pessoas reconhecíveis |
| S09 — nomear o que está errado | 49,8–55,56s | [Mixkit 99890](https://mixkit.co/free-stock-video/close-up-a-hand-writing-notes-on-a-notebook-with-99890/) | 8s mãos escrevendo; **Mixkit Free License**, uso comercial | palavras legíveis e mudança de textura/temperatura |
| S10 — apoio responsável | 55,56–62,16s | [Pexels 8555708](https://www.pexels.com/video/a-person-comforting-someone-while-touching-back-8555708/) | mão no ombro = acolhimento real | consentimento/reconhecibilidade, não insinuar situação real |
| S11 — espera continua | 62,16–67,2s | [Mixkit 99841](https://mixkit.co/free-stock-video/colorful-rain-soaked-bokeh-lights-at-night-99841/) | chuva em janela **vertical 1080×1920**, 23s, Mixkit Free comercial | cores vívidas devem ser neutralizadas; pessoas ausentes |
| S12 — loop | 67,2–70,425s | [Pexels 7744309](https://www.pexels.com/video/a-person-opening-a-notebook-7744309/) | pessoa abre caderno visto de cima | não casar com o mesmo caderno da S01 sem QA; recorte exato de loop |

## Licenças verificadas no site original
- [Pexels License](https://www.pexels.com/legal-pages/license/) / [Pexels uso comercial](https://help.pexels.com/hc/pt/articles/360042295214-Posso-usar-as-fotos-e-os-v%C3%ADdeos-em-um-projeto-comercial): vídeos gratuitos e editáveis, porém **pessoas identificáveis não podem ser retratadas em má luz/ofensa**, não insinuar endosso de pessoas/marcas. O plano de vídeo sobre sofrimento deve preferir silhuetas/mãos e não implicar participação dos atores em evento negativo.
- [Mixkit Stock Video Free License](https://mixkit.co/license/modal/videoFree/): uso comercial permitido em videoclipes Free; versões rotuladas **Restricted License** são apenas uso pessoal e foram excluídas desta lista.
- [Pixabay Content License](https://pixabay.com/service/license-summary/): é alternativa futura, conteúdo gratuito com direitos e marcas a verificar por item. Muitas cenas novas são rotuladas IA-gerada; a seleção prioriza cenas reais.
- Nunca assumir que Pexels, Mixkit e Pixabay cobrem terceiros, marcas, faces, música extra, contexto histórico ou direitos de voz.

## Prova prática S01 nesta branch
- **V1** https://github.com/BORELLITO/verbo-no-chao-engine/actions/runs/44614902739: renderização real 5,767s / 720×1280 / 30 fps e SHA256 `3653dd73575446533b1f47512b3c236b9184bba150fec5116c5526ba0ee1013e`; **REJEIÇÃO ESTÉTICA** por texto/decorativo na parede e corte de caderno branco claro que rompe a harmonia.
- **V2** https://github.com/BORELLITO/verbo-no-chao-engine/actions/runs/44615672379: substituiu os dois cortes incompatíveis por uma silhueta real à janela + chuva noturna, total 5,767s / 720×1280 / 30 fps, SHA256 `2c099db52b219cb901977d98fac29f91579a4be1d9a2126f4ff6ba0cbcc7c1e5`. **REPROVADO PARA MASTER**: o frame da silhueta tem janela clara/diurna, diferente da chuva escura; caderno fechado não está presente na S01; sem aprovação de visual, direitos ou sincronismo com WAV.
- ZIP com V2, vídeo real e relatório físico foi armazenado no Drive privado de quarentena (verificado por metadata): https://drive.google.com/file/d/1TN1u7c8HEc6KvcXWHCi9YDeWIELFNNsM/view
- Ambos os vídeos são **evidência executável de ingestão e montagem automática de stock**, não solução cinematográfica completa. A seleção artística continua sendo o gargalo a resolver por revisão dos planos, sem impor personagem único ou gastar créditos em IA.

- `agents/e01_s01_multi_stock_pilot_v1.py` baixa no runner dois Pexels oficiais em diretório temporário, testa origem e FFprobe, renderiza 2 cortes 720×1280 / 30fps total de 173 frames (5,767s) e decodifica integralmente, com SHA256 e relatório. **Não é MASTER nem aprovação estética**.
- Workflow de execução física único `.github/workflows/verbo-no-chao-e01-s01-multi-stock-real-pilot.yml`; artifact temporário (24h) pode ser transferido via connector para **pasta privada já criada** `1M0eQCkN8srETZeMvZ2miPqDdxAfk5pdY` sem login manual.
- Não registrar MP4s crus no repositório. Não ativar publicação. Não alterar a branch operacional aprovada sem aprovação do usuário do novo estilo.

## Critério de aceitação
1. Somente clipes reais, licenciados, movimento físico, sem IA gen nem falsa construção de personagens.
2. Enquadramento 9:16 legível em celular, margens das 28 legendas preservadas.
3. Coerência emocional do texto; vários planos curtos podem ser melhores que uma única cena artificialmente impossível.
4. Evitar repetição de imagem, rostos identificáveis e voz/trilha de terceiros.
5. Vídeo final real 1080×1920, áudio e legendas sincronizados, loop testado, direitos e revisão de publicação **separados**.
