# Sprint 1 — Núcleo audiovisual auditado

## Resultado

O ViralLab passou a possuir contratos independentes para mídia, legendas e
renderização. A integração usa padrões auditados do MoneyPrinterTurbo 1.3.4,
sem importar sua WebUI, prompts, músicas ou API antiga.

## Entregas

- `MediaProvider` com implementações local e Pexels;
- proveniência em `media-manifest.json`;
- limite de download de 250 MB e formatos permitidos;
- presets acessíveis de legenda;
- `VideoRenderer` e `RenderJob` com relatório auditável;
- feature flag `MPT_RENDER_ENGINE`;
- testes de contrato, caminhos, consentimento operacional e proveniência;
- registro `THIRD_PARTY_NOTICES.md`.

## Configuração opcional

```bash
export PEXELS_API_KEY="..."
export MPT_RENDER_ENGINE="mpt"
```

Sem chave do Pexels, o sistema falha de forma controlada e mantém o fluxo local.
A flag `mpt` ativa a camada compatível auditada, mas o compositor continua
sendo o renderizador FFmpeg do ViralLab.

## Critério do piloto

Gerar uma prévia de 30–60 segundos com mídia autorizada, verificar
`generated/render-report.json` e `media-manifest.json`, e somente então
aprovar a mídia por cena.

## Fora deste sprint

- publicação automática;
- clonagem de voz;
- exposição pública da API;
- fila Redis;
- músicas de terceiros;
- migração completa da interface Streamlit para SaaS.
