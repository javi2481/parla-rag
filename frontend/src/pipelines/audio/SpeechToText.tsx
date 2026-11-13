import { useEffect, useRef, useState } from 'react';
import { Check, Copy, FileAudio, LoaderCircle, Mic, Square } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Dropzone } from '@/components/Dropzone';
import { transcribe, type Lang } from '@/pipelines/audio/api';

const MAX_BYTES = 10 * 1024 * 1024;
const BARS = 32;
// Pasa segundos a formato m:ss.
const fmt = (s: number) => `${Math.floor(s / 60)}:${(s % 60).toString().padStart(2, '0')}`;

// Sección Voz a texto: grabás o subís un audio y obtenés la transcripción limpia.
export function SpeechToText({ ready, maxSeconds }: { ready: boolean; maxSeconds: number }) {
  const [lang, setLang] = useState<Lang>('es');
  const [recording, setRecording] = useState(false);
  const [seconds, setSeconds] = useState(0);
  const [levels, setLevels] = useState<number[]>(() => Array(BARS).fill(0));
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState<{ raw: string; text: string } | null>(null);
  const [copied, setCopied] = useState(false);
  const recorder = useRef<MediaRecorder | null>(null);
  const audioCtx = useRef<AudioContext | null>(null);

  // Cronómetro + corte automático: Scribe cobra por minuto de audio.
  useEffect(() => {
    if (!recording) return;
    const began = Date.now();
    const id = setInterval(() => {
      const s = Math.floor((Date.now() - began) / 1000);
      setSeconds(s);
      if (s >= maxSeconds) recorder.current?.stop();
    }, 250);
    return () => clearInterval(id);
  }, [recording, maxSeconds]);
  useEffect(() => () => { recorder.current?.stream.getTracks().forEach(t => t.stop()); void audioCtx.current?.close(); }, []);

  // Manda el audio a transcribir y muestra el resultado.
  async function send(blob: Blob, name: string) {
    if (blob.size > MAX_BYTES) { setError('El audio debe pesar hasta 10 MB.'); return; }
    setBusy(true); setError(''); setResult(null); setCopied(false);
    try { setResult(await transcribe(blob, lang, name)); }
    catch (e) { setError(e instanceof Error ? e.message : 'No se pudo transcribir el audio.'); }
    finally { setBusy(false); }
  }

  // Mide el volumen del micrófono para animar el indicador mientras se graba.
  function meter(stream: MediaStream) {
    const ctx = new AudioContext();
    audioCtx.current = ctx;
    const analyser = ctx.createAnalyser();
    analyser.fftSize = 512;
    ctx.createMediaStreamSource(stream).connect(analyser);
    const buf = new Uint8Array(analyser.fftSize);
    let last = 0;
    // Se llama en cada cuadro de animación: lee el volumen y lo muestra.
    const tick = (t: number) => {
      if (ctx.state === 'closed') return;
      if (t - last > 70) {
        last = t;
        analyser.getByteTimeDomainData(buf);
        let sum = 0;
        for (const v of buf) sum += ((v - 128) / 128) ** 2;
        const rms = Math.min(1, Math.sqrt(sum / buf.length) * 4);
        setLevels(l => [...l.slice(1), rms]);
      }
      requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
  }

  // Empieza o termina la grabación con el micrófono.
  async function toggleRecording() {
    if (recording) { recorder.current?.stop(); return; }
    setError('');
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: { echoCancellation: true, noiseSuppression: true } });
      const rec = new MediaRecorder(stream);
      const chunks: Blob[] = [];
      rec.ondataavailable = e => { if (e.data.size) chunks.push(e.data); };
      rec.onstop = () => {
        stream.getTracks().forEach(t => t.stop());
        void audioCtx.current?.close();
        setRecording(false); setLevels(Array(BARS).fill(0));
        const type = rec.mimeType || 'audio/webm';
        void send(new Blob(chunks, { type }), type.includes('mp4') ? 'grabacion.m4a' : type.includes('ogg') ? 'grabacion.ogg' : 'grabacion.webm');
      };
      recorder.current = rec;
      rec.start();
      meter(stream);
      setSeconds(0); setRecording(true);
    } catch { setError('No se pudo acceder al micrófono. Revisá los permisos del navegador.'); }
  }

  // Copia la transcripción al portapapeles.
  async function copy() {
    if (!result) return;
    await navigator.clipboard.writeText(result.text);
    setCopied(true); setTimeout(() => setCopied(false), 1500);
  }

  const disabled = !ready || busy;
  const left = maxSeconds - seconds;
  return (
    <div className="mt-10 space-y-6">
      <section aria-label="Audio a transcribir" className="grid grid-cols-1 gap-4 rounded-2xl border border-glass-border bg-glass/60 p-4 sm:p-5 lg:grid-cols-[minmax(0,1.1fr)_minmax(0,1fr)]">
        <div className={`flex flex-col justify-between gap-4 rounded-xl border p-4 transition-colors ${recording ? 'border-destructive/50 bg-destructive/5' : 'border-glass-border bg-background/40'}`}>
          <div className="flex items-center justify-between gap-3">
            <div>
              <p className="font-medium">{recording ? 'Grabando…' : 'Grabar con el micrófono'}</p>
              <p className="text-xs text-muted-foreground">{recording ? `Se corta sola en ${fmt(Math.max(0, left))}` : `Hasta ${fmt(maxSeconds)} por grabación`}</p>
            </div>
            <LangSwitch lang={lang} onChange={setLang} disabled={busy || recording} />
          </div>
          <div className="flex h-12 items-center gap-[3px]" aria-hidden="true">
            {levels.map((v, i) => <span key={i} className={`flex-1 rounded-full transition-[height] duration-75 ${recording ? 'bg-destructive/80' : 'bg-muted-foreground/25'}`} style={{ height: `${Math.max(8, v * 100)}%` }} />)}
          </div>
          <Button onClick={toggleRecording} disabled={disabled} size="lg" variant={recording ? 'destructive' : 'default'} className="rounded-full">
            {recording ? <Square /> : <Mic />}
            {recording ? `Detener · ${fmt(seconds)}` : 'Empezar a grabar'}
          </Button>
        </div>
        <div className="flex flex-col justify-center gap-3">
          <Dropzone id="stt-file" accept="audio/*,.webm" disabled={disabled || recording} onFile={f => void send(f, f.name)}
            icon={FileAudio} title="O soltá un archivo de audio" hint="MP3, M4A, WAV, OGG o WebM · hasta 10 MB" />
          {busy && <p className="flex items-center gap-2 text-sm text-primary" aria-live="polite"><LoaderCircle className="size-4 animate-spin motion-reduce:animate-none" /> Transcribiendo con Scribe…</p>}
          {!ready && <p role="status" className="text-sm text-muted-foreground">Falta configurar ELEVENLABS_API_KEY en el backend.</p>}
          {error && <p role="alert" className="break-words text-sm text-destructive">{error}</p>}
        </div>
      </section>

      {result
        ? <div className="grid grid-cols-1 animate-rise items-start gap-6 lg:grid-cols-[minmax(0,1.4fr)_minmax(0,1fr)]">
          <section aria-labelledby="stt-clean" className="rounded-2xl border border-glass-border bg-glass/60 p-5">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <h2 id="stt-clean" className="flex items-center gap-2 text-lg font-semibold"><span className="size-2 rounded-full bg-mint" /> Transcripción limpia</h2>
              <Button variant="outline" size="sm" onClick={copy} disabled={!result.text} className="rounded-full">{copied ? <Check /> : <Copy />} {copied ? 'Copiado' : 'Copiar'}</Button>
            </div>
            <p className="mt-4 whitespace-pre-wrap break-words font-display text-2xl leading-snug">{result.text || 'No se detectó voz en el audio.'}</p>
          </section>
          <section aria-labelledby="stt-raw" className="rounded-2xl border border-dashed border-glass-border p-5">
            <h2 id="stt-raw" className="text-sm font-medium text-muted-foreground">Lo que se escuchó, tal cual</h2>
            <p className="mt-3 whitespace-pre-wrap break-words text-sm text-muted-foreground">{result.raw || '—'}</p>
            <p className="mt-4 text-xs text-muted-foreground/80">Quitamos «eh», «mmm», tartamudeos, palabras repetidas y etiquetas como [tos].</p>
          </section>
        </div>
        : <div className="grid min-h-40 place-items-center rounded-2xl border border-dashed border-glass-border text-center text-muted-foreground">
          <div><Mic className="mx-auto size-8 opacity-60" /><p className="mt-3 text-sm">Grabá o subí un audio para ver la transcripción acá</p></div>
        </div>}
    </div>
  );
}

// Selector de idioma del audio: español o inglés.
function LangSwitch({ lang, onChange, disabled }: { lang: Lang; onChange: (l: Lang) => void; disabled?: boolean }) {
  return (
    <div role="radiogroup" aria-label="Idioma del audio" className="flex shrink-0 rounded-full border border-glass-border bg-background/50 p-0.5 text-xs">
      {(['es', 'en'] as const).map(l => (
        <button key={l} type="button" role="radio" aria-checked={lang === l} onClick={() => onChange(l)} disabled={disabled}
          className={`rounded-full px-2.5 py-1 font-medium transition-colors ${lang === l ? 'bg-primary text-primary-foreground' : 'text-muted-foreground hover:text-foreground'}`}>
          {l.toUpperCase()}
        </button>
      ))}
    </div>
  );
}
