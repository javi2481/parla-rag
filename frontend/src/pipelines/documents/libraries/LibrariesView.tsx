import { useEffect, useState } from 'react';
import { CircleCheck, LoaderCircle, Plus, RefreshCw, Trash2, TriangleAlert } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { INPUT } from '@/components/wizard/RowsEditor';
import { listRuns, type Run } from '../api';
import { addDocument, checkSync, createLibrary, deleteLibrary, getLibrary, listLibraries, removeDocument, startSync, type Library } from './api';
import { LibraryChat } from './LibraryChat';
import { LibrarySearch } from './LibrarySearch';

// Cada cuánto se consulta la sincronización mientras corre.
const POLL_MS = 5000;

// Saca el mensaje de un error para mostrarlo.
const message = (e: unknown) => (e instanceof Error ? e.message : 'Algo salió mal. Intentá de nuevo.');

// Sección Bibliotecas: documentos relacionados con un índice compartido, una búsqueda de prueba y un chat.
export function LibrariesView({ ready }: { ready: boolean }) {
  const [libraries, setLibraries] = useState<Library[]>([]);
  const [library, setLibrary] = useState<Library | null>(null);
  const [runs, setRuns] = useState<Run[]>([]);
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => { refresh(); listRuns().then(setRuns, () => setRuns([])); }, []);

  // Mientras la sincronización corre, se consulta cada POLL_MS.
  useEffect(() => {
    if (!library || library.steps.sync.state !== 'running') return;
    const timer = setTimeout(() => checkSync(library.id).then(setLibrary, e => setError(message(e))), POLL_MS);
    return () => clearTimeout(timer);
  }, [library]);

  // Vuelve a pedir la lista de bibliotecas.
  async function refresh() {
    try { setLibraries(await listLibraries()); } catch (e) { setError(message(e)); }
  }

  // Corre una acción contra el backend mostrando la espera y el error, y actualiza la biblioteca abierta.
  async function act(action: () => Promise<Library | void>) {
    setBusy(true); setError('');
    try {
      const updated = await action();
      if (updated) setLibrary(updated);
      refresh();
    } catch (e) {
      setError(message(e));
    } finally {
      setBusy(false);
    }
  }

  const parsed = runs.filter(run => run.steps.find(s => s.name === 'parse')?.state === 'done');
  const available = parsed.filter(run => !library?.documents.some(doc => doc.run_id === run.id));
  const sync = library?.steps.sync;
  const syncing = sync?.state === 'running';

  return (
    <div className="mt-10 grid gap-8 lg:grid-cols-[18rem_1fr]">
      <aside className="space-y-4">
        <div className="space-y-2 rounded-xl border border-glass-border bg-glass/40 p-4">
          <h3 className="text-sm font-medium">Nueva biblioteca</h3>
          <input className={INPUT} value={name} placeholder="Nombre, por ejemplo BYMA 3T26" onChange={e => setName(e.target.value)} />
          <input className={INPUT} value={description} placeholder="Descripción (opcional)" onChange={e => setDescription(e.target.value)} />
          <Button size="sm" disabled={!ready || busy || !name.trim()}
            onClick={() => act(async () => { const created = await createLibrary(name, description); setName(''); setDescription(''); return created; })}>
            <Plus /> Crear
          </Button>
          <p className="text-xs text-muted-foreground">El índice se arma con el parse que ya hizo el wizard: no se vuelve a parsear nada.</p>
        </div>
        <h3 className="pt-2 text-sm font-medium text-muted-foreground">Bibliotecas</h3>
        <ul className="space-y-2">
          {libraries.map(item => (
            <li key={item.id}>
              <button type="button" onClick={() => act(() => getLibrary(item.id))}
                className={`w-full rounded-lg border px-3 py-2 text-left text-sm ${library?.id === item.id ? 'border-primary bg-primary/10' : 'border-glass-border bg-glass/40'}`}>
                <span className="block truncate">{item.name}</span>
                <span className="text-xs text-muted-foreground">{item.documents.length} documento(s)</span>
              </button>
            </li>
          ))}
        </ul>
      </aside>

      <div className="min-w-0 space-y-6">
        {error && <p role="alert" className="rounded-xl border border-destructive/40 bg-destructive/10 p-4 text-sm text-destructive">{error}</p>}
        {!library && <p className="text-muted-foreground">Creá una biblioteca o abrí una para sumarle documentos, buscar y chatear.</p>}
        {library && (
          <>
            <div className="flex flex-wrap items-baseline justify-between gap-2">
              <h2 className="truncate font-display text-2xl">{library.name}</h2>
              <Button variant="ghost" size="sm" disabled={busy}
                onClick={() => confirm(library.engine === 'local' ? '¿Borrar la biblioteca? Se borra su carpeta con el índice (las corridas no se tocan).' : '¿Borrar la biblioteca? Se borran su índice y su directorio en LlamaCloud (las corridas no se tocan).')
                  && act(async () => { await deleteLibrary(library.id); setLibrary(null); })}><Trash2 /> Borrar</Button>
            </div>
            <p className="font-mono text-xs text-muted-foreground">
              {library.engine === 'local'
                ? `índice local (LlamaIndex) · embeddings ${library.embed_model} · reranker ${library.rerank_model} (Voyage AI) · chat DeepSeek`
                : `LlamaCloud · directorio ${library.directory_id} · índice ${library.index_id}`}
            </p>

            <section className="space-y-3 rounded-2xl border border-glass-border bg-glass/40 p-5">
              <h3 className="font-medium">Documentos</h3>
              {library.documents.length === 0 && <p className="text-sm text-muted-foreground">Todavía no tiene documentos.</p>}
              <ul className="space-y-2">
                {library.documents.map(doc => (
                  <li key={doc.run_id} className="flex flex-wrap items-start justify-between gap-2 rounded-lg border border-glass-border bg-background/40 p-3">
                    <div className="min-w-0">
                      <p className="truncate text-sm">{doc.name}</p>
                      <p className="mt-1 flex flex-wrap gap-1">
                        {Object.entries(doc.metadata).filter(([k]) => k !== 'nombre' && k !== 'corrida').map(([k, v]) => (
                          <span key={k} className="rounded-full border border-glass-border px-2 py-0.5 font-mono text-xs text-muted-foreground">{k}: {String(v)}</span>
                        ))}
                      </p>
                    </div>
                    <Button variant="ghost" size="icon" aria-label="Sacar" disabled={busy || syncing} onClick={() => act(() => removeDocument(library.id, doc.run_id))}><Trash2 /></Button>
                  </li>
                ))}
              </ul>
              <div className="flex flex-wrap items-center gap-2">
                <select className={`${INPUT} w-auto max-w-full`} disabled={busy || syncing || available.length === 0} defaultValue=""
                  onChange={e => { const runId = e.target.value; e.target.value = ''; if (runId) act(() => addDocument(library.id, runId)); }}>
                  <option value="">{available.length ? 'Agregar una corrida del wizard (con Parse terminado)…' : 'No hay más corridas con Parse terminado'}</option>
                  {available.map(run => <option key={run.id} value={run.id}>{run.name} · {run.id.slice(0, 17)}</option>)}
                </select>
              </div>
              <p className="text-xs text-muted-foreground">La metadata sale de la corrida: el tipo de Classify y los datos de identidad de Extract. Sirve para filtrar las búsquedas.</p>
            </section>

            <section className="space-y-3 rounded-2xl border border-glass-border bg-glass/40 p-5">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <h3 className="font-medium">Índice</h3>
                {syncing
                  ? <span className="flex items-center gap-2 text-sm text-primary"><LoaderCircle className="size-4 animate-spin" /> Sincronizando · {sync?.index_status ?? '…'}</span>
                  : <Button size="sm" disabled={busy || library.documents.length === 0 && !library.needs_sync} onClick={() => act(() => startSync(library.id))}><RefreshCw /> Sincronizar</Button>}
              </div>
              {library.needs_sync && !syncing && (
                <p className="flex items-center gap-2 text-sm text-amber-400"><TriangleAlert className="size-4" /> Cambiaron los documentos: hay que sincronizar para que el índice los tenga.</p>
              )}
              {sync?.state === 'done' && <p className="flex items-center gap-2 text-sm text-mint"><CircleCheck className="size-4" /> Sincronizado</p>}
              {sync?.state === 'failed' && <p className="text-sm text-destructive">{sync.error}</p>}
              {sync?.interpretacion && (
                <ul className="list-disc pl-5 text-sm">{sync.interpretacion.map(s => <li key={s}>{s}</li>)}</ul>
              )}
              {sync?.metricas && (
                <dl className="grid grid-cols-2 gap-3 sm:grid-cols-3">
                  {sync.metricas.map(m => (
                    <div key={m.label} className="rounded-lg border border-glass-border bg-background/40 p-3">
                      <dt className="text-xs text-muted-foreground">{m.label}</dt>
                      <dd className="mt-1 break-all font-mono text-sm">{m.value ?? '—'}</dd>
                    </div>
                  ))}
                </dl>
              )}
            </section>

            <Tabs defaultValue="chat">
              <TabsList>
                <TabsTrigger value="chat">Chat</TabsTrigger>
                <TabsTrigger value="buscar">Búsqueda de prueba</TabsTrigger>
              </TabsList>
              <TabsContent value="chat" className="mt-4">
                <LibraryChat libraryId={library.id} turns={library.turns} disabled={syncing || sync?.state !== 'done'} local={library.engine === 'local'}
                  onDone={() => getLibrary(library.id).then(setLibrary)} />
              </TabsContent>
              <TabsContent value="buscar" className="mt-4">
                <LibrarySearch libraryId={library.id} searches={library.searches} disabled={syncing || sync?.state !== 'done'}
                  onDone={() => getLibrary(library.id).then(setLibrary)} />
              </TabsContent>
            </Tabs>
          </>
        )}
      </div>
    </div>
  );
}
