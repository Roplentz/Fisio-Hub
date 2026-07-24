# Arquitetura do ViralLab AI

## Camadas

### 1. Ingestão
- Upload de MP4, MOV, MP3 ou WAV.
- Entrada por texto, tema ou transcrição.
- Links externos apenas como referência; o usuário deve possuir direito de uso do conteúdo.

### 2. Processamento multimídia
- FFmpeg extrai áudio, frames-chave, duração e metadados.
- Whisper gera transcrição com timestamps.
- Detector de cenas estima cortes e mudanças visuais.

### 3. Inteligência de conteúdo
- Gemini recebe transcrição, frames selecionados e metadados.
- O agente classifica hook, promessa, tensão, virada, prova, CTA, ritmo e recursos visuais.
- O sistema produz um JSON padronizado segundo `video-analysis.schema.json`.

### 4. Geração
- Hook Factory cria opções de abertura.
- Story Architect monta a narrativa.
- Rodrigo DNA ajusta tom, autoridade, vocabulário e limites éticos.
- Editor Director gera timeline de cortes, textos, zooms, pausas e B-roll.

### 5. Produção
- Remotion ou MoviePy cria uma primeira versão automática.
- FFmpeg incorpora legendas e normaliza áudio.
- O usuário revisa antes da exportação.

### 6. Aprendizado
- Métricas pós-publicação são registradas.
- O Learning Engine compara formatos, temas, hooks e CTAs.
- As recomendações futuras usam apenas padrões agregados, não cópia de falas.

## Fluxo de dados

```text
Vídeo/tema
  -> FFmpeg
  -> Whisper
  -> Frames + transcrição + metadados
  -> Gemini ou LLM local
  -> Análise estruturada
  -> Roteiro + storyboard + plano de edição
  -> Remotion/MoviePy + FFmpeg
  -> Vídeo revisável
  -> Métricas
```

## Segurança e privacidade

- Nenhum prontuário ou dado de paciente deve entrar no fluxo sem anonimização.
- Para conteúdo sensível, usar Whisper, Ollama e processamento local.
- A cota gratuita do Gemini pode usar dados para melhoria de produtos; portanto, não enviar conteúdo confidencial.
- Registrar fonte e licença de músicas, imagens e clipes.

## MVP recomendado

Primeiro MVP sem geração automática de vídeo completo:

1. Upload do vídeo.
2. Transcrição e análise.
3. Roteiro semelhante, mas original.
4. Storyboard com timeline.
5. Exportação em Markdown, JSON e SRT.

A geração integral do vídeo entra após validar que o diagnóstico e os roteiros realmente economizam tempo.