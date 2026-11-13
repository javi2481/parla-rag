import { Check, Trash2 } from 'lucide-react';

export type RunSummary = { id: string; name: string; created_at: string; total_credits: number; steps: { state: string }[] };

// Lista de corridas guardadas: nombre, fecha, pasos terminados y créditos. Se puede abrir o borrar cada una.
export function RunList({ runs, selected, onOpen, onDelete }: {
  runs: RunSummary[]; selected?: string; onOpen: (id: string) => void; onDelete: (id: string) => void;
}) {
  if (runs.length === 0) {
    return <p className="text-sm text-muted-foreground">Todavía no hay corridas. Subí un documento para empezar.</p>;
  }
  return (
    <ul className="divide-y divide-glass-border overflow-hidden rounded-xl border border-glass-border">
      {runs.map(run => {
        const done = run.steps.filter(step => step.state === 'done').length;
        return (
          <li key={run.id} className={`flex items-center gap-3 px-4 py-3 ${selected === run.id ? 'bg-primary/10' : 'bg-glass/30'}`}>
            <button type="button" onClick={() => onOpen(run.id)} className="min-w-0 flex-1 text-left">
              <span className="block truncate font-medium">{run.name}</span>
              <span className="block text-xs text-muted-foreground">
                {new Date(run.created_at).toLocaleString('es-AR', { dateStyle: 'short', timeStyle: 'short', hourCycle: 'h23' })} · <Check className="inline size-3" /> {done}/{run.steps.length} pasos · {run.total_credits} créditos
              </span>
            </button>
            <button
              type="button"
              onClick={() => { if (confirm(`¿Borrar la corrida "${run.name}"? También se borra en LlamaCloud.`)) onDelete(run.id); }}
              className="rounded-md p-2 text-muted-foreground hover:bg-destructive/10 hover:text-destructive"
              aria-label={`Borrar ${run.name}`}
            >
              <Trash2 className="size-4" />
            </button>
          </li>
        );
      })}
    </ul>
  );
}
