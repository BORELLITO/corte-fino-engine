# E01 v2 — decisão do lote B após observar 12 quadros reais

**Status:** `EDITORIAL_ALTERNATIVES_REVIEWED_NO_MASTER_RELEASE`. Não altera o lote A, o áudio/legendas nem a fonte original E01.

## Evidência material

- GitHub Actions: https://github.com/BORELLITO/corte-fino-engine/actions/runs/44264731877 — SUCCESS. Quatro MP4 reais de Pexels baixados e decodificados completamente; FFprobe, hashes, dimensões e tempos comprovados em artifact #14409886173.
- Folha derivada em 648×1696, 12 quadros extraídos de 15%/50%/85%, SHA-256 `19946e5fe18529d8222f76a7bf0867128308a94e7f42e4412f18e57f6263b955`.
- Dossiê em `contracts/e01_v2_stock_alternatives_physical_editorial_v1.json`. Validador fail-closed `agents/e01_stock_alt_review_gate.py` e testes adversariais.
- Os MP4 não foram preservados para edição e não houve reprodução integral humana; decodificação integral não substitui assistir ao vídeo inteiro. A licença da plataforma não garante automaticamente direitos de terceiros.

## Veredicto por cena (somente QA por amostras)

| Cena | Resultado | Justificativa |
|---|---|---|
| S03-B | REJECTED_EDITORIAL | Banco, reflexo de chuva, montanhas e ambiente claro. Repetiria erro de usar natureza genérica para ilustrar Habacuque e injustiça social |
| S08-B | CONDITIONAL_CONTEXT_ONLY | Mãos folheiam Bíblia, sem rosto visível; há coerência espiritual, mas a passagem trata de fé honesta e não cita necessariamente estudo bíblico; luz branca e texto potencialmente legível exigem avaliação |
| S09-B | REJECTED_EDITORIAL | Escultura ocupa grande área, estética de arranjo, texto manuscrito visível; desvia da ideia de reflexão pessoal |
| S09-C | REJECTED_EDITORIAL | Teclado e luz azul/verde remetem a escritório digital, sem conexão com quarto introspectivo original |

**Nenhum** candidato está aprovado para master. Rejeições e situação condicionada vinculadas por SHA específico; não alterar a decisão por crop, re-color, uso sem contexto, ou outra técnica de edição sem uma nova revisão registrada. O próximo passo criativo é buscar filmagens com função narrativa, em vez de insistir no stock genérico. Se não existirem, produzir tomadas próprias de mãos/objetos com movimento real ou manter a prévia bloqueada em vez de afirmar qualidade inexistente.
