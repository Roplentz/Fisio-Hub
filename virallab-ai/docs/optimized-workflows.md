# Fluxos otimizados do ViralLab AI

## Princípio central

Cada etapa recebe uma entrada estruturada e produz uma saída reutilizável. O fluxo evita pedir novamente informações já definidas e mantém separadas as decisões editoriais, a geração de assets e a renderização.

## Fluxo A — Criar a partir de um tema

1. Brief mínimo: tema, público, objetivo, duração, formato e CTA.
2. Guardrails: originalidade, evidência, privacidade e posicionamento.
3. Hook e tese.
4. Aplicação do template escolhido.
5. Storyboard temporal.
6. Pacote de assets.
7. Legendas e texto de publicação.
8. Revisão humana.
9. Renderização.
10. Registro das métricas após publicação.

## Fluxo B — Criar a partir de um vídeo de referência

1. Upload local.
2. FFmpeg extrai áudio, metadados e frames amostrais.
3. Whisper transcreve.
4. Reverse Engineer identifica estrutura, ritmo, estímulos, hook e CTA.
5. O sistema salva apenas o padrão abstrato.
6. O criador fornece novo tema e objetivo.
7. Script Generator produz uma obra original.
8. O restante segue o Fluxo A.

## Fluxo C — Produção com avatar

1. Gerar apenas as cenas marcadas como `avatar`.
2. Enviar essas falas ao HeyGen ou avatar local.
3. Salvar cada tomada com o identificador da cena.
4. Produzir telas, B-roll e capturas paralelamente.
5. FFmpeg/Remotion monta tudo conforme `video-package.json`.
6. Aplicar SRT, áudio, identidade e normalização final.

## Fluxo D — Aprendizado

Após publicação, registrar:

- alcance;
- retenção em 3 segundos;
- tempo médio assistido;
- taxa de conclusão;
- salvamentos;
- compartilhamentos;
- seguidores gerados;
- CTA utilizado;
- hook utilizado;
- formato utilizado.

O Learning Engine deve comparar vídeos do mesmo objetivo e atualizar recomendações, nunca alterar automaticamente conteúdos científicos sem revisão humana.

## Formato 01 — Professor Cinemático

A sequência padrão é:

1. Tela de impacto.
2. Avatar apresenta a tese.
3. B-roll contextualiza.
4. Avatar explica o benefício.
5. Prova ou limite ético.
6. Demonstração em tela.
7. Avatar entrega a nova visão.
8. CTA visual.

A cada 2–5 segundos deve existir mudança perceptível: enquadramento, palavra-chave, B-roll, captura, pausa ou tela de impacto.

## Contrato de saída

Cada geração produz:

- `video-package.json`: fonte única de verdade;
- `script.md`: storyboard legível;
- `captions.srt`: legendas temporizadas;
- `caption.txt`: publicação;
- `asset-list.txt`: lista de imagens, B-roll e capturas necessárias.

## Próximas integrações

1. Adaptador Gemini/Ollama para hooks e roteiro contextual.
2. Reverse Engineer com Whisper e amostragem de frames.
3. Renderizador Remotion.
4. Adaptador opcional para HeyGen.
5. Upload e organização no Google Drive.
6. Painel web para brief, revisão e exportação.
