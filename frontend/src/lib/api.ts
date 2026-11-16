// Llama al backend y devuelve el JSON. Si hay error, lanza el mensaje que mandó el servidor.
export async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, init);
  if (!res.ok) throw new Error(await errorMessage(res));
  return res.json() as Promise<T>;
}

// Saca el mensaje de error del cuerpo { detail } o arma uno genérico.
async function errorMessage(res: Response) {
  try {
    const body = await res.json() as { detail?: unknown };
    if (typeof body.detail === 'string') return body.detail;
  } catch { /* sin cuerpo JSON */ }
  return `Error del servidor (${res.status}). Intentá de nuevo.`;
}

export type AppConfig = {
  documents: { ready: boolean; maxUploadMb: number; parseTier: string; parseVersion: string };
};
// Pide la configuración pública: qué pipelines están listos y con qué opciones.
export const getConfig = () => api<AppConfig>('/api/config');
