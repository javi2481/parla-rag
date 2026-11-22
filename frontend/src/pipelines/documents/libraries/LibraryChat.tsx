import { useState } from 'react';
import { LoaderCircle, Send } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { JsonView } from '@/components/wizard/JsonView';
import { MarkdownView } from '@/components/wizard/MarkdownView';
import { INPUT } from '@/components/wizard/RowsEditor';
import { chat, type ChatEvent, type Turn } from './api';

// Junta el texto de la respuesta. Si LlamaCloud mandó el texto completo ("text"), se usa ese; si no, se suman los pedacitos ("text_delta").
function answerOf(events: ChatEvent[]) {
  const full = events.filter(e => e.type === 'text').map(e => e.content ?? '').join('');
  return full || events.filter(e => e.type === 'text_delta').map(e => e.content ?? '').join('');
}

// Junta el razonamiento del agente, igual que la respuesta.
function thinkingOf(events: ChatEvent[]) {
  const full = events.filter(e => e.type === 'thinking').map(e => e.content ?? '').join('');
  return full || events.filter(e => e.type === 'thinking_delta').map(e => e.content ?? '').join('');
}

// Una página que usó el chat local para responder: de qué documento es, qué página y qué tan relevante la vio el reranker.
type Source = { documento?: string; pagina?: number; rerank_score?: number | null };

// Saca las páginas que el chat local le pasó al modelo (vienen en el resultado de la búsqueda).
// Una página puede venir en varios fragmentos: se muestra una vez, con el mejor score del reranker.
function sourcesOf(events: ChatEvent[]): Source[] {
  const result = events.find(e => e.type === 'tool_result')?.result;
  if (!Array.isArray(result)) return [];
  const pages = new Map<string, Source>();
  for (const s of result as Source[]) {
    if (!s.documento || s.pagina == null) continue;
    const key = `${s.documento}|${s.pagina}`;
    const seen = pages.get(key);
    if (!seen || (s.rerank_score ?? 0) > (seen.rerank_score ?? 0)) pages.set(key, s);
  }
  return [...pages.values()];
}

// Un turno de chat: la pregunta, el razonamiento, las búsquedas que hizo el agente con lo que encontró y la respuesta.
// local: la biblioteca usa el motor local (LlamaIndex + Voyage AI + OpenAI), que no cobra créditos de LlamaCloud.
export function TurnView({ turn, live, local }: { turn: Turn; live?: boolean; local: boolean }) {
  const thinking = thinkingOf(turn.events);
  const calls = turn.events.filter(e => e.type === 'tool_call');
  const results = turn.events.filter(e => e.type === 'tool_result');
  const stop = turn.events.find(e => e.type === 'stop');
  const errors = turn.events.filter(e => e.type === 'error' || e.error);
  const answer = answerOf(turn.events);
  const sources = sourcesOf(turn.events);
  return (
    <div className="space-y-3 rounded-xl border border-glass-border bg-background/40 p-4">
      <p className="font-medium">{turn.prompt}</p>
      {thinking && (
        <details>
          <summary className="cursor-pointer text-xs text-muted-foreground">Razonamiento del agente</summary>
          <p className="mt-1 whitespace-pre-wrap text-xs text-muted-foreground">{thinking}</p>
        </details>
      )}
      {calls.length > 0 && (
        <details>
          <summary className="cursor-pointer text-xs text-muted-foreground">Búsquedas del agente ({calls.length})</summary>
          <ul className="mt-2 space-y-2">
            {calls.map((call, i) => (
              <li key={call.call_id ?? i} className="text-xs">
                <span className="font-mono text-primary">{call.name}</span>
                <JsonView data={call.arguments} />
                {results.filter(r => r.call_id === call.call_id).map((r, j) => (
                  <details key={j} className="mt-1">
                    <summary className="cursor-pointer text-muted-foreground">Lo que encontró</summary>
                    <JsonView data={r.result} />
                  </details>
                ))}
              </li>
            ))}
          </ul>
        </details>
      )}
      {answer && <MarkdownView markdown={answer} />}
      {sources.length > 0 && (
        <p className="flex flex-wrap gap-1">
          <span className="text-xs text-muted-foreground">Páginas que leyó el modelo:</span>
          {sources.map((s, i) => (
            <span key={i} className="rounded-full border border-glass-border px-2 py-0.5 font-mono text-xs text-muted-foreground">
              {s.documento} · pág. {s.pagina}{s.rerank_score != null ? ` · ${s.rerank_score.toFixed(2)}` : ''}
            </span>
          ))}
        </p>
      )}
      {live && !stop && <p className="flex items-center gap-2 text-xs text-primary"><LoaderCircle className="size-3.5 animate-spin" /> El agente está trabajando…</p>}
      {errors.map((e, i) => <p key={i} className="text-xs text-destructive">{e.content ?? e.error}</p>)}
      {stop?.usage && (
        <p className="font-mono text-xs text-muted-foreground">
          {Object.entries(stop.usage).filter(([, v]) => v != null).map(([k, v]) => `${k.replaceAll('_', ' ')}: ${v}`).join(' · ')}
          {local ? ' · 0 créditos de LlamaCloud' : ' · 100 créditos por turno (lista de precios)'}
        </p>
      )}
    </div>
  );
}

// El chat de la biblioteca: cada pregunta busca en todos sus documentos. Las respuestas se ven en vivo.
export function LibraryChat({ libraryId, turns, disabled, local, onDone }: { libraryId: string; turns: Turn[]; disabled: boolean; local: boolean; onDone: () => void }) {
  const [prompt, setPrompt] = useState('');
  const [live, setLive] = useState<Turn | null>(null);
  const [error, setError] = useState('');
  // La conversación de esta pantalla: la crea el backend con la primera pregunta y llega en el evento "stop".
  const [conversationId, setConversationId] = useState<string | undefined>();

  // Manda la pregunta y va mostrando los eventos a medida que llegan.
  async function send() {
    if (!prompt.trim() || live) return;
    const turn: Turn = { at: new Date().toISOString(), prompt, events: [] };
    setLive(turn); setError(''); setPrompt('');
    try {
      await chat(libraryId, turn.prompt, event => {
        turn.events = [...turn.events, event];
        if (event.type === 'stop' && event.conversation_id) setConversationId(event.conversation_id);
        setLive({ ...turn });
      }, { conversationId: local ? conversationId : undefined });
      onDone();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'No se pudo chatear.');
    } finally {
      setLive(null);
    }
  }

  return (
    <div className="space-y-4">
      {turns.map((turn, i) => <TurnView key={i} turn={turn} local={local} />)}
      {live && <TurnView turn={live} live local={local} />}
      {error && <p role="alert" className="text-sm text-destructive">{error}</p>}
      <div className="flex gap-2">
        <textarea className={`${INPUT} min-h-16`} value={prompt} disabled={disabled || !!live} placeholder="Preguntale algo a la biblioteca…"
          onChange={e => setPrompt(e.target.value)} onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(); } }} />
        <Button onClick={send} disabled={disabled || !!live || !prompt.trim()}><Send /> Preguntar</Button>
      </div>
      <p className="text-xs text-muted-foreground">
        {local
          ? 'Cada pregunta busca en el índice local (Voyage AI) y la responde OpenAI: no usa créditos de LlamaCloud.'
          : 'Cada pregunta cuesta 100 créditos según la lista de precios de LlamaCloud.'}
      </p>
    </div>
  );
}
