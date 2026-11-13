import { useEffect, useState } from 'react';
import { RowsEditor, type Row } from '@/components/wizard/RowsEditor';
import { fetchJson, type Step } from '../api';

export type ClassifyOptionsValue = { rules: Row[] };
type ClassifyResult = { type: string | null; confidence: number | null; reasoning: string | null };

// Las reglas con las que arranca el editor: las de la última vez o las de por defecto.
export function initialClassifyOptions(step: Step): ClassifyOptionsValue {
  const request = step.request as ClassifyOptionsValue | null;
  return { rules: request?.rules ?? (step.defaults as ClassifyOptionsValue).rules };
}

// Editor de las reglas de Classify: el tipo y su descripción.
export function ClassifyOptions({ value, onChange, disabled }: { value: ClassifyOptionsValue; onChange: (v: ClassifyOptionsValue) => void; disabled: boolean }) {
  return (
    <div className="space-y-3">
      <p className="text-sm text-muted-foreground">Los tipos de documento posibles. El modelo elige uno según las descripciones.</p>
      <RowsEditor rows={value.rules} onChange={rules => onChange({ rules })} keys={['type', 'description']} labels={['Tipo', 'Descripción']} disabled={disabled} />
    </div>
  );
}

// Resultado de Classify: el tipo elegido, la confianza y el razonamiento del modelo, tal cual.
export function ClassifyStep({ runId, step }: { runId: string; step: Step }) {
  const [result, setResult] = useState<ClassifyResult | null>(null);

  useEffect(() => {
    fetchJson<ClassifyResult>(runId, '4_classify/result.json').then(setResult, () => setResult(null));
  }, [runId, step.finished_at]);

  if (!result) return null;
  return (
    <div className="space-y-3 rounded-xl border border-glass-border bg-background/40 p-4">
      <p className="text-sm text-muted-foreground">Tipo elegido</p>
      <p className="font-display text-2xl">
        {result.type ?? 'ninguno'}
        {result.confidence != null && <span className="ml-3 font-mono text-base text-mint">{Math.round(result.confidence * 100)}%</span>}
      </p>
      {result.reasoning && (
        <blockquote className="border-l-2 border-primary/60 pl-3 text-sm whitespace-pre-wrap">{result.reasoning}</blockquote>
      )}
    </div>
  );
}
