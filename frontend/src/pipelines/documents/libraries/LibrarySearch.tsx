import { useState } from 'react';
import { Search as SearchIcon } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { INPUT } from '@/components/wizard/RowsEditor';
import { fileUrl, screenshotPath } from '../api';
import { search, type Search } from './api';

// Una búsqueda guardada: la pregunta, la interpretación y cada chunk con su score, su documento, sus páginas y la captura.
function SearchView({ item }: { item: Search }) {
  return (
    <div className="space-y-3 rounded-xl border border-glass-border bg-background/40 p-4">
      <p className="font-medium">«{item.request.query}»</p>
      <ul className="list-disc pl-5 text-sm text-muted-foreground">{item.interpretacion.map(s => <li key={s}>{s}</li>)}</ul>
      {item.response.results.map((result, i) => {
        const runId = result.metadata?.corrida as string | undefined;
        const page = result.static_fields?.page_range_start;
        const end = result.static_fields?.page_range_end;
        return (
          <div key={i} className="grid gap-3 border-t border-glass-border pt-3 sm:grid-cols-[6rem_1fr]">
            {runId && page ? (
              <a href={fileUrl(runId, screenshotPath(page))} target="_blank" rel="noreferrer">
                <img src={fileUrl(runId, screenshotPath(page))} alt={`Página ${page}`} loading="lazy" className="w-24 rounded border border-glass-border bg-white" />
              </a>
            ) : <span />}
            <div className="min-w-0 space-y-1">
              <p className="font-mono text-xs text-muted-foreground">
                #{i + 1} · {String(result.metadata?.nombre ?? 'documento')} · {page ? `pág. ${page}${end && end !== page ? `-${end}` : ''}` : 'sin página'}
                {' · '}score {result.score?.toFixed(3) ?? '—'} · rerank {result.rerank_score?.toFixed(3) ?? '—'}
              </p>
              <p className="max-h-40 overflow-auto whitespace-pre-wrap text-xs">{result.content}</p>
            </div>
          </div>
        );
      })}
    </div>
  );
}

// La búsqueda de prueba: muestra qué chunks recuperaría el chat para una pregunta, sin gastar un turno de chat.
export function LibrarySearch({ libraryId, searches, disabled, onDone }: { libraryId: string; searches: Search[]; disabled: boolean; onDone: () => void }) {
  const [query, setQuery] = useState('');
  const [topK, setTopK] = useState(8);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  // Busca y vuelve a cargar la biblioteca para ver la búsqueda guardada.
  async function run() {
    if (!query.trim()) return;
    setBusy(true); setError('');
    try { await search(libraryId, query, topK); onDone(); setQuery(''); }
    catch (e) { setError(e instanceof Error ? e.message : 'No se pudo buscar.'); }
    finally { setBusy(false); }
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-2">
        <input className={`${INPUT} min-w-60 flex-1`} value={query} disabled={disabled || busy} placeholder="¿Qué querés encontrar?"
          onChange={e => setQuery(e.target.value)} onKeyDown={e => e.key === 'Enter' && run()} />
        <label className="flex items-center gap-2 text-sm">resultados
          <input type="number" min={1} max={50} className={`${INPUT} w-20`} value={topK} onChange={e => setTopK(Number(e.target.value))} />
        </label>
        <Button onClick={run} disabled={disabled || busy || !query.trim()}><SearchIcon /> Buscar</Button>
      </div>
      <p className="text-xs text-muted-foreground">Cada búsqueda cuesta 1 crédito según la lista de precios de LlamaCloud.</p>
      {error && <p role="alert" className="text-sm text-destructive">{error}</p>}
      {searches.map(item => <SearchView key={item.at} item={item} />)}
    </div>
  );
}
