import type { LibraryDocument } from '@/pipelines/documents/libraries/api';

// Los nombres de las unidades para la pantalla. Las claves son las reglas de Classify (backend/.../steps/s4_classify.py).
export const UNIDADES: Record<string, string> = {
  redes_neuronales: 'Redes neuronales',
  procesamiento_del_lenguaje_natural: 'PLN',
  procesamiento_digital_de_imagenes: 'Procesamiento de imágenes',
  aprendizaje_profundo_en_imagenes: 'Aprendizaje profundo en imágenes',
  temas_complementarios: 'Temas complementarios',
  presentacion_de_la_materia: 'Presentación de la materia',
};

// Lo elegido en los filtros: "tipo" es la unidad y "nombre" la clase. Vacío = sin filtro.
export type Filtros = { tipo: string; nombre: string };
export const SIN_FILTROS: Filtros = { tipo: '', nombre: '' };

const SELECT = 'rounded-lg border border-glass-border bg-background/60 px-2 py-1 text-sm';

// Dos selectores, Unidad y Clase, armados con la metadata de los documentos de la biblioteca (no con una lista fija).
// Apagados por defecto: sin filtros, la búsqueda usa todas las clases.
export function ChatFilters({ documents, value, onChange, disabled }:
  { documents: LibraryDocument[]; value: Filtros; onChange: (filtros: Filtros) => void; disabled: boolean }) {
  const unidades = [...new Set(documents.map(d => String(d.metadata.tipo ?? '')).filter(Boolean))].sort();
  // Si hay una unidad elegida, la lista de clases muestra solo las de esa unidad.
  const clases = documents.filter(d => !value.tipo || d.metadata.tipo === value.tipo).map(d => d.name).sort();
  const activos = Boolean(value.tipo || value.nombre);

  return (
    <div className="flex flex-wrap items-center gap-3 text-sm">
      <label className="flex items-center gap-2">Unidad
        <select className={SELECT} value={value.tipo} disabled={disabled}
          onChange={e => onChange({ tipo: e.target.value, nombre: '' })}>
          <option value="">Todas</option>
          {unidades.map(u => <option key={u} value={u}>{UNIDADES[u] ?? u}</option>)}
        </select>
      </label>
      <label className="flex items-center gap-2">Clase
        <select className={SELECT} value={value.nombre} disabled={disabled}
          onChange={e => onChange({ ...value, nombre: e.target.value })}>
          <option value="">Todas</option>
          {clases.map(c => <option key={c} value={c}>{c.replace(/\.pdf$/i, '')}</option>)}
        </select>
      </label>
      {activos
        ? <button type="button" className="text-xs text-primary underline" disabled={disabled} onClick={() => onChange(SIN_FILTROS)}>Sacar filtros</button>
        : <span className="text-xs text-muted-foreground">Sin filtros, busca en las {documents.length} clases.</span>}
    </div>
  );
}
