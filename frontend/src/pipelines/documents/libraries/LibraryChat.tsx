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

// Un turno de chat: la pregunta, el razonamiento, las búsquedas que hizo el agente con lo que encontró y la respuesta.
function TurnView({ turn, live }: { turn: Turn; live?: boolean }) {
  const thinking = thinkingOf(turn.events);
  const calls = turn.events.filter(e => e.type === 'tool_call');
  const results = turn.events.filter(e => e.type === 'tool_result');
  const stop = turn.events.find(e => e.type === 'stop');
  const errors = turn.events.filter(e => e.type === 'error' || e.error);
  const answer = answerOf(turn.events);
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
      {live && !stop && <p className="flex items-center gap-2 text-xs text-primary"><LoaderCircle className="size-3.5 animate-spin" /> El agente está trabajando…</p>}
      {errors.map((e, i) => <p key={i} className="text-xs text-destructive">{e.content ?? e.error}</p>)}
      {stop?.usage && (
        <p className="font-mono text-xs text-muted-foreground">
          {Object.entries(stop.usage).filter(([, v]) => v != null).map(([k, v]) => `${k}: ${v}`).join(' · ')} · 100 créditos por turno (lista de precios)
        </p>
      )}
    </div>
  );
}

// El chat de la biblioteca: cada pregunta busca en todos sus documentos. Las respuestas se ven en vivo.
export function LibraryChat({ libraryId, turns, disabled, onDone }: { libraryId: string; turns: Turn[]; disabled: boolean; onDone: () => void }) {
  const [prompt, setPrompt] = useState('');
  const [live, setLive] = useState<Turn | null>(null);
  const [error, setError] = useState('');

  // Manda la pregunta y va mostrando los eventos a medida que llegan.
  async function send() {
    if (!prompt.trim() || live) return;
    const turn: Turn = { at: new Date().toISOString(), prompt, events: [] };
    setLive(turn); setError(''); setPrompt('');
    try {
      await chat(libraryId, turn.prompt, event => {
        turn.events = [...turn.events, event];
        setLive({ ...turn });
      });
      onDone();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'No se pudo chatear.');
    } finally {
      setLive(null);
    }
  }

  return (
    <div className="space-y-4">
      {turns.map((turn, i) => <TurnView key={i} turn={turn} />)}
      {live && <TurnView turn={live} live />}
      {error && <p role="alert" className="text-sm text-destructive">{error}</p>}
      <div className="flex gap-2">
        <textarea className={`${INPUT} min-h-16`} value={prompt} disabled={disabled || !!live} placeholder="Preguntale algo a la biblioteca…"
          onChange={e => setPrompt(e.target.value)} onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(); } }} />
        <Button onClick={send} disabled={disabled || !!live || !prompt.trim()}><Send /> Preguntar</Button>
      </div>
      <p className="text-xs text-muted-foreground">Cada pregunta cuesta 100 créditos según la lista de precios de LlamaCloud.</p>
    </div>
  );
}
