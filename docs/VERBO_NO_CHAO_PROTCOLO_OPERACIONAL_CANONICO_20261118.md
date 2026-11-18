# VERBO NO CHÃO — Protocolo operacional canônico (camada de interpretação, 18/11/2026)

**Status: LEITURA E DIREÇÃO / DRAFT PR #42. NÃO É alteração do manifesto canônico nem aprovação de master.**
Esta camada resolve diferenças de interpretação entre contratos, sem reescrever mídia, direitos, autoria ou decisões do proprietário. Em caso de divergência com arquivo executável canônico, o motor bloqueia; não edita silenciosamente a fonte.

## 0 — Precedência das fontes e isolamento

1. **Decisões expressas do proprietário >** contratos aprovados de escopo específico > código executável e testes > políticas genéricas e histórico > hipóteses e propostas. Direitos, integridade e publicações não podem ser dispensados por delegação criativa.
2. `main` é histórico, `verbo-no-chao/bootstrap` é a branch de base canônica, PR #41 isola produção E01, PR #42 isola correções técnicas, empilhadas e **sem merge**. Teste verde na PR #42 não atualiza automaticamente bootstrap nem a PR #41.
3. **Clean room total:** não importar imagens, vozes, roteiros, prompts, código ou convenções de Because Of This, Corte Fino, Rajada etc. A infraestrutura física do repositório pode ser compartilhada, mas os contratos e assets são independentes. Exceções exigem autorização do proprietário.
4. **Cloud-only:** computação somente em serviços cloud autorizados; celular/PC servem de interface. Neste chat, usar conectores oficiais, Python e arquivos disponíveis. Navegação autenticada não equivale a ter ChatGPT Work ativado. Não usar TinyFish neste projeto; Playwright do GitHub é efêmero e limitado a páginas públicas.

## 1 — Autonomia e responsabilidades

5. Diretor/assistente decide roteiro, ordem de tarefas, criação, rejeição de mídia, correções e QA interno; sem pedir microaprovações. **Não é** uma equipe de oito modelos independentes executando LLM continuamente: os oito jobs atuais auditam provas de forma determinística, e revisão semântica nova precisa de avaliação real documentada e vinculada ao SHA do roteiro.
6. Somente aprovação explícita do proprietário habilita publicação externa, gasto, assinatura, exclusões irreversíveis, permissões ou alterações de credenciais. A autorização para produzir não implica autorização para publicar.
7. **Estados distintos:** roteiro aprovado internamente ≠ mídia aprovada; `PREVIEW_READY` ≠ master; `READY_FOR_OWNER_APPROVAL` do manifesto legada corresponde semanticamente a *aguardando autorização de publicação* para novos episódios, NÃO exige assinatura de qualidade; `PUBLISHED` requer postagem verificada na plataforma e permissão explícita.
8. **Fail closed:** falta de prova, recurso gratuito, mídia íntegra, direito aplicável ou ferramenta significa BLOCKED com motivo e próxima ação concreta, não “sucesso” por JSON ou CI verde.

## 2 — Travas editoriais E01 v2

9. `VNC-W01-E1` preserva Habacuque 1:2–4, 12 shots, 70,425 segundos, 182 palavras, 28 cues. Script SHA `c64b57cb9d6529b60b9e80ab7607e5887f909dd00e14cd80ed9ec2b7474a5dc6`; WAV SHA `4f2ee1ff0171ddedb7c64e0dce2300c53a0ef105ef12d643a7af6b0a4621942e`; ASS SHA `0b8171a473cbc247eb48ed822bb006a04c74510b8c4cd1b30e409c226f1bb98a`. Mudança em roteiro exige novo parecer semântico e hashes de narração/legenda; não modificar para acomodar footage genérica.
10. **Passagem bíblica:** preservar o lamento contra violência e injustiça coletiva, sem transformar o texto em promessa de sucesso pessoal, prazo divino, cura ou prosperidade. Texto bíblico de tradução moderna só com licença específica; preferir paráfrase original com fonte e sem criar fala de Deus.
11. Imagens de época são **símbolos visuais**, nunca fotografias/filmagens autênticas de Judá, de Habacuque ou de um fato bíblico. Pessoas reais identificáveis não devem parecer ligadas a crimes, sofrimento ou testemunhos inventados.

## 3 — Direção de filmagem

12. Para este E01, a regra **específica** do universo visual prevalece sobre a proporção **sugerida, não obrigatória**, de 60–70% stock do manual geral. S01, S02, S06, S07, S08, S09, S11 e S12 precisam de mesma pessoa anônima e mesmo ambiente `ROOM_A`; S03/S04/S05/S10 podem ter origens independentes, desde que haja fidelidade narrativa, direitos e coerência de cor/luz.
13. **S01 obrigatória:** adulto anônimo visto de costas, casaco grafite, janela chuvosa à noite, luz âmbar, mesa de madeira e **caderno fechado**. Sem rosto, texto, marcas, efeitos sobrenaturais ou gráficos. Somente clipe real >=5,74 segundos, com movimento temporal verificável e revisão do diretor, pode originar o *frame anchor* de referência. 2,04 segundos e outros candidatos rejeitados permanecem rejeitados.
14. **S06:** caderno pode estar aberto mais tarde (continuidade temporal narrativa), mas a S01 deve permanecer fechada até o corte. **S12:** abertura parcial do caderno é movimento temporário; para o loop conectar com S01, último quadro deve retornar a composição e estado fechado da primeira cena; validar visualmente a transição. Isto é instrução de execução, não modificação do texto, narração, trama ou storyboard.
15. **Legendas:** contrato global indica 380 px livres em baixo; prompts individuais pedem até 420 px. Aplicar a **restrição mais conservadora: 420 px** de área livre no master 1080×1920, considerando safe zones efetivas das plataformas no QA. Nunca deslocar texto e atriz/objetos para essa área só porque passou na regra menos restritiva. O gate atual de geometria não comprova a compatibilidade com interfaces reais.
16. O alvo canônico E01 é **1080×1920, 30 fps**. Arquivo 480×848/24 fps é prova de geração apenas, não master; upscale não melhora resolução nativa nem permite vender falso 4K.

## 4 — Segurança de mídia e liberação

17. Cada shot necessita `scene_id`, arquivo físico, hash do byte exato, origem, tempo de entrada/saída, direitos/licença e revisão semântica/continuidade. Referência visual de personagem pode ser reutilizada como guia de *conditioning*, mas **não** autoriza repetir o mesmo take/arquivo de origem no vídeo: cropar, acelerar, reverter, espelhar e dar zoom não torna asset novo.
18. Proibido repetir automática ou silenciosamente clipe curto para completar duração; rejeitar output pré-existente e caminhos inválidos. Arquivos físicos de narração, música, captions e MP4 devem corresponder a manifestos. Nunca substituir silenciosamente hash declarado pelo hash de outro arquivo.
19. Trilha exige origem/licença, mix audível inteligível, **ducking real guiado pela voz** e nível de áudio analisado no master. Os testes sintéticos de sidechain não comprovam loudness ou sincronia do E01 final.
20. Oito pilares semânticos e quatro pilares físicos são **portas separadas**; nenhuma prova de estrutura, FFprobe, status verde, screenshot, fonte URL ou texto de contrato prova sozinha licença, visualidade, desempenho comercial ou aprovação do vídeo final.
21. **Licenças em aberto:** modelo Kokoro upstream Apache-2.0 e termos de um host não provam automaticamente as licenças efetivas de runtime + voz consumida; Pexels/stock exige análise de termos, pessoas e uso contextual; música exige licença própria. Nunca promover `CLEARED` por conveniência.
22. **Segredos/privacidade:** nenhum upload para GitHub público de mídia privada; nenhuma impressão de chaves. Cada execução de geração gratuita verifica custo efetivo, disponibilidade, licença e limites. Sem repetição cega, bypass de autenticação ou cobrança.
23. **One-shot S01:** preservar automação vigente para 18/11/2026 15:37 (Brasília). Um único nonce de commit na branch de PR #41, se não existir e preflight permitir. Não executar manualmente, não rerun de SHA obsoleto, não antecipar/duplicar a geração. A PR #42 adiciona bloqueio de replay, mas não está integrada à PR #41.
24. Arte gerada em chat ou prévia não equivale a asset licenciado/aprovado; promover somente com bytes disponíveis, hashes e QA; preservar arte rejeitada como rejeição, jamais como recurso canônico. O master e publicação continuam BLOCKED até que todas as provas existam.

## 5 — Portão final e próximo passo

Sequência priorizada: **(i)** reavaliar S01 no único evento agendado e registrar seus bytes/frames se houver, **(ii)** aprovar ou rejeitar como âncora real por critérios editoriais, **(iii)** produzir ROOM_A com first frames individualmente dirigidos e fontes independentes S03/S04/S05/S10, **(iv)** ingestão privada byte a byte e manifesto, **(v)** montar e auditar mestre com som e legendas, **(vi)** resolver direitos e entregar vídeo com metadados; **(vii)** publicação só depois de autorização específica.
No momento de qualquer falha, registrar o bloqueio e escolher a alternativa gratuita segura, sem autodeclarar uma etapa concluída.

**Rollback:** descarte PR #42 sem merge; as branches e os arquivos aprovados não foram alterados. O contrato canônico ainda rege qualquer divergência não resolvida.
