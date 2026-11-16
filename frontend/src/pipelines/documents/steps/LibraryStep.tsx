import { useState } from 'react';
import { CircleCheck, Library as LibraryIcon, Plus } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { INPUT } from '@/components/wizard/RowsEditor';
import { addDocument, type Library } from '../libraries/api';

// Paso 7 del wizard: sumar el documento a una biblioteca. Usa el parse que ya está hecho (no se vuelve a parsear)
// y no gasta créditos; los embeddings se calculan recién al sincronizar, en la pestaña Bibliotecas.
export function LibraryStep({ runId, parsed, libraries, onAdded }: {
  runId: string; parsed: boolean; libraries: Library[]; onAdded: () => void;
}) {
  const [target, setTarget] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [added, setAdded] = useState('');

  const inside = libraries.filter(library => library.documents.some(doc => doc.run_id === runId));
  const available = libraries.filter(library => !inside.includes(library));

  // Agrega la corrida a la biblioteca elegida y avisa que falta sincronizar.
  async function add() {
    if (!target) return;
    setBusy(true); setError(''); setAdded('');
    try {
      const library = await addDocument(target, runId);
      setAdded(library.name);
      setTarget('');
      onAdded();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'No se pudo agregar.');
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="space-y-4 rounded-2xl border border-glass-border bg-glass/40 p-5">
      <div>
        <h3 className="flex items-center gap-2 font-medium"><LibraryIcon className="size-4" /> Paso 7 · Biblioteca</h3>
        <p className="mt-1 text-sm text-muted-foreground">
          Sumá este documento a una biblioteca para buscar y chatear con varios documentos a la vez.
          Se usa el Markdown de cada página del parse: no se vuelve a parsear y no gasta créditos.
        </p>
      </div>

      {!parsed && <p className="text-sm text-amber-400">Primero tiene que terminar el paso Parse.</p>}

      {inside.length > 0 && (
        <div className="space-y-1">
          <p className="text-sm">Ya está en:</p>
          <ul className="flex flex-wrap gap-2">
            {inside.map(library => (
              <li key={library.id} className="flex items-center gap-1 rounded-full border border-glass-border px-3 py-1 text-xs">
                <CircleCheck className="size-3.5 text-mint" /> {library.name}
              </li>
            ))}
          </ul>
        </div>
      )}

      {parsed && (
        <div className="flex flex-wrap items-center gap-2">
          <select className={`${INPUT} w-auto max-w-full`} value={target} disabled={busy || available.length === 0}
            onChange={e => setTarget(e.target.value)}>
            <option value="">{available.length ? 'Elegí una biblioteca…' : 'No hay otras bibliotecas: creá una en la pestaña Bibliotecas'}</option>
            {available.map(library => <option key={library.id} value={library.id}>{library.name}</option>)}
          </select>
          <Button size="sm" disabled={busy || !target} onClick={add}><Plus /> Agregar</Button>
        </div>
      )}

      {added && (
        <p className="text-sm text-mint">
          Se agregó a «{added}». Para que el índice lo tenga, falta sincronizar en la pestaña{' '}
          <a href="#bibliotecas" className="underline">Bibliotecas</a>.
        </p>
      )}
      {error && <p role="alert" className="text-sm text-destructive">{error}</p>}
    </section>
  );
}
