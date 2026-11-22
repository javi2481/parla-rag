import { useState } from 'react';
import { ChevronRight } from 'lucide-react';
import { RECORRIDO, type PasoDelRecorrido } from './explicaciones';

// Los colores dicen quién hace cada cosa, igual que en los diagramas del README:
// gris = nuestros datos, azul = LlamaCloud, verde = LlamaIndex, violeta = Voyage AI, rosa = OpenAI.
const COLORES: Record<PasoDelRecorrido['id'], string> = {
  pdf: 'border-zinc-400/40 bg-zinc-400/10 text-zinc-200',
  parse: 'border-blue-400/50 bg-blue-400/10 text-blue-200',
  chunks: 'border-green-400/50 bg-green-400/10 text-green-200',
  voyage: 'border-purple-400/50 bg-purple-400/10 text-purple-200',
  openai: 'border-pink-400/50 bg-pink-400/10 text-pink-200',
};

// Los números de cada caja, ya armados por la página con lo que devolvió la API (null = la API no lo dice todavía).
export type NumerosDelRecorrido = Record<PasoDelRecorrido['id'], string | null>;

// El recorrido del proyecto: 5 cajas, de los PDF a la respuesta. Cada caja se abre con qué hace y por qué se eligió.
// Queda fijo arriba de la conversación, así siempre se ve de dónde sale lo que responde el chat.
export function ProjectJourney({ numeros }: { numeros: NumerosDelRecorrido }) {
  const [abierta, setAbierta] = useState<PasoDelRecorrido['id'] | null>(null);
  const paso = RECORRIDO.find(p => p.id === abierta);

  return (
    <section aria-label="Recorrido del proyecto"
      className="sticky top-[4.25rem] z-20 rounded-2xl border border-glass-border bg-background/85 p-3 backdrop-blur-xl">
      <ol className="flex flex-wrap items-stretch gap-1.5">
        {RECORRIDO.map((p, i) => (
          <li key={p.id} className="flex flex-1 items-center gap-1.5">
            <button type="button" onClick={() => setAbierta(abierta === p.id ? null : p.id)} aria-expanded={abierta === p.id}
              className={`flex min-w-36 flex-1 flex-col rounded-xl border px-3 py-2 text-left transition hover:brightness-125 ${COLORES[p.id]} ${abierta === p.id ? 'ring-1 ring-current' : ''}`}>
              <span className="text-sm font-medium">{p.titulo}</span>
              <span className="text-[11px] opacity-75">{p.herramienta}</span>
              {numeros[p.id] && <span className="mt-1 font-mono text-[11px] text-foreground/90">{numeros[p.id]}</span>}
            </button>
            {i < RECORRIDO.length - 1 && <ChevronRight aria-hidden className="size-4 flex-none text-muted-foreground" />}
          </li>
        ))}
      </ol>
      {paso && (
        <div className={`mt-2 rounded-xl border px-4 py-3 text-sm ${COLORES[paso.id]}`}>
          <p><strong>Qué hace:</strong> {paso.queHace}</p>
          <p className="mt-1"><strong>Por qué:</strong> {paso.porQue}</p>
        </div>
      )}
    </section>
  );
}
