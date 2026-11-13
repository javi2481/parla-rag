/** Llamadas al backend FastAPI. Los errores llegan como { detail } y se muestran tal cual. */
export async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, init);
  if (!res.ok) throw new Error(await errorMessage(res));
  return res.json() as Promise<T>;
}

export async function apiResponse(path: string, init?: RequestInit): Promise<Response> {
  const res = await fetch(path, init);
  if (!res.ok) throw new Error(await errorMessage(res));
  return res;
}

async function errorMessage(res: Response) {
  try {
    const body = await res.json() as { detail?: unknown };
    if (typeof body.detail === 'string') return body.detail;
  } catch { /* sin cuerpo JSON */ }
  return `Error del servidor (${res.status}). Intentá de nuevo.`;
}

export type AppConfig = {
  invoice: { ready: boolean; fields: Record<string, string>; maxBytes: number; maxPages: number; dailyLimit: number; tier: string };
  audio: { ready: boolean; ttsMaxChars: number; ttsModel: string; sttModel: string; sttMaxSeconds: number };
};
export const getConfig = () => api<AppConfig>('/api/config');
