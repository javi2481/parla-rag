import { useState } from 'react';
import { Check, FlaskConical, Minus, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { INPUT } from '@/components/wizard/RowsEditor';
import { runEvals, type EvalResult, type EvalRun } from './api';

// "2026-11-16_124019" → "16/11/2026 12:40:19", para mostrar cuándo se corrió.
function when(folder: string) {
  const [date, time] = folder.split('_');
  const [y, m, d] = (date ?? '').split('-');
  return time ? `${d}/${m}/${y} ${time.slice(0, 2)}:${time.slice(2, 4)}:${time.slice(4, 6)}` : folder;
}

// Tilde verde, cruz roja o guion (cuando la pregunta no se midió en esa parte).
function Mark({ ok }: { ok: boolean | undefined }) {
  if (ok === undefined) return <Minus className="size-4 text-muted-foreground" aria-label="no se mide" />;
  return ok ? <Check className="size-4 text-mint" aria-label="sí" /> : <X className="size-4 text-destructive" aria-label="no" />;
}

// Una fila de la tabla: la pregunta, cómo le fue a la búsqueda y, si se juzgó, a la respuesta. Al abrirla se ve el detalle.
function ResultRow({ result }: { result: EvalResult }) {
  const search = result.busqueda;
  const answer = result.respuesta;
  return (
    <details className="group border-t border-glass-border py-2">
      <summary className="grid cursor-pointer grid-cols-[1fr_auto_auto_auto] items-center gap-3 text-sm">
        <span className="min-w-0"><span className="font-mono text-xs text-muted-foreground">{result.tipo}</span> {result.pregunta}</span>
        <span className="flex items-center gap-1 font-mono text-xs" title="La búsqueda trajo una página correcta">
          <Mark ok={search ? search.hit_rate === 1 : undefined} /> {search ? `MRR ${search.mrr.toFixed(2)}` : 'trampa'}
        </span>
        <span className="flex items-center gap-1 font-mono text-xs" title="El juez la marcó como correcta (4 o más de 5)">
          <Mark ok={answer?.correcta} /> {answer?.correccion != null ? `${answer.correccion}/5` : ''}
        </span>
        <span className="flex items-center gap-1 text-xs" title="Fiel a los fragmentos"><Mark ok={answer?.fiel_a_los_fragmentos} /></span>
      </summary>
      <div className="mt-3 space-y-2 pl-2 text-xs">
        <p><span className="text-muted-foreground">Respuesta esperada:</span> {result.respuesta_esperada}</p>
        {search && (
          <p><span className="text-muted-foreground">Páginas esperadas:</span> {search.paginas_esperadas.join(' · ')}<br />
            <span className="text-muted-foreground">Páginas que llegaron al modelo:</span> {search.paginas_encontradas.join(' · ') || '—'}</p>
        )}
        {answer && (
          <>
            <p className="whitespace-pre-wrap rounded-lg border border-glass-border bg-background/40 p-2">{answer.respuesta}</p>
            {answer.correccion_explicacion && <p><span className="text-muted-foreground">El juez (corrección):</span> {answer.correccion_explicacion}</p>}
          </>
        )}
      </div>
    </details>
  );
}

// Una corrida de evals: cuándo y cómo se corrió, el resumen y la tabla pregunta por pregunta.
function EvalRunView({ item, open }: { item: EvalRun; open: boolean }) {
  return (
    <details open={open} className="rounded-xl border border-glass-border bg-background/40 p-4">
      <summary className="cursor-pointer font-medium">
        {when(item.carpeta)} · corte {item.request.splitter} · {item.request.candidatos} candidatos
        {item.request.respuestas ? ' · con respuestas' : ' · solo búsqueda'}
      </summary>
      <ul className="mt-3 list-disc pl-5 text-sm text-muted-foreground">{item.interpretacion.map(s => <li key={s}>{s}</li>)}</ul>
      <dl className="mt-3 grid grid-cols-2 gap-3 sm:grid-cols-3">
        {item.metricas.map(m => (
          <div key={m.label} className="rounded-lg border border-glass-border bg-background/40 p-3">
            <dt className="text-xs text-muted-foreground">{m.label}</dt>
            <dd className="mt-1 break-all font-mono text-sm">{m.value ?? '—'}</dd>
          </div>
        ))}
      </dl>
      <div className="mt-4 grid grid-cols-[1fr_auto_auto_auto] gap-3 text-xs text-muted-foreground">
        <span>Pregunta</span><span>Búsqueda</span><span>Correcta</span><span>Fiel</span>
      </div>
      {item.resultados.map(result => <ResultRow key={result.id} result={result} />)}
    </details>
  );
}

// La pestaña Evals: corre el set de preguntas contra la biblioteca (con los evaluadores nativos de LlamaIndex)
// y muestra las corridas guardadas, la más nueva primero.
export function LibraryEvals({ libraryId, runs, disabled, onDone }: { libraryId: string; runs: EvalRun[]; disabled: boolean; onDone: () => void }) {
  const [set, setSet] = useState('byma');
  const [withAnswers, setWithAnswers] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  // Corre los evals; si incluyen las respuestas, primero pide confirmación porque DeepSeek cobra.
  async function run() {
    if (withAnswers && !confirm('Con respuestas, el chat responde cada pregunta y DeepSeek la juzga: tiene costo (centavos de dólar). ¿Seguir?')) return;
    setBusy(true); setError('');
    try { await runEvals(libraryId, set, withAnswers); onDone(); }
    catch (e) { setError(e instanceof Error ? e.message : 'No se pudieron correr los evals.'); }
    finally { setBusy(false); }
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-3">
        <label className="flex items-center gap-2 text-sm">set
          <input className={`${INPUT} w-28`} value={set} disabled={busy} onChange={e => setSet(e.target.value)} />
        </label>
        <label className="flex items-center gap-2 text-sm">
          <input type="checkbox" checked={withAnswers} disabled={busy} onChange={e => setWithAnswers(e.target.checked)} />
          también las respuestas (juez DeepSeek)
        </label>
        <Button onClick={run} disabled={disabled || busy || !set.trim()}><FlaskConical /> {busy ? 'Corriendo…' : 'Correr evals'}</Button>
      </div>
      <p className="text-xs text-muted-foreground">
        Las preguntas están en <code>data/samples/{set}/evals/preguntas.json</code>. La búsqueda solo usa tokens de Voyage AI;
        con respuestas, además, el chat responde y DeepSeek juzga cada una. Puede tardar unos minutos.
      </p>
      {error && <p role="alert" className="text-sm text-destructive">{error}</p>}
      {runs.length === 0 && <p className="text-sm text-muted-foreground">Esta biblioteca todavía no tiene evals.</p>}
      {runs.map((item, i) => <EvalRunView key={item.carpeta} item={item} open={i === 0} />)}
    </div>
  );
}
