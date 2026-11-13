import { useEffect, useState } from 'react';
import { INPUT, RowsEditor, type Row } from '@/components/wizard/RowsEditor';
import { fetchJson, fileUrl, screenshotPath, type Step } from '../api';

export type Segment = { category: string; confidence_category: string; pages: number[] };
export type SplitOptionsValue = { categories: Row[]; allow_uncategorized: string };
type SplitRequest = { categories: Row[]; splitting_strategy?: { allow_uncategorized?: string } };

// Las opciones con las que arranca el editor: las de la última vez que se corrió el paso o las de por defecto.
export function initialSplitOptions(step: Step): SplitOptionsValue {
  const request = step.request as SplitRequest | null;
  const defaults = step.defaults as SplitOptionsValue;
  if (request?.categories) {
    return { categories: request.categories, allow_uncategorized: request.splitting_strategy?.allow_uncategorized ?? defaults.allow_uncategorized };
  }
  return defaults;
}

// Editor de las categorías de Split: nombre y descripción de cada una.
export function SplitOptions({ value, onChange, disabled }: { value: SplitOptionsValue; onChange: (v: SplitOptionsValue) => void; disabled: boolean }) {
  return (
    <div className="space-y-3">
      <p className="text-sm text-muted-foreground">
        Las categorías en las que se divide el documento. La descripción es lo que lee el modelo para decidir: cuanto más clara, mejor.
      </p>
      <RowsEditor rows={value.categories} onChange={categories => onChange({ ...value, categories })}
        keys={['name', 'description']} labels={['Categoría', 'Descripción']} disabled={disabled} />
      <label className="flex flex-wrap items-center gap-2 text-sm">
        Páginas que no encajan en ninguna categoría:
        <select className={`${INPUT} w-auto`} value={value.allow_uncategorized} disabled={disabled}
          onChange={e => onChange({ ...value, allow_uncategorized: e.target.value })}>
          <option value="include">mostrarlas como "sin categoría"</option>
          <option value="omit">dejarlas afuera</option>
          <option value="forbid">obligar a elegir una categoría</option>
        </select>
      </label>
    </div>
  );
}

// Resultado de Split: cada parte con su categoría, sus páginas (en miniatura) y su confianza.
export function SplitStep({ runId, step }: { runId: string; step: Step }) {
  const [segments, setSegments] = useState<Segment[]>([]);

  useEffect(() => {
    fetchJson<Segment[]>(runId, '3_split/segments.json').then(setSegments, () => setSegments([]));
  }, [runId, step.finished_at]);

  return (
    <div className="space-y-4">
      {segments.map((segment, index) => (
        <div key={index} className="rounded-xl border border-glass-border bg-background/40 p-3">
          <div className="flex flex-wrap items-baseline justify-between gap-2">
            <span className="font-mono text-sm">{segment.category}</span>
            <span className="text-xs text-muted-foreground">
              {segment.pages.length} {segment.pages.length === 1 ? 'página' : 'páginas'} · confianza {segment.confidence_category}
            </span>
          </div>
          <div className="mt-2 flex gap-2 overflow-x-auto pb-1">
            {segment.pages.map(page => (
              <a key={page} href={fileUrl(runId, screenshotPath(page))} target="_blank" rel="noreferrer" className="shrink-0 text-center text-xs text-muted-foreground">
                <img src={fileUrl(runId, screenshotPath(page))} alt={`Página ${page}`} loading="lazy" className="h-28 rounded border border-glass-border bg-white" />
                {page}
              </a>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
