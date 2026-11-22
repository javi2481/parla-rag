import { useCallback, useEffect, useState } from 'react';
import { LoaderCircle } from 'lucide-react';
import { listRuns, type Run } from '@/pipelines/documents/api';
import { closeConversation, createConversation, getLibrary, listConversations, listLibraries,
  type Conversation, type Library } from '@/pipelines/documents/libraries/api';
import { ChatFilters, SIN_FILTROS, type Filtros } from './ChatFilters';
import { ChatThread } from './ChatThread';
import { ConversationTabs } from './ConversationTabs';
import { ProjectJourney, type NumerosDelRecorrido } from './ProjectJourney';

// La biblioteca del chat: la local con la sincronización terminada más reciente (hay una sola, así que no hay selector).
function bibliotecaDelChat(libraries: Library[]): Library | undefined {
  return libraries
    .filter(l => l.engine === 'local' && l.steps.sync.state === 'done')
    .sort((a, b) => (b.steps.sync.finished_at ?? '').localeCompare(a.steps.sync.finished_at ?? ''))[0];
}

// Busca un número en las métricas de la última sincronización (por ejemplo, "Chunks").
function metrica(library: Library, label: string) {
  return library.steps.sync.metricas?.find(m => m.label === label)?.value ?? null;
}

// Arma el número de cada caja del recorrido con datos de la API. Si la API no lo informa, la caja queda sin número.
function numerosDe(library: Library, runs: Run[]): NumerosDelRecorrido {
  const ids = new Set(library.documents.map(d => d.run_id));
  const corridas = runs.filter(r => ids.has(r.id));
  const paginas = library.documents.reduce((total, d) => total + (d.pages ?? 0), 0);
  const creditos = corridas.reduce((total, r) => total + r.total_credits, 0);
  const chunks = metrica(library, 'Chunks');
  // El modelo que respondió sale del último turno guardado (evento "stop"); sin turnos todavía no se sabe.
  const ultimoStop = library.turns.at(-1)?.events.findLast(e => e.type === 'stop');
  const modelo = ultimoStop?.usage?.modelo;
  return {
    pdf: `${library.documents.length} documentos · ${paginas} páginas`,
    parse: corridas.length ? `${creditos.toLocaleString('es-AR')} créditos en ${corridas.length} corridas` : null,
    chunks: chunks !== null ? `${chunks} chunks` : null,
    voyage: [library.embed_model, library.rerank_model].filter(Boolean).join(' · ') || null,
    openai: typeof modelo === 'string' ? modelo : null,
  };
}

// La página principal: el recorrido fijo arriba y, abajo, la conversación con la biblioteca de la materia.
// Si todavía no hay ninguna biblioteca sincronizada, lo dice y manda a la pestaña Bibliotecas.
export function ChatPage() {
  const [library, setLibrary] = useState<Library | null>(null);
  const [runs, setRuns] = useState<Run[]>([]);
  const [state, setState] = useState<'cargando' | 'lista' | 'sin-biblioteca'>('cargando');
  const [error, setError] = useState('');
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [active, setActive] = useState<string | null>(null);
  const [filtros, setFiltros] = useState<Filtros>(SIN_FILTROS);
  const [busy, setBusy] = useState(false);

  // Vuelve a pedir la biblioteca (con sus turnos) y las corridas; se usa al cargar y después de cada respuesta.
  const cargar = useCallback(async () => {
    try {
      const [libraries, allRuns] = await Promise.all([listLibraries(), listRuns()]);
      const elegida = bibliotecaDelChat(libraries);
      if (!elegida) { setState('sin-biblioteca'); return; }
      setLibrary(await getLibrary(elegida.id));
      setRuns(allRuns);
      setState('lista');
    } catch (e) {
      setError(e instanceof Error ? e.message : 'No se pudo cargar la biblioteca.');
    }
  }, []);

  useEffect(() => { void cargar(); }, [cargar]);

  // Al tener la biblioteca, abre las mismas pestañas que había (la activa es la última). Si no hay ninguna, crea una.
  const libraryId = library?.id;
  useEffect(() => {
    if (!libraryId) return;
    (async () => {
      let abiertas = await listConversations(libraryId);
      if (!abiertas.length) abiertas = [await createConversation(libraryId)];
      setConversations(abiertas);
      setActive(actual => abiertas.some(c => c.id === actual) ? actual : abiertas.at(-1)!.id);
    })().catch(e => setError(e instanceof Error ? e.message : 'No se pudieron cargar las conversaciones.'));
  }, [libraryId]);

  // El "+": crea una conversación vacía y la deja activa.
  async function nueva() {
    if (!libraryId) return;
    try {
      const creada = await createConversation(libraryId);
      setConversations(previas => [...previas, creada]);
      setActive(creada.id);
    } catch (e) { setError(e instanceof Error ? e.message : 'No se pudo crear la conversación.'); }
  }

  // La "×": cierra la conversación (queda en disco) y pasa a la de al lado; si era la última, crea una nueva.
  async function cerrar(id: string) {
    if (!libraryId) return;
    try {
      await closeConversation(libraryId, id);
      const quedan = conversations.filter(c => c.id !== id);
      if (!quedan.length) quedan.push(await createConversation(libraryId));
      setConversations(quedan);
      if (active === id) setActive(quedan.at(-1)!.id);
    } catch (e) { setError(e instanceof Error ? e.message : 'No se pudo cerrar la conversación.'); }
  }

  // Después de cada respuesta: actualiza los títulos de las pestañas y los números del recorrido (por ejemplo, el modelo).
  async function alResponder() {
    if (!libraryId) return;
    try {
      setConversations(await listConversations(libraryId));
      setLibrary(await getLibrary(libraryId));
    } catch { /* los números se actualizan en la próxima carga */ }
  }

  if (error) return <p role="alert" className="mt-8 rounded-xl border border-destructive/40 bg-destructive/10 p-4 text-sm text-destructive">{error}</p>;
  if (state === 'cargando') return <p className="mt-8 flex items-center gap-2 text-sm text-muted-foreground"><LoaderCircle className="size-4 animate-spin" /> Cargando la biblioteca…</p>;
  if (state === 'sin-biblioteca' || !library) {
    return (
      <div className="mt-8 rounded-2xl border border-glass-border bg-glass/40 p-6 text-sm">
        <p>Todavía no hay ninguna biblioteca sincronizada para chatear.</p>
        <p className="mt-2 text-muted-foreground">Armá una en <a href="#bibliotecas" className="text-primary underline">Bibliotecas</a>: sumá las corridas del wizard y sincronizá el índice.</p>
      </div>
    );
  }

  return (
    <div className="mt-8 flex flex-col gap-6">
      <ProjectJourney numeros={numerosDe(library, runs)} />
      <p className="text-sm text-muted-foreground">Chateás con <strong className="text-foreground">{library.name}</strong>.</p>
      <ConversationTabs conversations={conversations} active={active} disabled={busy}
        onSelect={setActive} onCreate={() => void nueva()} onClose={id => void cerrar(id)} />
      <ChatFilters documents={library.documents} value={filtros} onChange={setFiltros} disabled={busy} />
      {active && <ChatThread libraryId={library.id} conversationId={active} filtros={filtros} busy={busy}
        onBusyChange={setBusy} onDone={() => void alResponder()} />}
    </div>
  );
}
