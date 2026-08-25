const OPENAI_URL = 'https://api.openai.com/v1/responses';
const MODEL = Deno.env.get('EXECUTA_AI_MODEL') || 'gpt-5.6-luna';
const SYSTEM = `Você é EXECUTA AI, um agente de execução comportamental. Seu objetivo é fazer o usuário transformar intenção em comportamento observável. Não diagnostique condições psicológicas. Não trate procrastinação como preguiça. Diferencie fato relatado de hipótese. Faça no máximo uma pergunta quando faltar evidência crítica. Se já houver evidência suficiente, gere uma microação observável de 2 a 10 minutos. Prefira execução a conversa. Em crise, autolesão, violência, emergência médica, fraude, invasão, armas ou outra tarefa perigosa/ilegal, defina safety_route=true e não gere microação. Responda SOMENTE JSON válido neste formato: {"safety_route":boolean,"barrier":"clarity|size|judgment|boredom|energy|options|other","confidence":0.0,"evidence":"string","needs_question":boolean,"question":"string|null","micro_action":"string|null","minutes":number|null,"rationale":"string"}.`;

function cors(req: Request) {
  const origin = req.headers.get('origin') || '*';
  return {
    'Access-Control-Allow-Origin': origin,
    'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
    'Access-Control-Allow-Methods': 'POST, OPTIONS',
    'Content-Type': 'application/json',
    'Vary': 'Origin'
  };
}

function extractText(data: any) {
  for (const item of data?.output || []) {
    if (item?.type === 'message') {
      for (const part of item.content || []) if (part?.type === 'output_text') return part.text;
    }
  }
  return '';
}

Deno.serve(async (req: Request) => {
  const headers = cors(req);
  if (req.method === 'OPTIONS') return new Response('ok', { headers });
  if (req.method !== 'POST') return new Response(JSON.stringify({ error: 'method_not_allowed' }), { status: 405, headers });

  const key = Deno.env.get('OPENAI_API_KEY');
  if (!key) return new Response(JSON.stringify({ error: 'configuration_required', message: 'OPENAI_API_KEY ausente no backend.' }), { status: 503, headers });

  try {
    const body = await req.json();
    const task = String(body.task || '').trim().slice(0, 1500);
    const context = String(body.context || '').trim().slice(0, 1500);
    const resistance = Math.max(0, Math.min(10, Number(body.resistance || 0)));
    const barrierHint = String(body.barrier_hint || '').slice(0, 100);
    if (!task) return new Response(JSON.stringify({ error: 'task_required' }), { status: 400, headers });

    const input = `Tarefa: ${task}\nResistência: ${resistance}/10\nBarreira selecionada: ${barrierHint || 'não informada'}\nRelato do usuário sobre o que pesa: ${context || 'não informado'}`;
    const r = await fetch(OPENAI_URL, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${key}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ model: MODEL, instructions: SYSTEM, input, max_output_tokens: 500 })
    });
    const data = await r.json();
    if (!r.ok) return new Response(JSON.stringify({ error: 'openai_error', status: r.status, detail: data?.error?.message || 'Falha no modelo' }), { status: 502, headers });
    const raw = extractText(data);
    let result;
    try { result = JSON.parse(raw); } catch { return new Response(JSON.stringify({ error: 'invalid_model_output', raw }), { status: 502, headers }); }
    return new Response(JSON.stringify({ ...result, model: MODEL }), { headers });
  } catch (e) {
    return new Response(JSON.stringify({ error: 'server_error', detail: e instanceof Error ? e.message : String(e) }), { status: 500, headers });
  }
});
