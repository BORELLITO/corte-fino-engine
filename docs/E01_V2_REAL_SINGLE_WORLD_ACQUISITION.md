# VERBO NO CHÃO — E01 v2: rota para filmagens reais com mundo visual único

**Etapa:** `SHOOTING_BLUEPRINT_READY_NOT_MEDIA`. Esta rota complementa a PR #41 e o storyboard aprovado sem substituir nenhum contrato de voz, legenda ou imagem original. **Nenhum vídeo novo foi gerado ou captado por este plano**.

## Evidência da decisão

- O projeto testou 8 vídeos MP4 reais em dois lotes; cada um teve arquivo físico, SHA, FFmpeg e 3 amostras visuais verificados em Actions. Nenhum foi aprovado para master.
- Lote A: três rejeitados e corredor S05 apenas condicional.
- Lote B: três rejeitados e mãos folheando Bíblia S08 apenas condicional.
- A falha recorrente não é técnica: falta continuidade de ator, luz, figurino, cenário, objetos e progressão emocional.
- Mesmo stock Pexels compatível com monetização pode exigir cuidado adicional para pessoas/marcas, e vídeos com personagens em contexto negativo são de maior risco. Ver https://www.pexels.com/legal-pages/license/ e https://help.pexels.com/hc/pt/articles/360042295214-Posso-usar-as-fotos-e-os-v%C3%ADdeos-em-um-projeto-comercial.

## Nova estratégia

**Oito das doze tomadas** passam a ser planejadas como um único mundo narrativo, com o mesmo ator anônimo, casaco grafite, caderno, mesa de madeira e janela. A versão do protagonista no rough cut atual é apenas referência; não há permissões ou arquivos de filmagem associados a essa nova proposta. A montagem com vídeo real requer filmagem original em sessão única ou **clipes realmente compatíveis e comprovados**; não sugerir que vários atores stock são uma pessoa só por mudar cor ou crop.

As quatro tomadas restantes são exceções justificadas:
- **S03:** contexto social real e discreto (não paisagem vazia genérica, nem pessoa acusada de injustiça);
- **S04 e S05:** atmosfera simbólica para Habacuque, **sem falsificação histórica**;
- **S10:** ajuda concreta e acolhimento, retratados sem faces identificáveis.

A cronologia do áudio permanece exatamente **70,425s**, as **28 legendas** preservadas e a área inferior de 380px reservada.

## Matriz executável

O contrato `contracts/e01_v2_visual_single_world_acquisition_v1.json` contém para cada uma das 12 cenas: timecode, objetivo narrativo, gesto real necessário, grupo de continuidade, instrução de câmera, pesquisas em inglês, rejeições específicas e estado dos direitos. `agents/e01_visual_single_world_gate.py` é fail-closed: sem vídeo físico, SHA, direitos, inspeção de quadros e áudio final, reporta **0 assets liberados**. Os testes injetam arquivos falsos, publicação falsa, alteração dos timecodes e perda das travas das cenas.

## Produção eficiente sem custo adicional

1. Na curadoria, priorizar primeiro material de **uma mesma sessão/fonte**, não apenas de um mesmo site. Antes de baixar, verificar com preview três critérios: continuidade de pessoa/objeto, gesto que comunica o trecho bíblico e espaço para legendas.
2. Para cada proposta aprovada em etapa de pesquisa, conferir os frames reais e hashes em runner. **Somente** então guardar o arquivo bruto em repositório privado/Drive com permissão de uso documentada; não em branch GitHub pública.
3. Se as cenas não existirem em stock coerente, a execução automática não pode fingir ter filmado. Uma sessão de gravação própria futura, ou geração real de vídeo com termos e custo validados e autorização pertinente, são alternativas; ainda não executadas.
4. Renderizar 1080×1920 somente após os ativos de todas as cenas, áudio e licenças estarem materializados e com QA. Não produzir master inflada de tiles 720×1280.
5. Preservar `main`, `bootstrap`, PRs empilhadas, piloto Salmo 13, E01 roteiro/WAV/ASS imutáveis.

## Referências

- `contracts/e01_v2_12_scene_visual_plan_v1.json` — 12 cenas históricas.
- `contracts/e01_v2_stock_editorial_review_v1.json` — lote A.
- `contracts/e01_v2_stock_alternatives_physical_editorial_v1.json` — lote B.
- `docs/VISUAL_HARMONY_STANDARD.md` — identidade do canal.

**Condição de saída:** o plano e os testes apenas preparam a coleta. Não publicar nem promover candidatos até comprovar todos os direitos e a integridade do master.
