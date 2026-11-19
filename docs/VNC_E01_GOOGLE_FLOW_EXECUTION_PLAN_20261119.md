# VERBO NO CHÃO | E01 | Pipeline principal: Google Flow Veo 3.1 Lite (19/11/2026)

**Status real**: `PRODUCTION_INPUT_READY / USER_FLOW_AUTH_REQUIRED / ZERO_NEW_MP4`. Não transformar documentação, testes ou slots em aprovação de filmagem. Repositório público; vídeos candidatos ficam fora do GitHub.

## A decisão que encerra a caça de provedores
Os testes executados com Agnes, LTX, Hugging Face e Higgsfield mostraram que preços promocionais, modelos catalogados, sessões ZeroGPU e cota de créditos não bastam para garantir geração operacional em conta gratuita. A rota Pexels não entregou a composição aprovada (mesmo depois de QA dos MP4); não repetiremos esses testes sem nova evidência.

**Escolha única para produção:** [Google Flow](https://labs.google/fx/tools/flow) via **Veo 3.1 Lite**.

Validação oficial:
- [Créditos](https://support.google.com/flow/answer/16526234?hl=pt-br): 50 créditos/dia para contas sem assinatura, Veo 3.1 Lite 720p, 4/6/8 segundos por **10 créditos/geração**, preços podem mudar.
- [Recursos do Veo Lite](https://support.google.com/flow/answer/16352836?hl=pt-br): texto→vídeo, primeiro quadro→vídeo, primeiro e último→vídeo. Para elementos/referências diretamente, apenas 8s nesse modelo.
- [Países](https://support.google.com/flow/answer/16353544?hl=pt-BR): Brasil contemplado, mas condições individuais ainda precisam ser observadas na conta.
- [Ajuda de uso e download](https://support.google.com/flow/answer/16935308?hl=en): o usuário pode baixar MP4; há marca-d'água invisível SynthID que NÃO deve ser alterada.
- Horário de pico: Google pode impedir temporariamente gerações sem assinatura entre **14:00 e 17:00 UTC**. Sem contorno, VPN ou planos pagos. Créditos não acumulam.
- Não há **API gratuita oficial do Flow** conectada ao GitHub/ChatGPT nesta conversa. Nunca usar cookies, automação de login não autorizada, endpoint interno, cartão, trial com renovação ou afirmação de geração simulada.
- Usuário precisa **abrir Flow no próprio login Google** ou autorizá-lo a partir do navegador do modo Work, quando disponível; nada nesta branch realiza login ou usa créditos. Esse é o único bloqueio de interface de momento.

## Pasta de entrada no Drive
[**VNC E01 — FLOW | ENTRADA DE CLIPES (SEM PUBLICAÇÃO)**](https://drive.google.com/drive/folders/1M0eQCkN8srETZeMvZ2miPqDdxAfk5pdY) — criada sob a pasta já existente **VERBO NO CHÃO — PRÉVIAS EM QUARENTENA**. Compartilhamento não foi auditado; manter somente acesso pessoal e não criar links públicos.

## Plano de captação fechado em 50 créditos/dia
A linha de tempo, o WAV, o SHA do roteiro e as 28 legendas são canônicos em `contracts/e01_v2_12_scene_visual_plan_v1.json`; não adaptar narração para o que o gerador entregar.

| Rodada | S01..S12 previstos | Créditos |
|---|---|---:|
| 1 | S01 (6s), S02 (6s), S06 (6s), S07 (8s), S08 (8s) | 50 |
| 2 | S03 (8s), S04 (6s), S09 (6s), S11 (6s), S12 (4s) | 50 |
| 3 | S05 (8s), S10 (8s) | 20 |
| **Total mínimo sem refações** | **12 cenas** | **120 créditos em ≥3 ciclos de crédito** |

**Dependência absoluta:** gerar e **aprovar S01 antes** de gastar mais créditos nas cenas ROOM_A. Cronograma acima é apenas uma capacidade nominal e deve ser pausado se S01 falhar, houver troca de preço/plano, watermark incompatível, inconsistência ou negativa do produto.

### Continuidade do mundo ROOM_A
Oito cenas do mundo único: S01, S02, S06, S07, S08, S09, S11 e S12.
1. Criar a **S01 em texto→vídeo**, 6s, vertical 9:16, Veo 3.1 Lite, 720p. Usar prompt exato do manifesto.
2. Reassistir a S01 inteira. Exigir pessoa anônima de costas, **caderno FECHADO**, chuva em movimento no vidro, interior noturno modesto, luz âmbar, casaco grafite e movimento corporal/físico real. Não confundir *cinematografia bonita* com coerência.
3. Após a aprovação, capturar um frame real da S01 como **âncora visual**, não antes. Usar o Nano Banana 2 Lite dentro do Flow, se realmente disponível sem custo na conta, para elaborar **um primeiro frame específico por cena** conservando os mesmos figurino, objetos, pessoa, quarto e luz. Isso evita usar a wide shot como referência errada para um close de mão.
4. Gerar as cenas ROOM_A restantes via **primeiro frame→vídeo** com Veo 3.1 Lite. Separar tomadas de S03, S04, S05 e S10 com origem narrativa própria. Não usar rostos reconhecíveis e não caracterizar a simbologia antiga como reconstituição factual.
5. Fazer uma saída por vez, guardar como `VNC-E01-Snn-FLOW-CANDIDATE.mp4` na pasta Drive já criada. Não usar comando Publish to YouTube.

### Gate de ingestão que já existe
`python -m agents.e01_flow_free_daily_intake_gate --dir <PASTA_LOCAL_DE_MP4>` (execução local, requer `ffprobe` e `ffmpeg`; os unit tests não dependem deles). O motor emite relatório JSON com hash, FPS, resolução, duração adequada ao timecode, decodificação integral e aviso de quadros quase estáticos, sem aprovar cena por métricas.

A análise editorial deve confirmar também movimento real, coerência do mesmo ator e objetos, composição de legendas, integridade e direitos, som indesejado, SynthID/watermark visível e loop S12↔S01. O áudio master já aprovado é inserido **só após** as cenas estarem aprovadas. Nenhum arquivo de origem real deve ser commitado no repositório público. O fluxo de ingestão nesta etapa **não tem sincronização automática Google Flow→Drive**: a exportação depende da sessão autenticada do usuário. Não declarar automação E2E onde ela não existe.

### Critérios de saída para o piloto
- Existem 12 MP4 reais, cada um com bytes/hash físico e duração íntegra >= slot do storyboard.
- O editor aprovou coerência, atuação, composição, chuva/caderno, safe-zone e continuidade em **vídeo integral**, não só thumbnails.
- Direitos de entrada e saída, voz/trilha, marcas d'água e eventual exibição comercial foram revisados.
- Render final **1080×1920** e sincronismo do WAV/28 legendas fisicamente verificados, sem fingir que upscale cria detalhes inexistentes.
- Nenhum envio ao YouTube/TikTok ou publicação sem autorização expressa.

**Estado atual: NÃO EXISTE NOVO CLIPE FLOW GERADO NEM APROVADO.** Próximo único gesto necessário na interface: entrar no Flow e verificar que a conta possui o pacote gratuito; em seguida, criar somente S01 com o prompt exato, inspecionar a saída e só então usar as demais rodadas.
