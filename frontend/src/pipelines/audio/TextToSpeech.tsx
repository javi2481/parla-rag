import { useEffect, useState } from 'react';
import { AudioLines, Coins, LoaderCircle, Sparkles, Wand2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { AudioPlayer } from '@/pipelines/audio/AudioPlayer';
import { speak, type SpeechResult } from '@/pipelines/audio/api';

const SAMPLE = 'Buen día. Te cuento en treinta segundos cómo trabajamos: primero entendemos tu proceso, después lo automatizamos y, al final, medimos cuánto tiempo te ahorraste.';

// Sección Texto a voz: pegás un texto y lo escuchás con la voz clonada.
export function TextToSpeech({ ready, maxChars, model }: { ready: boolean; maxChars: number; model: string }) {
  const [text, setText] = useState('');
  const [audio, setAudio] = useState<{ url: string; info: SpeechResult } | null>(null);
  const [spent, setSpent] = useState(0);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => () => { if (audio) URL.revokeObjectURL(audio.url); }, [audio]);

  // Manda el texto a ElevenLabs y prepara el reproductor con el resultado.
  async function generate() {
    if (!text.trim() || busy || !ready) return;
    setBusy(true); setError('');
    try {
      const info = await speak(text);
      setAudio({ url: URL.createObjectURL(info.blob), info });
      setSpent(s => s + (info.credits ?? 0));
    } catch (e) { setError(e instanceof Error ? e.message : 'No se pudo generar el audio.'); }
    finally { setBusy(false); }
  }

  const ratio = text.length / maxChars;
  return (
    <div className="mt-10 grid grid-cols-1 items-start gap-6 lg:grid-cols-[minmax(0,1.4fr)_minmax(0,1fr)]">
      <section aria-label="Texto a convertir" className="rounded-2xl border border-glass-border bg-glass/60 p-4 sm:p-5">
        <div className="mb-3 flex items-center justify-between gap-3">
          <label htmlFor="tts-text" className="text-sm font-medium">Texto</label>
          <button type="button" onClick={() => setText(SAMPLE)} disabled={busy} className="flex items-center gap-1.5 text-xs text-muted-foreground transition-colors hover:text-primary">
            <Wand2 className="size-3.5" /> Probar con un ejemplo
          </button>
        </div>
        <Textarea id="tts-text" value={text} maxLength={maxChars} rows={9} disabled={!ready || busy}
          onChange={e => setText(e.target.value)}
          onKeyDown={e => { if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) void generate(); }}
          placeholder="Pegá o escribí el texto que querés escuchar…"
          className="min-h-48 resize-y border-glass-border bg-background/50 text-base leading-relaxed" />
        <div className="mt-2 h-1 overflow-hidden rounded-full bg-background/60">
          <div className={`h-full rounded-full transition-[width] ${ratio > 0.9 ? 'bg-destructive' : 'bg-primary/70'}`} style={{ width: `${Math.min(100, ratio * 100)}%` }} />
        </div>
        <div className="mt-3 flex flex-wrap items-center justify-between gap-3">
          <span className="font-mono text-xs text-muted-foreground">{text.length.toLocaleString('es-AR')} / {maxChars.toLocaleString('es-AR')} caracteres <span className="hidden sm:inline">· Ctrl+Enter</span></span>
          <Button onClick={generate} disabled={!ready || !text.trim() || busy} size="lg" className="rounded-full">
            {busy ? <LoaderCircle className="animate-spin motion-reduce:animate-none" /> : <AudioLines />}
            {busy ? 'Generando…' : 'Generar voz'}
          </Button>
        </div>
        {!ready && <p role="status" className="mt-3 text-sm text-muted-foreground">Falta configurar ELEVENLABS_API_KEY en el backend.</p>}
        {error && <p role="alert" className="mt-3 break-words text-sm text-destructive">{error}</p>}
      </section>

      <div className="space-y-4">
        {audio
          ? <div className="animate-rise space-y-3">
            <AudioPlayer key={audio.url} src={audio.url} title="Tu texto, con tu voz" badge={model} downloadName="voz.mp3" />
            <p className="flex items-center gap-2 text-xs text-muted-foreground">
              <Coins className="size-3.5 text-mint" />
              {audio.info.cached
                ? <>0 créditos: este texto ya estaba generado (caché).</>
                : audio.info.credits !== null ? <>Costó <b className="text-foreground">{audio.info.credits}</b> créditos por {audio.info.characters} caracteres.</> : <>Generado.</>}
            </p>
          </div>
          : <div className="grid min-h-48 place-items-center rounded-2xl border border-dashed border-glass-border p-6 text-center text-muted-foreground">
            <div><AudioLines className="mx-auto size-8 opacity-60" /><p className="mt-3 text-sm">El audio generado aparece acá</p></div>
          </div>}
        <aside className="rounded-2xl border border-glass-border bg-glass/40 p-4 text-xs text-muted-foreground">
          <p className="flex items-center gap-2 font-medium text-foreground"><Sparkles className="size-3.5 text-primary" /> Cómo ahorramos créditos</p>
          <ul className="mt-2 space-y-1.5">
            <li>· Modelo <b className="text-foreground">{model}</b>: la mitad de créditos por carácter que los modelos premium.</li>
            <li>· Se quitan markdown, links, emojis y viñetas antes de enviar: no se pagan.</li>
            <li>· Lo ya generado se guarda en disco y no se vuelve a cobrar.</li>
          </ul>
          {spent > 0 && <p className="mt-3 font-mono text-foreground">Esta sesión: {spent} créditos</p>}
        </aside>
      </div>
    </div>
  );
}
