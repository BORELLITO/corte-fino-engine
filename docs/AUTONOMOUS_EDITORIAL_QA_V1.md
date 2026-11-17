# VERBO NO CHÃO — Governança editorial autônoma v1

**Decisão nova (17/11/2026):** O usuário não precisa revisar roteiros, passagens, copies ou o vídeo terminado. O motor deve assumir a criação, a crítica, a correção e o controle de qualidade. A única ação externa mantida é a **autorização específica para publicação**. A ausência dessa autorização não impede produzir um vídeo tecnicamente finalizado, mas impede publicá-lo.

## Arquitetura operacional

`PEDIDO → RESEARCH → ROTEIRO → REVISÃO SEMÂNTICA POR IA → CORREÇÕES E REAVALIAÇÃO → ROTEIRO APROVADO INTERNAMENTE → ASSETS E LICENÇAS → VOZ E MÚSICA → MONTAGEM → LEGENDAS → QA FÍSICO → VÍDEO VALIDADO → AUTORIZAÇÃO ESPECÍFICA DE PUBLICAÇÃO`

**Linguagem precisa das aprovações:**

- `DRAFT_REVIEW_REQUIRED`: condição histórica de origem do texto; não significa que o proprietário tenha de ler o texto. Continua válida no pacote de três rascunhos e no piloto para preservar hashes e contratos.
- `AUTO_APPROVED_FOR_INTERNAL_PRODUCTION`: um parecer semântico real foi produzido pelo modelo, verificou oito pilares e passou nos gates de vínculo textual. **Aprova somente o roteiro para prosseguir na pipeline interna; não é parecer humano, certificado teológico, prova de licenciamento ou autorização de TTS.**
- `BLOCKED_PHYSICAL_MEDIA_AND_RIGHTS_NOT_PROVEN`: vídeo ainda não foi renderizado e as quatro dimensões materiais/legais não têm evidência de mídia real.
- `READY_FOR_PUBLICATION_AUTHORIZATION`: estado futuro **somente** após o arquivo final ser efetivamente renderizado, decodificado, hasheado, auditado em áudio, vídeo, direitos, segurança, sincronização, originalidade e metadados. Não é uma qualidade que um JSON sozinho possa alegar.
- `PUBLISHED`: requer autorização separada do usuário e confirmação real da plataforma. Nunca automático por causa do selo de roteiro ou vídeo.

## 12 pilares, dois níveis de controle

**Nível 1 — roteiro (8):** contexto bíblico primário; distinção entre texto e interpretação; integridade cristã; segurança emocional; linguagem original/direitos de texto; estrutura de retenção; clareza pt-BR para TTS; comprovação das fontes.

**Nível 2 — vídeo real (4):** storyboard e imagens com direitos, contexto e antirrepetição; voz/música com proveniência, licença e audição; legendas sincronizadas, vídeo master decodificável e especificações técnicas; títulos, capa, créditos, regras da plataforma, integridade de monetização e publicação.

No E01, os oito pilares de roteiro foram apreciados semanticamente **por este assistente ChatGPT em conversa**, com achados vinculados ao hash `67052ec614f3beaca25cbac40414eecb7f197be0b73b7c1af4fd6579c0cf6990` e fontes externas. É uma **revisão de IA de um único modelo**, não avaliação independente de um segundo modelo ou especialista teológico humano. O CI confere a existência, a integridade, os vínculos e os bloqueios do parecer; **não reexecuta um modelo para validar a interpretação.**

Fontes bíblicas de apoio: https://bible.usccb.org/bible/habakkuk/1 ; https://bibleproject.com/guides/book-of-habakkuk/ ; https://classic.net.bible.org/passage.php?passage=hab+1%3A2-4 . O contexto inicial da passagem é a violência e injustiça que paralisam a lei, e o diálogo prossegue no livro. As fontes não autorizam transcrição integral de traduções.

O parecer E01 consta em `contracts/e01_ai_editorial_review_v1.json`. A validação encontra-se em `agents/autonomous_editorial_gate.py`; o quadro de doze pilares em `agents/video_pillar_readiness.py`; ambos são emitidos pelo pré-voo e conferidos por SHA-256 pelo coordenador. O status **continua BLOCKED** na ausência de direitos completos de mídia, WAV master ou vídeo final. Falsas aprovações ou troca de texto não passam.

## Operação dos próximos episódios sem depender de revisões do proprietário

O coordenador editorial deve executar:

1. Pesquisar recorte bíblico e checar contexto com duas fontes confiáveis (ao menos uma primária).
2. Gerar narração original, distinguir citação, exegese e aplicação; evitar garantias sobrenaturais, manipulação, uso indiscriminado de violência e substituição de cuidado clínico.
3. Produzir uma crítica semântica por um modelo genuíno. Se falhar, reescrever e **submeter o novo SHA-256** a nova avaliação; nunca reutilizar recibo antigo ou declarar que regex realizou crítica semântica.
4. Fixar no manifesto a versão, modelo/revisor e vínculo do parecer exato ao texto. O CI verifica sua integridade e status; se faltarem provas, **BLOCKED**.
5. Continuar produção audiovisual, aplicando os outros quatro pilares sobre mídia real.
6. Entregar vídeo pronto, se todos os gates forem cumpridos, sem pedir ao usuário revisões intermediárias nem assinatura de QA. A publicação permanece separada.

### Limitação de infraestrutura real — sem promessa de IA invisível no CI

GitHub Models foi encerrado em 30/07/2026 (https://github.blog/changelog/2026-07-01-github-models-is-being-fully-retired-on-july-30-2026/). Não há uma API de LLM conectada e comprovada neste repositório. **Nesta etapa, o parecer semântico de E01 foi produzido pelo ChatGPT desta conversa e versionado.** O runner GitHub Actions executa validações determinísticas, não múltiplos modelos agentes. Novos pareceres podem ser produzidos pelo assistente em novas execuções de chat/Work, sem revisão do usuário, e então validados pelo GitHub. A geração autônoma futura a partir de uma execução do CI, sem uma conversa, exigirá conexão comprovada com provedor de inferência e permissões/custos testados. Não conectar API cobrada nem declarar que já existe um cérebro de LLM rodando sozinho.

## Continuidade, reversão e proteção

Esta política complementa as travas históricas de proteção do piloto Salmo 13, sem modificar `contracts/pilot_salmo_13_master.json` ou `verbo-no-chao/bootstrap`. Os status do pacote antigo de roteiro permanecem documentais e não autorizam publicação. O escopo é **somente episódios novos**.

A PR nova é empilhada na #34; rollback = descartar a branch sem tocar nos contratos aprovados. Não houve gravação de WAV final, criação de vídeo master, postagem, merge, exclusões ou contratação de serviços. Custo adicional: minutos de CI para código e testes; nenhum modelo pago foi chamado.
