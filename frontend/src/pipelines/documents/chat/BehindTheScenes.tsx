import type { ChatEvent } from '@/pipelines/documents/libraries/api';
import { fuentesDe } from './AnswerSources';
import { DETRAS_DE_ESCENA } from './explicaciones';

// Lo que manda el chat local en el evento "tool_call" de la búsqueda.
type Busqueda = { busquedas?: { consulta: string; candidatos: number }[]; paginas_para_el_modelo?: number; modo?: string };

// Un paso numerado del detrás de escena: el título, la línea que explica qué es y los datos del turno.
function Paso({ n, titulo, explicacion, children }: { n: number; titulo: string; explicacion: string; children: React.ReactNode }) {
  return (
    <li className="space-y-1">
      <p className="text-sm font-medium"><span className="mr-2 font-mono text-primary">{n}</span>{titulo}</p>
      <p className="text-xs text-muted-foreground">{explicacion}</p>
      <div className="font-mono text-xs">{children}</div>
    </li>
  );
}

// El "detrás de escena" de una respuesta (desplegable): ① la búsqueda, ② el reranker y ③ la respuesta.
// Todos los números salen del turno (eventos tool_call, tool_result y stop); el costo en dólares es estimado.
export function BehindTheScenes({ events }: { events: ChatEvent[] }) {
  const llamada = events.find(e => e.type === 'tool_call')?.arguments as Busqueda | undefined;
  const fuentes = fuentesDe(events);
  const usage = events.find(e => e.type === 'stop')?.usage as Record<string, number | string | undefined> | undefined;
  if (!llamada && !usage) return null;

  return (
    <details className="rounded-lg border border-glass-border px-3 py-2">
      <summary className="cursor-pointer text-xs text-muted-foreground">Detrás de escena: búsqueda, reranker y respuesta</summary>
      <ol className="mt-3 space-y-4">
        <Paso n={1} titulo="Búsqueda" explicacion={DETRAS_DE_ESCENA.busqueda}>
          {llamada?.busquedas?.length
            ? llamada.busquedas.map((b, i) => (
                <p key={i}>"{b.consulta}" → {b.candidatos} candidatos{llamada.modo ? ` · modo ${llamada.modo}` : ''}</p>
              ))
            : <p className="text-muted-foreground">El turno no informa la búsqueda.</p>}
        </Paso>
        <Paso n={2} titulo="Reranker" explicacion={DETRAS_DE_ESCENA.reranker}>
          {fuentes.length
            ? <ul>{fuentes.map((f, i) => (
                <li key={i}>{f.rerank_score != null ? f.rerank_score.toFixed(2) : '—'} · {f.documento?.replace(/\.pdf$/i, '')} · pág. {f.pagina}</li>
              ))}</ul>
            : <p className="text-muted-foreground">No llegó ninguna página al modelo.</p>}
          {llamada?.paginas_para_el_modelo != null && <p className="mt-1 text-muted-foreground">Se queda con hasta {llamada.paginas_para_el_modelo} páginas.</p>}
        </Paso>
        <Paso n={3} titulo="Respuesta" explicacion={DETRAS_DE_ESCENA.respuesta}>
          {usage
            ? <p>
                {usage.modelo} · {usage.llamadas_al_modelo} {usage.llamadas_al_modelo === 1 ? 'llamada' : 'llamadas'} ·
                {' '}{usage.tokens_de_entrada} tokens de entrada · {usage.tokens_de_salida} de salida
                {usage.costo_estimado_usd != null && <> · <strong>USD {Number(usage.costo_estimado_usd).toFixed(5)} (estimado)</strong></>}
                {' '}· 0 créditos de LlamaCloud
              </p>
            : <p className="text-muted-foreground">Todavía respondiendo…</p>}
        </Paso>
      </ol>
    </details>
  );
}
