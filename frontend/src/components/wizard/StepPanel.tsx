import type { ReactNode } from 'react';
import { CircleCheck, FileDown, LoaderCircle, Lock, Play, RotateCcw, TriangleAlert } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { JsonView } from './JsonView';

export type PanelStep = {
  number: number;
  title: string;
  explicacion: string;
  state: string;
  locked: boolean;
  job_status?: string;
  error?: string;
  request: unknown;
  metricas: { label: string; value: string | number | null }[];
  interpretacion: string[];
  files: { path: string; size: number }[];
};

// El panel de un paso, siempre con el mismo orden:
// qué hace · botón para correrlo · interpretación · métricas · resultado · qué se pidió · archivos.
// `children` es la vista del resultado propia de cada paso (por ejemplo el Markdown del parse).
export function StepPanel({ step, onStart, canStart = true, fileHref, children }: {
  step: PanelStep;
  onStart?: () => void;
  canStart?: boolean;
  fileHref: (path: string) => string;
  children?: ReactNode;
}) {
  const done = step.state === 'done';
  return (
    <section className="space-y-6 rounded-2xl border border-glass-border bg-glass/40 p-5 sm:p-6" aria-label={`Paso ${step.number}: ${step.title}`}>
      <header className="flex flex-wrap items-start justify-between gap-4">
        <div className="max-w-2xl">
          <p className="font-mono text-xs uppercase tracking-[0.2em] text-mint">Paso {step.number}</p>
          <h2 className="mt-1 font-display text-3xl">{step.title}</h2>
          <p className="mt-2 text-sm text-muted-foreground">{step.explicacion}</p>
        </div>
        <StepAction step={step} onStart={onStart} canStart={canStart} />
      </header>

      {step.state === 'failed' && (
        <p role="alert" className="flex items-center gap-2 rounded-lg border border-destructive/40 bg-destructive/10 p-3 text-sm text-destructive">
          <TriangleAlert className="size-4" /> {step.error}
        </p>
      )}

      {done && step.interpretacion.length > 0 && (
        <div className="rounded-xl border border-mint/30 bg-mint/5 p-4">
          <h3 className="mb-2 text-sm font-medium text-mint">Qué nos dice este resultado</h3>
          <ul className="list-disc space-y-1 pl-5 text-sm">
            {step.interpretacion.map(sentence => <li key={sentence}>{sentence}</li>)}
          </ul>
        </div>
      )}

      {done && step.metricas.length > 0 && (
        <dl className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
          {step.metricas.map(metric => (
            <div key={metric.label} className="rounded-lg border border-glass-border bg-background/40 p-3">
              <dt className="text-xs text-muted-foreground">{metric.label}</dt>
              <dd className="mt-1 break-all font-mono text-sm">{metric.value ?? '—'}</dd>
            </div>
          ))}
        </dl>
      )}

      {done && children}

      {step.request != null && (
        <details className="group">
          <summary className="cursor-pointer text-sm text-muted-foreground hover:text-foreground">Qué se le pidió a LlamaCloud</summary>
          <div className="mt-2"><JsonView data={step.request} /></div>
        </details>
      )}

      {step.files.length > 0 && (
        <details>
          <summary className="cursor-pointer text-sm text-muted-foreground hover:text-foreground">Archivos guardados ({step.files.length})</summary>
          <ul className="mt-2 grid gap-1 text-xs sm:grid-cols-2">
            {step.files.map(file => (
              <li key={file.path}>
                <a href={fileHref(file.path)} target="_blank" rel="noreferrer" className="flex items-center gap-2 font-mono text-muted-foreground hover:text-primary">
                  <FileDown className="size-3.5 shrink-0" /> {file.path} <span className="opacity-60">({formatSize(file.size)})</span>
                </a>
              </li>
            ))}
          </ul>
        </details>
      )}
    </section>
  );
}

// El botón o el estado del paso: bloqueado, listo para correr, corriendo, terminado (con opción de repetir).
function StepAction({ step, onStart, canStart }: { step: PanelStep; onStart?: () => void; canStart: boolean }) {
  if (step.locked) {
    return <span className="flex items-center gap-2 text-sm text-muted-foreground"><Lock className="size-4" /> Primero terminá el paso anterior</span>;
  }
  if (step.state === 'running') {
    return (
      <span className="flex items-center gap-2 text-sm text-primary">
        <LoaderCircle className="size-4 animate-spin" /> Corriendo en LlamaCloud · {step.job_status ?? 'PENDING'}
      </span>
    );
  }
  if (step.state === 'done') {
    return (
      <div className="flex items-center gap-3">
        <span className="flex items-center gap-2 text-sm text-mint"><CircleCheck className="size-5" /> Terminado</span>
        {onStart && <Button variant="outline" size="sm" onClick={onStart} disabled={!canStart}><RotateCcw /> Repetir</Button>}
      </div>
    );
  }
  if (!onStart) return null;
  return <Button onClick={onStart} disabled={!canStart}><Play /> Correr {step.title}</Button>;
}

// Pasa bytes a un texto corto: 2048 → "2.0 KB".
function formatSize(bytes: number) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}
