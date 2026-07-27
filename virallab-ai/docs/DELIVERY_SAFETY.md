# ViralLab — Segurança de entrega

## Regra de produção

Nenhuma alteração funcional deve ser enviada diretamente para `main`.

Fluxo obrigatório:

1. criar uma branch curta;
2. abrir pull request;
3. aguardar todos os checks obrigatórios;
4. publicar a branch em um aplicativo Streamlit de staging;
5. validar manualmente os fluxos essenciais;
6. somente então aprovar o merge em `main`.

## Aplicativo de staging

Criar no Streamlit Community Cloud um segundo aplicativo com estas configurações:

- repositório: `Roplentz/Fisio-Hub`;
- branch: a branch do pull request ou uma branch permanente `staging`;
- arquivo principal: `virallab-ai/app.py`;
- secrets: cópia controlada dos secrets necessários, sem credenciais de produção quando houver alternativa;
- nome sugerido: `rp-virallab-staging`.

O staging não deve compartilhar dados persistentes com produção.

## Checks automatizados mínimos

O workflow `ViralLab Delivery Safety` deve:

- instalar as dependências equivalentes às de produção;
- compilar os entrypoints;
- iniciar o servidor com `python -m streamlit run app.py`;
- aguardar `/_stcore/health` responder `200 OK`;
- confirmar que a página raiz responde HTTP 200;
- falhar quando o processo encerrar durante a inicialização.

## Checklist manual de staging

Antes do merge:

- [ ] página inicial abre sem tela preta ou traceback;
- [ ] sidebar e seletor de etapas aparecem;
- [ ] criação de novo projeto funciona;
- [ ] upload de vídeo aceita um arquivo pequeno;
- [ ] geração local de estratégia e roteiro funciona;
- [ ] navegação entre etapas não altera o estado indevidamente;
- [ ] erros de IA, voz e FFmpeg aparecem como mensagens controladas;
- [ ] nenhum segredo aparece em tela ou log;
- [ ] uso em dispositivo móvel foi verificado pelo menos visualmente.

## Rollback de emergência

Quando produção falhar após um merge:

1. interromper novas mudanças;
2. identificar o último commit comprovadamente funcional;
3. preferir um pull request de `git revert` do merge defeituoso;
4. quando a indisponibilidade exigir recuperação imediata, mover temporariamente a referência de `main` apenas com autorização explícita;
5. confirmar o novo deploy no Streamlit Cloud;
6. registrar causa, impacto e correção em um post-mortem curto.

Nunca declarar recuperação concluída apenas porque o GitHub aceitou o rollback. A página pública e seus logs precisam ser verificados.

## Proteção recomendada da branch `main`

Configurar no GitHub:

- exigir pull request antes do merge;
- exigir pelo menos uma aprovação;
- exigir branches atualizadas antes do merge;
- exigir os checks `ViralLab CI`, `ViralLab Guardian` e `ViralLab Delivery Safety`;
- bloquear force push e exclusão da branch;
- impedir bypass, salvo conta administrativa de emergência.

Essas configurações são administrativas e não podem ser aplicadas apenas por arquivos versionados no repositório.
