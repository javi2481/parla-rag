import { useEffect, useState } from 'react';
import { JsonView } from '@/components/wizard/JsonView';
import { BoxLegend, PageBoxes, type PageBox } from '@/components/wizard/PageBoxes';
import { INPUT } from '@/components/wizard/RowsEditor';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { fetchJson, fileUrl, screenshotPath, type Step } from '../api';
import type { Segment } from './SplitStep';

type Citation = { page: number; text: string | null; boxes: { x: number; y: number; w: number; h: number }[]; page_width: number | null; page_height: number | null };
type Field = { field: string; value: unknown; confidence: number | null; citations: Citation[] };
export type ExtractOptionsValue = { segment: string | null; target_pages: string | null };

// Misma regla que el backend: debajo de esta confianza, el campo se marca para revisar.
const LOW_CONFIDENCE = 0.8;
const COLORS = { ok: '#16a34a', low: '#dc2626', none: '#6b7280' };

// Arranca con lo de la última vez o con "todo el documento".
export function initialExtractOptions(step: Step): ExtractOptionsValue {
  const request = (step.request ?? {}) as { segment?: string | null; configuration?: { target_pages?: string } };
  return { segment: request.segment ?? null, target_pages: request.configuration?.target_pages ?? null };
}

// Pasa una lista de páginas a un texto corto: [4, 5, 6, 9] → "4-6,9" (el formato de target_pages).
function pagesText(pages: number[]) {
  const sorted = [...pages].sort((a, b) => a - b);
  const ranges: string[] = [];
  let start = sorted[0]!;
  for (let i = 1; i <= sorted.length; i++) {
    if (sorted[i] !== sorted[i - 1]! + 1) {
      ranges.push(start === sorted[i - 1] ? `${start}` : `${start}-${sorted[i - 1]}`);
      start = sorted[i]!;
    }
  }
  return ranges.join(',');
}

// Elegir sobre qué páginas trabaja Extract: todo el documento o una parte encontrada por Split.
export function ExtractOptions({ runId, value, onChange, disabled }: { runId: string; value: ExtractOptionsValue; onChange: (v: ExtractOptionsValue) => void; disabled: boolean }) {
  const [segments, setSegments] = useState<Segment[]>([]);

  useEffect(() => {
    fetchJson<Segment[]>(runId, '3_split/segments.json').then(setSegments, () => setSegments([]));
  }, [runId]);

  const options = segments.map(segment => ({ label: segment.category, pages: pagesText(segment.pages) }));
  const selected = options.findIndex(option => option.label === value.segment && option.pages === value.target_pages);
  return (
    <label className="flex flex-wrap items-center gap-2 text-sm">
      Páginas que analiza Extract:
      <select className={`${INPUT} w-auto`} disabled={disabled} value={selected}
        onChange={e => {
          const option = options[Number(e.target.value)];
          onChange(option ? { segment: option.label, target_pages: option.pages } : { segment: null, target_pages: null });
        }}>
        <option value={-1}>todo el documento</option>
        {options.map((option, index) => <option key={index} value={index}>{option.label} (págs. {option.pages})</option>)}
      </select>
    </label>
  );
}

// Muestra un valor extraído como texto.
function show(value: unknown) {
  if (value == null || value === '') return '—';
  if (typeof value === 'number') return value.toLocaleString('es-AR');
  if (typeof value === 'object') return JSON.stringify(value);
  return String(value);
}

// El color de un campo según su confianza.
function colorOf(field: Field) {
  if (field.confidence == null) return COLORS.none;
  return field.confidence < LOW_CONFIDENCE ? COLORS.low : COLORS.ok;
}

// Resultado de Extract: la tabla de campos y, al lado, la página con la caja de donde salió cada dato.
export function ExtractStep({ runId, step }: { runId: string; step: Step }) {
  const [fields, setFields] = useState<Field[]>([]);
  const [result, setResult] = useState<unknown>(null);
  const [selected, setSelected] = useState<number | null>(null);
  const [page, setPage] = useState<number | null>(null);

  useEffect(() => {
    fetchJson<Field[]>(runId, '6_extract/fields.json').then(loaded => {
      setFields(loaded);
      setPage(loaded.flatMap(f => f.citations.map(c => c.page))[0] ?? null);
    }, () => setFields([]));
    fetchJson<unknown>(runId, '6_extract/result.json').then(setResult, () => setResult(null));
    setSelected(null);
  }, [runId, step.finished_at]);

  // Elige un campo y abre la página de su primera cita.
  function choose(index: number) {
    setSelected(index);
    const first = fields[index]?.citations[0];
    if (first) setPage(first.page);
  }

  const pages = [...new Set(fields.flatMap(f => f.citations.map(c => c.page)))].sort((a, b) => a - b);
  const boxes: PageBox[] = [];
  const owners: number[] = [];
  let size = { width: 612, height: 792 };
  fields.forEach((field, index) => {
    for (const citation of field.citations) {
      if (citation.page !== page) continue;
      if (citation.page_width && citation.page_height) size = { width: citation.page_width, height: citation.page_height };
      for (const box of citation.boxes) {
        boxes.push({ ...box, color: colorOf(field), active: selected === index, label: `${field.field}: ${show(field.value)}` });
        owners.push(index);
      }
    }
  });

  return (
    <Tabs defaultValue="campos">
      <TabsList>
        <TabsTrigger value="campos">Campos y citas</TabsTrigger>
        <TabsTrigger value="json">JSON</TabsTrigger>
      </TabsList>

      <TabsContent value="campos" className="mt-4">
        <div className="grid gap-4 xl:grid-cols-[minmax(0,5fr)_minmax(0,6fr)]">
          <div className="max-h-[48rem] overflow-auto rounded-xl border border-glass-border">
            <table className="w-full text-left text-sm">
              <thead className="sticky top-0 bg-background text-xs text-muted-foreground">
                <tr><th className="p-2">Campo</th><th className="p-2">Valor</th><th className="p-2">Confianza</th><th className="p-2">Cita</th></tr>
              </thead>
              <tbody>
                {fields.map((field, index) => (
                  <tr key={field.field} onClick={() => choose(index)}
                    className={`cursor-pointer border-t border-glass-border align-top hover:bg-primary/5 ${selected === index ? 'bg-primary/10' : ''}`}>
                    <td className="p-2 font-mono text-xs">{field.field}</td>
                    <td className="p-2">{show(field.value)}</td>
                    <td className="p-2 font-mono text-xs" style={{ color: colorOf(field) }}>
                      {field.confidence == null ? '—' : `${Math.round(field.confidence * 100)}%`}
                    </td>
                    <td className="p-2 text-xs text-muted-foreground">
                      {field.value == null || field.value === '' ? '—'
                        : field.citations.length === 0 ? <span className="text-destructive">sin cita</span>
                        : field.citations.map((c, i) => <div key={i}>pág. {c.page}: «{c.text}»</div>)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="space-y-2">
            <div className="flex flex-wrap gap-1">
              {pages.map(number => (
                <button key={number} type="button" onClick={() => setPage(number)}
                  className={`rounded-md border px-2 py-0.5 text-xs ${page === number ? 'border-primary bg-primary/15' : 'border-glass-border'}`}>
                  pág. {number}
                </button>
              ))}
            </div>
            {page != null && (
              <PageBoxes src={fileUrl(runId, screenshotPath(page))} alt={`Página ${page}`} pageWidth={size.width} pageHeight={size.height}
                boxes={boxes} onBoxClick={i => setSelected(owners[i]!)} />
            )}
            <BoxLegend items={[
              { color: COLORS.ok, label: `confianza ≥ ${LOW_CONFIDENCE * 100}%` },
              { color: COLORS.low, label: 'para revisar' },
              { color: COLORS.none, label: 'sin confianza informada' },
            ]} />
          </div>
        </div>
      </TabsContent>

      <TabsContent value="json" className="mt-4"><JsonView data={result} /></TabsContent>
    </Tabs>
  );
}
