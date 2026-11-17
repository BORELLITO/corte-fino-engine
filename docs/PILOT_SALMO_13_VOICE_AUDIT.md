# Auditoria de voz — piloto Salmo 13

## Decisão

Direção aprovada: **Kokoro-82M local, português brasileiro**.

Candidato-base selecionado para benchmark: **pm_alex**.

A escolha é provisória. O motor só poderá fechar o voice ID depois de comparar pm_alex, pm_santa e pf_dora no mesmo trecho do roteiro.

## Por que pm_alex é o baseline

- é uma voz masculina pt-BR;
- aparece no exemplo oficial de execução do Kokoro para português brasileiro;
- oferece um ponto de comparação neutro para um canal narrativo de reflexão;
- mantém pm_santa e pf_dora como alternativas reversíveis.

## Travas antes da geração final

1. Comparar os três voice IDs no mesmo trecho de 15–20 segundos.
2. Verificar pronúncia de “Salmo”, “lamento”, “angústia” e “esperança”.
3. Avaliar naturalidade, ritmo, pausas, emoção e fadiga auditiva.
4. Confirmar a licença do pacote/voz exato.
5. Auditar as dependências de inferência e seus avisos de licença.
6. Fazer benchmark no ambiente disponível.
7. Gerar a narração final somente após o gate de voz.
8. Manter publicação bloqueada até o QA audiovisual e de direitos.

## Estado atual

- direção: **APROVADA**;
- candidato-base: **pm_alex**;
- voice ID definitivo: **pendente de benchmark**;
- áudio: **não gerado**;
- publicação: **não autorizada**.

## Evidências consultadas

- CLI oficial com exemplo pm_alex: https://github.com/hexgrad/kokoro/blob/main/kokoro/__main__.py
- Lista oficial de vozes: https://huggingface.co/hexgrad/Kokoro-82M/blob/main/VOICES.md
- Licença oficial: https://github.com/hexgrad/kokoro/blob/main/LICENSE

A licença Apache do modelo não elimina a necessidade de auditar a voz específica, o runtime e as dependências antes do uso comercial.
