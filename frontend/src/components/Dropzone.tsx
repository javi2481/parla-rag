import { useState, type ReactNode } from 'react';
import type { LucideIcon } from 'lucide-react';

// Zona para soltar o elegir un archivo. Es un <label> de un input file, así funciona también con teclado.
export function Dropzone({ id, accept, disabled, onFile, icon: Icon, title, hint, children }: {
  id: string; accept: string; disabled?: boolean; onFile: (file: File) => void;
  icon: LucideIcon; title: string; hint: string; children?: ReactNode;
}) {
  const [over, setOver] = useState(false);
  return (
    <>
      <label
        htmlFor={id}
        onDragOver={e => { e.preventDefault(); if (!disabled) setOver(true); }}
        onDragLeave={() => setOver(false)}
        onDrop={e => {
          e.preventDefault(); setOver(false);
          const f = e.dataTransfer.files?.[0];
          if (f && !disabled) onFile(f);
        }}
        className={`group flex min-h-20 min-w-0 cursor-pointer items-center gap-4 rounded-xl border border-dashed px-4 py-3 transition-colors
          ${over ? 'border-primary bg-primary/10' : 'border-glass-border bg-background/40 hover:border-primary/60 hover:bg-primary/5'}
          ${disabled ? 'pointer-events-none opacity-60' : ''}`}
      >
        <span className={`grid size-11 shrink-0 place-items-center rounded-lg border transition-colors ${over ? 'border-primary bg-primary text-primary-foreground' : 'border-glass-border bg-glass text-mint group-hover:text-primary'}`}>
          <Icon className="size-5" />
        </span>
        <span className="min-w-0 flex-1">
          <span className="block truncate font-medium">{over ? 'Soltalo acá' : title}</span>
          <span className="block text-xs text-muted-foreground">{hint}</span>
        </span>
        {children}
      </label>
      <input id={id} type="file" accept={accept} className="sr-only" disabled={disabled} onChange={e => {
        const f = e.target.files?.[0]; e.target.value = '';
        if (f) onFile(f);
      }} />
    </>
  );
}
