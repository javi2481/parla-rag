import { useState } from 'react';
import { MarkdownView } from '@/components/wizard/MarkdownView';
import { fileUrl, screenshotPath } from '@/pipelines/documents/api';
import type { ChatEvent } from '@/pipelines/documents/libraries/api';

// Una página que llegó al modelo, tal como la manda el chat local en el evento "tool_result".
export type Fuente = { documento?: string; pagina?: number; rerank_score?: number | null; texto?: string; metadata?: { corrida?: string } };

// Saca las páginas que se le pasaron al modelo en este turno (vienen en el resultado de la búsqueda).
export function fuentesDe(events: ChatEvent[]): Fuente[] {
  const result = events.find(e => e.type === 'tool_result')?.result;
  return Array.isArray(result) ? (result as Fuente[]) : [];
}

// Agrupa las páginas por documento, en el orden en que aparecen (el del reranker: la mejor primero).
function porDocumento(fuentes: Fuente[]) {
  const grupos = new Map<string, Fuente[]>();
  for (const f of fuentes) {
    const doc = f.documento ?? 'Documento sin nombre';
    grupos.set(doc, [...(grupos.get(doc) ?? []), f]);
  }
  return [...grupos.entries()];
}

// Las citas de una respuesta, agrupadas por clase. Cada página se abre con su texto y la captura que sacó Parse,
// así se puede comprobar que la cita es correcta (el modelo a veces cita mal).
export function AnswerSources({ events }: { events: ChatEvent[] }) {
  const [abierta, setAbierta] = useState<string | null>(null);
  const grupos = porDocumento(fuentesDe(events));
  if (!grupos.length) return null;

  return (
    <div className="space-y-2">
      <p className="text-xs text-muted-foreground">Páginas que leyó el modelo, por clase ({grupos.length} {grupos.length === 1 ? 'clase' : 'clases'}):</p>
      {grupos.map(([doc, paginas]) => (
        <div key={doc} className="rounded-lg border border-glass-border px-3 py-2">
          <p className="text-sm font-medium">{doc.replace(/\.pdf$/i, '')}</p>
          <div className="mt-1 flex flex-wrap gap-1">
            {paginas.map(p => {
              const clave = `${doc}|${p.pagina}`;
              return (
                <button key={clave} type="button" aria-expanded={abierta === clave} onClick={() => setAbierta(abierta === clave ? null : clave)}
                  className={`rounded-full border px-2 py-0.5 font-mono text-xs ${abierta === clave ? 'border-primary text-foreground' : 'border-glass-border text-muted-foreground hover:text-foreground'}`}>
                  pág. {p.pagina}{p.rerank_score != null ? ` · ${p.rerank_score.toFixed(2)}` : ''}
                </button>
              );
            })}
          </div>
          {paginas.filter(p => abierta === `${doc}|${p.pagina}`).map(p => (
            <div key={p.pagina} className="mt-2 grid gap-3 md:grid-cols-2">
              {p.metadata?.corrida && p.pagina != null
                ? <img src={fileUrl(p.metadata.corrida, screenshotPath(p.pagina))} alt={`Captura de ${doc}, página ${p.pagina}`}
                    className="w-full rounded-lg border border-glass-border" loading="lazy" />
                : <p className="text-xs text-muted-foreground">Sin captura: la página no dice de qué corrida sale.</p>}
              <MarkdownView markdown={p.texto ?? ''} />
            </div>
          ))}
        </div>
      ))}
    </div>
  );
}
