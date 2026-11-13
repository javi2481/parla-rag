import { api, apiResponse } from '@/lib/api';

export type Lang = 'es' | 'en';
export type SpeechResult = { blob: Blob; credits: number | null; cached: boolean; characters: number };

/** Genera MP3 con la voz clonada. Devuelve también lo que cobró ElevenLabs (0 si vino de la caché). */
export async function speak(text: string): Promise<SpeechResult> {
  const res = await apiResponse('/api/audio/tts', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ text }) });
  const credits = res.headers.get('X-Credits');
  return {
    blob: await res.blob(),
    credits: credits === null ? null : Number(credits),
    cached: res.headers.get('X-Cache') === 'hit',
    characters: Number(res.headers.get('X-Characters') ?? 0),
  };
}

/** Transcribe con ElevenLabs Scribe y devuelve el texto crudo y el limpio (sin muletillas). */
export function transcribe(audio: Blob, lang: Lang, filename = 'audio.webm') {
  const form = new FormData();
  form.append('file', audio, filename);
  form.append('lang', lang);
  return api<{ raw: string; text: string }>('/api/audio/transcribe', { method: 'POST', body: form });
}
