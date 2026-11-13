// Logo de Parla: una hoja con ondas de sonido (documentos que hablan).
export function BrandMark({ className = 'size-8' }: { className?: string }) {
  return (
    <svg viewBox="0 0 32 32" className={className} aria-hidden="true">
      <rect width="32" height="32" rx="9" className="fill-glass" />
      <path d="M9 7h9l5 5v13H9z" fill="none" stroke="var(--primary)" strokeWidth="2" strokeLinejoin="round" />
      <path d="M18 7v5h5" fill="none" stroke="var(--primary)" strokeWidth="2" strokeLinejoin="round" />
      <path d="M13 16v4M16 14v8M19 17v2" stroke="var(--mint)" strokeWidth="2" strokeLinecap="round" />
    </svg>
  );
}

// Logo más el nombre, con link al inicio.
export function Brand() {
  return (
    <a href="#facturas" className="flex items-center gap-2.5" aria-label="Parla, inicio">
      <BrandMark />
      <span className="font-display text-2xl leading-none tracking-tight">Parla</span>
    </a>
  );
}
