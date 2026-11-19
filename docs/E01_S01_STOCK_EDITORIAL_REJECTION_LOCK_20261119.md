# E01 S01 — bloqueio de reutilização de stock rejeitado (19/11/2026)

**Projeto:** VERBO_NO_CHAO_EXCLUSIVO. **Fase:** proteção contra regressão editorial; não é nova montagem nem master.

## Decisão de produção preservada

O E01 `Quando você pergunta e nada muda` (Habacuque 1:2–4), 70,425 s, 12 cenas e 28 legendas permanece em RASCUNHO. A orientação atual prioriza **clipes capturados em câmera** de bancos online sob licenças compatíveis, de preferência sem custo; geração por IA não é etapa obrigatória. O storyboard ROOM_A continua como referência e a montagem simbólica multifonte da PR #57 não possui aprovação estética para substituí-lo.

## Evidência de reprovação que deve sobreviver às próximas execuções

| Tentativa | SHA-256 do render | Fontes | Situação | Run físico |
|---|---|---|---|---|
| S01 V1 | `3653dd73575446533b1f47512b3c236b9184bba150fec5116c5526ba0ee1013e` | Pexels 32788087 / 4458845 / 6376122 | REJEITADO: escrita/decorativo na parede, caderno claro | [44614902739](https://github.com/BORELLITO/verbo-no-chao-engine/actions/runs/44614902739) |
| S01 V2 | `2c099db52b219cb901977d98fac29f91579a4be1d9a2126f4ff6ba0cbcc7c1e5` | Pexels 8860242 / 4458845 | REJEITADO: claridade diurna na janela contraposta a chuva noturna; ausência de caderno fechado | [44615672379](https://github.com/BORELLITO/verbo-no-chao-engine/actions/runs/44615672379) |

Ambos os renders existiram fisicamente como prévias **720×1280 / 30 fps / 5,767 s**. Um PASS no FFmpeg NÃO revoga a reprovação de estética; nenhuma versão obteve direitos individualizados ou 1080×1920 master validado.

## Correção mínima implementada nesta branch isolada

- `contracts/e01_s01_stock_rejection_lock_20261119_v1.json` — registro imutável por política dos dois SHAs e respectivos conjuntos de IDs, prova e razões.
- `agents/e01_s01_stock_rejection_gate.py` — verifica regras fixas independentes do contrato, ID do projeto/cena, tentativas de falsificar direitos, mídia ou autorização, integridade do SHA local quando arquivo fornecido e combinação de fontes. Duas cópias de um vídeo com outra codificação **não** driblam a rejeição quando usam exatamente a mesma dupla/trio de fontes.
- `agents/e01_s01_multi_stock_pilot_v1.py` — chama o gate após hash físico e decodificação completa; quando reconhece rejeição anterior, expõe `REAL_STOCK_MONTAGE_PHYSICALLY_VERIFIED_REJECTED_EDITORIAL`. Ainda pode terminar CI com sucesso **técnico**, mas não reporta aprovação cinematográfica, direitos ou master.
- `tests/test_e01_s01_stock_rejection_gate.py` — testes adversariais de SHAs antigos, mesmo source-set com encode diferente, troca de projeto/cena, falsas aprovações, direitos de fonte, duplicatas, origem inválida, divergência de SHA local e adulteração do registro.

**Gate adicional de resolução nativa:** a fonte Pexels [4458845](https://www.pexels.com/video/rainy-nights-4458845/) anuncia `1920×1080`, horizontal. Um crop para 9:16 preservando a altura física de 1080 px só dispõe de cerca de 608 px de largura; portanto não fornece por si um `1080×1920` vertical nativo. O gate agora expõe `source_native_1080x1920_dimensions_sufficient=false` quando qualquer fonte não comprovar largura >=1080 **e** altura >=1920. A flag de dimensão não aprova licenças nem estética, e não altera o uso da prévia como prova física. Teste adversarial incluído.

**Limite importante:** o novo gate não é revisor visual. Uma fonte inédita recebe sempre `PENDING_HUMAN_FRAME_AND_RIGHTS_REVIEW`, jamais `APPROVED`. Uma cena diferente ou um novo corte não recebem revisão automática por similitude. Um arquivo de teste sintético não prova decodificação de MP4 real; a prova de mídia permanece responsabilidade do pipeline FFmpeg existente.

**Eficiência e segurança:** nenhuma chamada a provedor externo, geração de IA, download de MP4, nova chave, gasto ou workflow de GPU foi introduzido. Os testes são offline. O workflow de download/render mantém seu gatilho estreito original (alterações no próprio arquivo YAML), que não foi tocado.

## Próximo passo cinematográfico

Não reutilizar V1/V2. Buscar um único take real ou uma mesma sessão de ator anônimo junto à janela escura chuvosa, luz neutra/quente discreta, caderno fechado e movimento físico verificável. Fazer primeiro leitura de frames, reputação/licença e continuidade sem alegar que clipes de autores distintos compartilham local/ator. Se nenhum stock cobrir honestamente os critérios, preparar uma alternativa de abertura simbólica para aprovação **antes** de renderizar novamente.

**Proibido avançar:** promoção a master, merge de produção, alterações em `main`, upload público de stock bruto, publicação ou gasto sem autorização específica. Preservar PR #57 e PR #58 em DRAFT.
