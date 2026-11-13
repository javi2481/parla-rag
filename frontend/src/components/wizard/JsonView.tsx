// Muestra un objeto como JSON con sangría, con scroll si es largo.
export function JsonView({ data }: { data: unknown }) {
  return (
    <pre className="max-h-96 overflow-auto rounded-lg border border-glass-border bg-background/60 p-3 font-mono text-xs leading-relaxed">
      {JSON.stringify(data, null, 2)}
    </pre>
  );
}
