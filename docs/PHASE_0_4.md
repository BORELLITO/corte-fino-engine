# Fase 0.4 — Orquestrador dry-run

Objetivo: conectar os contratos editoriais, bíblicos, de direitos e audiovisuais sem gerar mídia ou publicar.

Fluxo:

1. validar pacote editorial;
2. validar registros de direitos;
3. conferir referências de direitos usadas pelas cenas;
4. validar áudio, imagem e legendas;
5. bloquear publicação;
6. retornar estado e evidências dos gates.

O orquestrador não acessa APIs externas, não grava arquivos de mídia e não altera o pacote de entrada.
