import { useEffect, useRef, useState } from 'react';
import { LoaderCircle, Send } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { MarkdownView } from '@/components/wizard/MarkdownView';
import { INPUT } from '@/components/wizard/RowsEditor';
import { chat, getConversation, type Turn } from '@/pipelines/documents/libraries/api';
import { answerOf } from '@/pipelines/documents/libraries/LibraryChat';
import { AnswerSources } from './AnswerSources';
import { BehindTheScenes } from './BehindTheScenes';
import type { Filtros } from './ChatFilters';

// Un turno del chat: la pregunta, la respuesta, las páginas citadas agrupadas por clase y el detrás de escena.
function ChatTurn({ turn, live }: { turn: Turn; live?: boolean }) {
  const answer = answerOf(turn.events);
  const done = turn.events.some(e => e.type === 'stop');
  const errors = turn.events.filter(e => e.type === 'error' || e.error);
  return (
    <div className="space-y-3 rounded-xl border border-glass-border bg-background/40 p-4">
      <p className="font-medium">{turn.prompt}</p>
      {answer && <MarkdownView markdown={answer} />}
      {live && !done && <p className="flex items-center gap-2 text-xs text-primary"><LoaderCircle className="size-3.5 animate-spin" /> Buscando en las clases y escribiendo la respuesta…</p>}
      {errors.map((e, i) => <p key={i} className="text-xs text-destructive">{e.content ?? e.error}</p>)}
      <AnswerSources events={turn.events} />
      <BehindTheScenes events={turn.events} />
    </div>
  );
}

// Una conversación: los turnos se acumulan (una pregunta nueva no borra las anteriores) y abajo está el cuadro de pregunta.
// Al terminar cada respuesta baja hasta el final y el foco vuelve al cuadro, listo para la próxima pregunta.
// Mientras responde, el cuadro y el botón quedan deshabilitados: así una pregunta no pisa a la que está en curso.
export function ChatThread({ libraryId, conversationId, filtros, busy, onBusyChange, onDone }: {
  libraryId: string; conversationId: string; filtros: Filtros; busy: boolean;
  onBusyChange: (busy: boolean) => void; onDone: () => void;
}) {
  const [turns, setTurns] = useState<Turn[] | null>(null);
  const [live, setLive] = useState<Turn | null>(null);
  const [prompt, setPrompt] = useState('');
  const [error, setError] = useState('');
  const box = useRef<HTMLTextAreaElement>(null);
  const end = useRef<HTMLDivElement>(null);

  // Al cambiar de pestaña, trae los turnos guardados de esa conversación.
  useEffect(() => {
    let vigente = true;
    setTurns(null); setError('');
    getConversation(libraryId, conversationId).then(
      c => { if (vigente) setTurns(c.turns); },
      e => { if (vigente) setError(e instanceof Error ? e.message : 'No se pudo cargar la conversación.'); });
    return () => { vigente = false; };
  }, [libraryId, conversationId]);

  // Cuando termina una respuesta (o se carga la conversación), baja hasta el final y deja el cursor en el cuadro.
  useEffect(() => {
    if (live || !turns) return;
    end.current?.scrollIntoView({ behavior: 'smooth', block: 'end' });
    box.current?.focus();
  }, [turns, live]);

  // Manda la pregunta a esta conversación, con los filtros elegidos, y va mostrando los eventos a medida que llegan.
  async function send() {
    if (!prompt.trim() || busy) return;
    const turn: Turn = { at: new Date().toISOString(), prompt, events: [] };
    setLive(turn); setError(''); setPrompt(''); onBusyChange(true);
    try {
      await chat(libraryId, turn.prompt, event => {
        turn.events = [...turn.events, event];
        setLive({ ...turn });
      }, { conversationId, filters: filtros });
      setTurns(previos => [...(previos ?? []), turn]);
      onDone();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'No se pudo chatear.');
    } finally {
      setLive(null); onBusyChange(false);
    }
  }

  return (
    <div className="space-y-4">
      {!turns && !error && <p className="flex items-center gap-2 text-sm text-muted-foreground"><LoaderCircle className="size-4 animate-spin" /> Cargando la conversación…</p>}
      {turns?.length === 0 && !live && <p className="text-sm text-muted-foreground">Conversación nueva: preguntá algo sobre cualquier clase de la materia.</p>}
      {turns?.map((turn, i) => <ChatTurn key={i} turn={turn} />)}
      {live && <ChatTurn turn={live} live />}
      {error && <p role="alert" className="text-sm text-destructive">{error}</p>}
      <div ref={end} className="flex gap-2">
        <textarea ref={box} className={`${INPUT} min-h-16`} value={prompt} disabled={busy || !turns} placeholder="Preguntale algo a la materia…"
          onChange={e => setPrompt(e.target.value)} onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); void send(); } }} />
        <Button onClick={() => void send()} disabled={busy || !turns || !prompt.trim()}><Send /> Preguntar</Button>
      </div>
    </div>
  );
}
