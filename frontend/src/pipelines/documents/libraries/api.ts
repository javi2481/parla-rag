import { api } from '@/lib/api';

type Metric = { label: string; value: string | number | null };

// Un documento de la biblioteca: la corrida del wizard de donde salió y su metadata de identidad.
export type LibraryDocument = { run_id: string; name: string; file_id: string; directory_file_id: string; metadata: Record<string, unknown>; added_at: string };

// Un resultado de la búsqueda: el chunk, su score y de qué documento y páginas salió.
export type SearchResult = {
  content: string; score: number | null; rerank_score: number | null;
  metadata: Record<string, unknown> | null;
  static_fields: { page_range_start?: number | null; page_range_end?: number | null; chunk_index?: number | null } | null;
};
export type Search = { at: string; request: { query: string; top_k: number }; response: { results: SearchResult[] }; metricas: Metric[]; interpretacion: string[] };

// Un evento del chat, tal como lo manda LlamaCloud: texto, razonamiento, búsquedas que hizo el agente y lo que encontró.
export type ChatEvent = { type: string; content?: string; name?: string; arguments?: unknown; result?: unknown; call_id?: string;
  image_attachment?: { attachment_name: string; source_id: string } | null; usage?: Record<string, unknown>; error?: string | null };
export type Turn = { at: string; prompt: string; events: ChatEvent[]; summary?: { job_metadata?: Record<string, unknown> } | null };

// Una corrida de evals guardada (libraries/<id>/evals/<fecha>/): cómo se corrió, el resultado de cada pregunta y el resumen.
export type EvalResult = {
  id: string; tipo: string; pregunta: string; respuesta_esperada: string;
  busqueda?: { hit_rate: number; mrr: number; paginas_esperadas: string[]; paginas_encontradas: string[] };
  respuesta?: { respuesta: string; fiel_a_los_fragmentos: boolean; fidelidad_explicacion: string | null;
    correccion: number | null; correcta: boolean; correccion_explicacion: string | null };
};
export type EvalRun = {
  carpeta: string; resultados: EvalResult[]; metricas: Metric[]; interpretacion: string[];
  request: { conjunto: string; preguntas: number; candidatos: number; respuestas: boolean; splitter: string; juez: string | null };
};

export type Library = {
  id: string; name: string; created_at: string; description?: string;
  // engine "local": índice en nuestro servidor (LlamaIndex + Voyage AI). Sin engine: índice de LlamaCloud.
  // splitter: cómo se cortan las páginas en chunks ("pagina", "oraciones" o "markdown").
  engine?: string; embed_model?: string; rerank_model?: string; splitter?: string;
  directory_id?: string; index_id?: string; parse_configuration_id?: string;
  documents: LibraryDocument[]; needs_sync: boolean; chat_session_id?: string;
  steps: { sync: { state: string; started_at?: string; finished_at?: string; credits?: number; index_status?: string; error?: string; metricas?: Metric[]; interpretacion?: string[] } };
  searches: Search[]; turns: Turn[]; evals?: EvalRun[];
};

const BASE = '/api/documents/libraries';
const json = (body: unknown) => ({ method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });

export const listLibraries = () => api<Library[]>(BASE);
export const createLibrary = (name: string, description: string) => api<Library>(BASE, json({ name, description }));
export const getLibrary = (id: string) => api<Library>(`${BASE}/${id}`);
export const deleteLibrary = (id: string) => api<{ deleted: string }>(`${BASE}/${id}`, { method: 'DELETE' });
export const addDocument = (id: string, runId: string) => api<Library>(`${BASE}/${id}/documents`, json({ run_id: runId }));
export const removeDocument = (id: string, runId: string) => api<Library>(`${BASE}/${id}/documents/${runId}`, { method: 'DELETE' });
export const startSync = (id: string) => api<Library>(`${BASE}/${id}/sync`, { method: 'POST' });
export const checkSync = (id: string) => api<Library>(`${BASE}/${id}/sync`);
export const runEvals = (id: string, conjunto: string, respuestas: boolean) =>
  api<EvalRun>(`${BASE}/${id}/evals`, json({ conjunto, respuestas }));
export const search = (id: string, query: string, topK: number) => api<Search>(`${BASE}/${id}/search`, json({ query, top_k: topK }));

// Un turno de chat: va llamando a onEvent con cada evento a medida que llega (Server-Sent Events: líneas "data: {...}").
export async function chat(id: string, prompt: string, onEvent: (event: ChatEvent) => void) {
  const res = await fetch(`${BASE}/${id}/chat`, json({ prompt }));
  if (!res.ok || !res.body) throw new Error(`El chat respondió con un error (${res.status}).`);
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop() ?? '';
    for (const line of lines) {
      if (!line.startsWith('data:')) continue;
      try { onEvent(JSON.parse(line.slice(5).trim()) as ChatEvent); } catch { /* línea incompleta o no JSON */ }
    }
  }
}
