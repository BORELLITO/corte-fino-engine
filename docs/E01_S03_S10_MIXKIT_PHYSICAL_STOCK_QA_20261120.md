# E01 S03 + S10 — lote real Mixkit / 20-11-2026

**Escopo isolado:** projeto VERBO_NO_CHAO_EXCLUSIVO; duas filmagens reais baixadas por HTTPS Mixkit sem credenciais, custo adicional R$0. Este QA não altera master, storyboard, roteiro, narração, S01 ou qualquer canal.

## Prova física

[GitHub Actions #44720731370](https://github.com/BORELLITO/verbo-no-chao-engine/actions/runs/44720731370) rodou um workflow one-shot com gatilho de adição única de arquivo, token somente leitura. **SUCCESS.** Imagens e JSON verificados depois por inspeção local de SHA e full decode FFmpeg.

**S03** — [Mixkit #4331, Traffic on a rainy night](https://mixkit.co/free-stock-video/traffic-on-a-rainy-night-4331/): arquivo original 1920×1080, H264 30fps, 14,9s, 51.846.621 bytes, SHA `d5975aa71a2616ac4d9c70f671c192ea9b26d3b95eff190578fa392770e02a05`. Prévia vertical real 540×960, 30fps, 184 quadros, 6,133333s, 1.263.440 bytes, SHA `8432d73bcda04aec85bf59eba867248822fbe47b27ab85e3a1bbd20c78c95cca`. Folha 3 frames SHA `e2c719da0d09cb295c49ef54f0845dbc31849147edd0c7391513b4ceeb932363`. Chuva refletida no asfalto com veículos em movimento — **bom motivo visual noturno**, mas não retrata literalmente a violência/injustiça do texto de Habacuque. **CANDIDATA NÃO APROVADA.**

**S10** — [Mixkit #8748, Sad and crestfallen young man is comforted by his girlfriend](https://mixkit.co/free-stock-video/sad-and-crestfallen-young-man-is-comforted-by-his-girlfriend-8748/): origem 3840×2160, H264 24fps, 15s, 72.219.292 bytes, SHA `c10db2c1c62de875b1a2b1721d1ac5bc8c5c93d8f33050224f34dbde11035a04`. Prévia vertical real 540×960, 30fps, 198 quadros, 6,6s, 260.405 bytes, SHA `84d6f4b6f28348de128ca35fc514ab6bacd2ac983f7958e80a7436b4495a0a29`. Folha 3 frames SHA `0a20de4620f4f0ef53b897b03c83fc50c3c7dca4776dbd7ba845bad0ec18ac3e`. **REPROVADA no enquadramento central 9:16:** a pessoa que oferece apoio não aparece nos quadros e não é possível representar com essa prévia um gesto entre duas pessoas; fundo de cozinha claro destoa do cenário modesto projetado. A origem pode ser reavaliada em crop diferente após evidência, mas não afirmar que S10 está pronta.

Ambos os MP4s de QA têm marca d'água técnica e **sem voz, trilha, legenda, direitos individuais aprovados ou permissão de publicação**. A licença exibida em ambas as páginas é Mixkit Stock Video Free License; verificar eventuais direitos de imagem/marcas antes de distribuir. A origem de câmera humana não foi comprovada independentemente. Os arquivos originais grandes foram apagados no runner temporário; a fonte completa não teve full decode, somente as prévias curtas.

## Arquivos privados e integração

`/VERBO_NO_CHAO/E01_MULTIBANK_MIXKIT_QA_20261120/S03_S10_BATCH/` preserva 2 MP4s, duas folhas de 3 frames e relatório JSON. Os SHA estão travados em `contracts/e01_mixkit_s03_s10_physical_scene_assessment_20261120_v1.json`.

O workflow e script de duas fontes são limitados aos IDs 4331 e 8748, HTTPS `assets.mixkit.co` URLs exatas, 155 MB por arquivo, 2 previews curtas e provas reais. Travas: sem autorização de merge, sem master, sem gravação no repositório dos MP4s originais e sem gastos.

**Regressão detectada e corrigida:** o teste adversarial usava um contrato de caminho absoluto e podia escrever no checkout temporário de CI; corrigido para `CONTRACT` relativo com raiz temporária para testes, revalidando o Engine Gates antes de habilitar o download. Nenhuma alteração ao contrato remoto canônico foi feita por esse teste.

**Próximo passo:** priorizar S03 com narração/legenda real em QA de continuidade; S10 exige reenquadrar a fonte ou trocar tomada. A S02 permanece pendente, sem obrigar o projeto a parar nela.
