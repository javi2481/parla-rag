import { Plus, Trash2 } from 'lucide-react';
import { Button } from '@/components/ui/button';

// Estilo común de los campos de texto de los editores del wizard.
export const INPUT = 'w-full rounded-md border border-glass-border bg-background/60 px-2 py-1.5 text-sm outline-none focus:border-primary';

// Una fila del editor: un nombre corto y una descripción.
export type Row = Record<string, string>;

// Editor de una lista de filas con dos columnas (por ejemplo las categorías de Split: nombre y descripción).
// `keys` dice cómo se llaman las dos columnas en el JSON que se manda a LlamaCloud.
export function RowsEditor({ rows, onChange, keys, labels, disabled }: {
  rows: Row[];
  onChange: (rows: Row[]) => void;
  keys: [string, string];
  labels: [string, string];
  disabled?: boolean;
}) {
  const [nameKey, descriptionKey] = keys;

  // Cambia una columna de una fila.
  function update(index: number, key: string, value: string) {
    onChange(rows.map((row, i) => (i === index ? { ...row, [key]: value } : row)));
  }

  return (
    <div className="space-y-2">
      <div className="hidden grid-cols-[14rem_1fr_2.5rem] gap-2 text-xs text-muted-foreground sm:grid">
        <span>{labels[0]}</span><span>{labels[1]}</span>
      </div>
      {rows.map((row, index) => (
        <div key={index} className="grid gap-2 sm:grid-cols-[14rem_1fr_2.5rem]">
          <input className={`${INPUT} font-mono`} value={row[nameKey] ?? ''} disabled={disabled} aria-label={labels[0]}
            onChange={e => update(index, nameKey, e.target.value)} />
          <input className={INPUT} value={row[descriptionKey] ?? ''} disabled={disabled} aria-label={labels[1]}
            onChange={e => update(index, descriptionKey, e.target.value)} />
          <Button variant="ghost" size="icon" disabled={disabled} aria-label="Sacar"
            onClick={() => onChange(rows.filter((_, i) => i !== index))}><Trash2 /></Button>
        </div>
      ))}
      <Button variant="outline" size="sm" disabled={disabled}
        onClick={() => onChange([...rows, { [nameKey]: '', [descriptionKey]: '' }])}><Plus /> Agregar</Button>
    </div>
  );
}
