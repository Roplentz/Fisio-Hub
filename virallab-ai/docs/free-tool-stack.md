# Stack gratuita do ViralLab AI

## Núcleo recomendado

| Função | Ferramenta principal | Alternativa | Observação |
|---|---|---|---|
| Análise multimodal e roteiro | Gemini API / Google AI Studio | Ollama | O Gemini possui cota gratuita limitada; conteúdo enviado no free tier pode ser usado para melhoria dos produtos. |
| Transcrição | Whisper | whisper.cpp | Execução local, código e pesos sob licença MIT. |
| Processamento audiovisual | FFmpeg | — | Base para extrair áudio, frames, cortes, legendas e renderizar. |
| Composição de vídeo | Remotion | MoviePy | Remotion favorece interfaces web; MoviePy acelera protótipos em Python. |
| Legendas | Whisper + FFmpeg | Subtitle Edit | Exportar SRT e queimar legenda quando necessário. |
| LLM local | Ollama | LM Studio | Útil para privacidade e redução de custo. |
| Imagens locais | ComfyUI + modelos abertos | AUTOMATIC1111 | Verificar licença de cada modelo antes de uso comercial. |
| Voz local | Piper TTS | Coqui TTS | Não clonar voz de terceiros sem autorização. |
| Banco local | SQLite | Supabase free tier | Começar local; migrar só quando houver necessidade de colaboração e escala. |
| Interface | Next.js ou Vite/React | Streamlit | Streamlit é mais rápido para validar; React é melhor para produto. |
| Armazenamento | Google Drive | armazenamento local | Drive para referências, roteiros, exports e métricas. |
| Automação | GitHub Actions | scripts locais | Usar com parcimônia para não depender da franquia gratuita. |

## O que fica para uma fase posterior

- Geração de vídeo generativo por API paga.
- Avatares realistas.
- Clonagem de voz.
- Busca automática de tendências.
- Publicação automática em redes sociais.

## Regra econômica

O MVP deve funcionar sem nenhuma API paga obrigatória. A API melhora velocidade e qualidade, mas o modo local precisa continuar disponível.

## Regra jurídica

O sistema analisa padrões de comunicação. Ele não deve reproduzir falas, identidade visual, voz, rosto ou edição proprietária de um criador de forma indistinguível.