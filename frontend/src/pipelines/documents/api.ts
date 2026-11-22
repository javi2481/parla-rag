import { api } from '@/lib/api';

// Un archivo guardado por un paso, con su ruta dentro de la corrida y su tamaño.
export type RunFile = { path: string; size: number };

// Un paso del wizard, tal como lo arma el backend (pipeline.describe_run).
export type Step = {
  number: number;
  name: string;
  title: string;
  explicacion: string;
  folder: string;
  locked: boolean;
  requires_title?: string | null; // el paso que tiene que terminar antes (por ejemplo, "Parse")
  state: 'pending' | 'running' | 'done' | 'failed';
  job_status?: string;
  started_at?: string;
  finished_at?: string;
  credits?: number | null;
  error?: string;
  file_id?: string;
  configuration_id?: string;
  request: unknown;
  defaults: Record<string, unknown> | null;
  metricas: { label: string; value: string | number | null }[];
  interpretacion: string[];
  files: RunFile[];
};

// Una corrida: un documento con todos sus pasos.
export type Run = { id: string; name: string; created_at: string; total_credits: number; steps: Step[] };

const BASE = '/api/documents/runs';

// Lista las corridas guardadas, de la más nueva a la más vieja.
export const listRuns = () => api<Run[]>(BASE);

// Sube un archivo y crea una corrida nueva (el paso 1 ya queda hecho).
export function createRun(file: File) {
  const form = new FormData();
  form.append('file', file);
  return api<Run>(BASE, { method: 'POST', body: form });
}

// Trae una corrida con todos sus pasos.
export const getRun = (runId: string) => api<Run>(`${BASE}/${runId}`);

// Arranca un paso (por ejemplo "split"), con las opciones elegidas en el wizard si las hay.
export function startStep(runId: string, step: string, options?: unknown) {
  return api<Run>(`${BASE}/${runId}/steps/${step}`, {
    method: 'POST',
    headers: options === undefined ? undefined : { 'Content-Type': 'application/json' },
    body: options === undefined ? undefined : JSON.stringify(options),
  });
}

// Consulta un paso que está corriendo. El backend le pregunta a LlamaCloud y devuelve la corrida actualizada.
export const checkStep = (runId: string, step: string) => api<Run>(`${BASE}/${runId}/steps/${step}`);

// Borra la corrida (la carpeta y lo que haya en LlamaCloud).
export const deleteRun = (runId: string) => api<{ deleted: string }>(`${BASE}/${runId}`, { method: 'DELETE' });

// Devuelve la URL para ver o descargar un archivo guardado en la corrida.
export function fileUrl(runId: string, path: string) {
  return `${BASE}/${runId}/files/${path.split('/').map(encodeURIComponent).join('/')}`;
}

// Trae el contenido de un archivo de texto guardado en la corrida (por ejemplo el .md).
export async function fetchText(runId: string, path: string) {
  const res = await fetch(fileUrl(runId, path));
  if (!res.ok) throw new Error('No se pudo leer el archivo.');
  return res.text();
}

// Trae un archivo JSON guardado en la corrida (por ejemplo los segmentos del Split).
export async function fetchJson<T>(runId: string, path: string): Promise<T> {
  return JSON.parse(await fetchText(runId, path)) as T;
}

// La ruta de la captura de una página, guardada por el paso Parse.
export const screenshotPath = (page: number) => `2_parse/images/page_${page}.jpg`;
