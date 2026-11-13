import { useEffect, useRef, useState } from 'react';
import { Loader2, Pause, Play, RotateCcw } from 'lucide-react';
import { speak } from '@/pipelines/audio/api';

let current: HTMLAudioElement | null = null;

// Pasa segundos a formato m:ss.
function fmt(s: number) {
  if (!Number.isFinite(s) || s < 0) s = 0;
  return `${Math.floor(s / 60)}:${Math.floor(s % 60).toString().padStart(2, '0')}`;
}

const labels = { idle: 'Escuchar', playing: 'Pausar', loading: 'Generando…', error: 'No se pudo reproducir', restart: 'Volver al inicio', seek: 'Posición del audio' };

// Botón para escuchar un texto. Solo gasta créditos al hacer clic; si cambia el texto, se regenera.
export function ListenButton({ text, label = labels.idle, disabled }: { text: string; label?: string; disabled?: boolean }) {
  const [state, setState] = useState<'idle' | 'loading' | 'playing' | 'error'>('idle');
  const [time, setTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [ready, setReady] = useState(false);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const urlRef = useRef<string | null>(null);

  useEffect(() => () => {
    audioRef.current?.pause();
    if (urlRef.current) URL.revokeObjectURL(urlRef.current);
    audioRef.current = null; urlRef.current = null;
    setReady(false); setState('idle'); setTime(0); setDuration(0);
  }, [text]);

  // Genera el audio la primera vez; después solo reproduce o pausa.
  async function onClick() {
    if (state === 'playing') { audioRef.current?.pause(); return; }
    if (state === 'loading') return;
    try {
      if (!audioRef.current) {
        setState('loading');
        const url = URL.createObjectURL((await speak(text)).blob);
        urlRef.current = url;
        const a = new Audio(url);
        a.onended = () => setState('idle');
        a.onpause = () => setState(s => (s === 'playing' ? 'idle' : s));
        a.onplay = () => setState('playing');
        a.ontimeupdate = () => setTime(a.currentTime);
        a.onloadedmetadata = () => setDuration(a.duration);
        a.ondurationchange = () => setDuration(a.duration);
        audioRef.current = a;
        setReady(true);
      }
      if (current && current !== audioRef.current) current.pause();
      current = audioRef.current;
      if (audioRef.current.ended) audioRef.current.currentTime = 0;
      await audioRef.current.play();
      setState('playing');
    } catch {
      setState('error');
    }
  }

  // Salta a un segundo del audio.
  function seek(v: number) {
    const a = audioRef.current;
    if (!a) return;
    a.currentTime = v; setTime(v);
  }

  const Icon = state === 'loading' ? Loader2 : state === 'playing' ? Pause : Play;

  if (!ready) {
    return (
      <button type="button" onClick={onClick} disabled={disabled} aria-label={state === 'idle' ? label : labels[state]}
        className="inline-flex items-center gap-2 rounded-full border border-primary/40 bg-primary/10 px-3 py-1.5 text-xs font-medium text-foreground transition-colors hover:bg-primary/20 disabled:opacity-50">
        <span className="grid size-5 place-items-center rounded-full bg-primary text-primary-foreground">
          <Icon className={`size-3 ${state === 'loading' ? 'animate-spin' : ''}`} />
        </span>
        {state === 'idle' ? label : labels[state]}
      </button>
    );
  }

  return (
    <div className="flex w-full max-w-xs items-center gap-2 rounded-full border border-primary/40 bg-primary/10 px-2 py-1.5 text-xs text-foreground">
      <button type="button" onClick={onClick} aria-label={state === 'playing' ? labels.playing : label}
        className="grid size-6 shrink-0 place-items-center rounded-full bg-primary text-primary-foreground">
        <Icon className="size-3" />
      </button>
      <input type="range" min={0} max={duration || 0} step={0.1} value={Math.min(time, duration || 0)}
        onChange={e => seek(Number(e.target.value))} aria-label={labels.seek} className="h-1 min-w-0 flex-1 cursor-pointer accent-primary" />
      <span className="shrink-0 tabular-nums text-muted-foreground">{fmt(time)} / {fmt(duration)}</span>
      <button type="button" onClick={() => seek(0)} aria-label={labels.restart} title={labels.restart}
        className="grid size-6 shrink-0 place-items-center rounded-full text-muted-foreground hover:text-foreground">
        <RotateCcw className="size-3.5" />
      </button>
    </div>
  );
}
