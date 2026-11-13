import { useEffect, useRef, useState } from 'react';
import { Download, Loader2, Pause, Play, RotateCcw } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Slider } from '@/components/ui/slider';

function formatTime(seconds: number) {
  const safe = Number.isFinite(seconds) ? Math.max(0, seconds) : 0;
  return `${Math.floor(safe / 60)}:${Math.floor(safe % 60).toString().padStart(2, '0')}`;
}

/** Reproductor grande (mismo diseño que el de la carta del fundador) para un audio ya generado. */
export function AudioPlayer({ src, title, badge, downloadName }: { src: string; title: string; badge?: string; downloadName?: string }) {
  const ref = useRef<HTMLAudioElement | null>(null);
  const [playing, setPlaying] = useState(false);
  const [loading, setLoading] = useState(false);
  const [time, setTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [error, setError] = useState(false);

  useEffect(() => {
    const audio = ref.current;
    return () => { audio?.pause(); };
  }, []);

  async function toggle() {
    const audio = ref.current;
    if (!audio) return;
    if (!audio.paused) { audio.pause(); return; }
    setError(false); setLoading(true);
    try {
      if (audio.ended) audio.currentTime = 0;
      await audio.play();
    } catch { setError(true); } finally { setLoading(false); }
  }

  function seek(value: number) {
    const audio = ref.current;
    if (!audio || !duration) return;
    audio.currentTime = Math.max(0, Math.min(value, duration));
    setTime(audio.currentTime);
  }

  return (
    <div className="w-full rounded-2xl border border-primary/40 bg-gradient-to-br from-primary/15 to-mint/5 p-5" role="group" aria-label={title}>
      <div className="mb-3 flex items-baseline justify-between gap-3">
        <p className="font-display text-base font-medium sm:text-lg">{title}</p>
        {badge && <span className="shrink-0 font-mono text-[11px] uppercase tracking-wider text-primary">{badge}</span>}
      </div>
      <audio
        ref={ref}
        src={src}
        preload="metadata"
        onPlay={event => {
          const cur = event.currentTarget;
          document.querySelectorAll('audio').forEach(other => { if (other !== cur) other.pause(); });
          setPlaying(true);
        }}
        onPause={() => setPlaying(false)}
        onEnded={() => setPlaying(false)}
        onTimeUpdate={event => setTime(event.currentTarget.currentTime)}
        onDurationChange={event => { const v = event.currentTarget.duration; if (Number.isFinite(v)) setDuration(v); }}
        onWaiting={() => setLoading(true)}
        onPlaying={() => setLoading(false)}
        onError={() => { setError(true); setLoading(false); setPlaying(false); }}
      />
      <div className="flex min-h-10 items-center gap-3">
        <Button type="button" size="icon" className={`size-12 shrink-0 rounded-full shadow-lg [&_svg]:size-5 ${playing ? '' : 'animate-pulse'}`}
          onClick={toggle} disabled={loading} aria-label={playing ? 'Pausar' : 'Reproducir'} title={playing ? 'Pausar' : 'Reproducir'}>
          {loading ? <Loader2 className="animate-spin" /> : playing ? <Pause /> : <Play />}
        </Button>
        <Slider min={0} max={duration || 1} step={0.1} value={[Math.min(time, duration)]}
          onValueChange={([value]) => { if (value !== undefined) seek(value); }} disabled={!duration}
          aria-label="Posición del audio" className="min-w-0 flex-1" />
        <span className="shrink-0 font-mono text-[11px] tabular-nums text-muted-foreground">{formatTime(time)} / {formatTime(duration)}</span>
        <Button type="button" variant="ghost" size="icon" className="size-8 shrink-0 text-muted-foreground" onClick={() => seek(0)}
          disabled={!duration} aria-label="Volver al inicio" title="Volver al inicio">
          <RotateCcw />
        </Button>
        {downloadName && <Button asChild variant="ghost" size="icon" className="size-8 shrink-0 text-muted-foreground">
          <a href={src} download={downloadName} aria-label="Descargar MP3" title="Descargar MP3"><Download /></a>
        </Button>}
      </div>
      {error && <p role="alert" className="mt-2 text-xs text-destructive">No se pudo reproducir. Probá de nuevo.</p>}
    </div>
  );
}
