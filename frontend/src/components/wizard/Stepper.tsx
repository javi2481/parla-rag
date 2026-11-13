import { Check, Lock, LoaderCircle, X } from 'lucide-react';

export type StepperItem = { name: string; number: number; title: string; state: string; locked: boolean };

// Barra de pasos del wizard: cada paso muestra si está bloqueado (candado), corriendo (spinner),
// terminado (tilde verde) o con error (cruz). Al hacer clic se elige el paso para verlo.
export function Stepper({ steps, selected, onSelect }: { steps: StepperItem[]; selected: string; onSelect: (name: string) => void }) {
  return (
    <ol className="flex flex-wrap gap-2" aria-label="Pasos">
      {steps.map(step => (
        <li key={step.name}>
          <button
            type="button"
            onClick={() => onSelect(step.name)}
            aria-current={selected === step.name ? 'step' : undefined}
            className={`flex items-center gap-2 rounded-full border px-3 py-1.5 text-sm transition-colors
              ${selected === step.name ? 'border-primary bg-primary/15 text-foreground' : 'border-glass-border bg-glass/40 text-muted-foreground hover:text-foreground'}`}
          >
            <StepIcon state={step.state} locked={step.locked} number={step.number} />
            {step.title}
          </button>
        </li>
      ))}
    </ol>
  );
}

// El ícono de un paso según su estado.
function StepIcon({ state, locked, number }: { state: string; locked: boolean; number: number }) {
  const base = 'grid size-5 place-items-center rounded-full text-[11px]';
  if (state === 'done') return <span className={`${base} bg-mint text-background`}><Check className="size-3.5" /></span>;
  if (state === 'running') return <span className={`${base} text-primary`}><LoaderCircle className="size-4 animate-spin" /></span>;
  if (state === 'failed') return <span className={`${base} bg-destructive text-white`}><X className="size-3.5" /></span>;
  if (locked) return <span className={`${base} text-muted-foreground`}><Lock className="size-3.5" /></span>;
  return <span className={`${base} border border-glass-border`}>{number}</span>;
}
