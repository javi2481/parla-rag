import { useEffect, useState } from 'react';
import { Plus, Trash2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { JsonView } from '@/components/wizard/JsonView';
import { INPUT } from '@/components/wizard/RowsEditor';
import { fetchJson, type Step } from '../api';

// Un campo de la tabla del modo manual. El backend lo traduce a JSON Schema.
type Field = { name: string; type: string; required: boolean; description: string };
type Defaults = { mode: string; templates: Record<string, Field[]>; fields: Field[]; prompt: string; only_identity_required: boolean };
type JsonSchema = { type?: string | string[]; description?: string; properties?: Record<string, JsonSchema>; items?: JsonSchema; required?: string[] };

// Lo que guarda el editor. `editor` dice si el modo manual se edita con la tabla o como JSON.
// `onlyIdentity`: dejar obligatorios solo los datos de identidad (los campos sueltos del primer nivel).
export type SchemaOptionsValue = { mode: 'manual' | 'auto'; editor: 'tabla' | 'json'; fields: Field[]; json: string; prompt: string; onlyIdentity: boolean };

const FIELD_TYPES = ['texto', 'número', 'fecha', 'sí/no', 'lista'];

// Arranca con lo de la última vez (si se corrió) o con la plantilla de por defecto.
export function initialSchemaOptions(step: Step): SchemaOptionsValue {
  const defaults = step.defaults as Defaults;
  const request = (step.request ?? {}) as { mode?: 'manual' | 'auto'; fields?: Field[]; data_schema?: unknown; prompt?: string; only_identity_required?: boolean };
  return {
    mode: request.mode ?? 'manual',
    editor: request.data_schema ? 'json' : 'tabla',
    fields: request.fields ?? defaults.fields,
    json: request.data_schema ? JSON.stringify(request.data_schema, null, 2) : '',
    prompt: request.prompt ?? defaults.prompt,
    onlyIdentity: request.only_identity_required ?? defaults.only_identity_required,
  };
}

// Pasa lo del editor al pedido que entiende el backend. Si el JSON está mal escrito, lanza un error para mostrar.
export function schemaRequest(value: SchemaOptionsValue) {
  const only_identity_required = value.onlyIdentity;
  if (value.mode === 'auto') return { mode: 'auto', prompt: value.prompt, only_identity_required };
  if (value.editor === 'json') {
    try { return { mode: 'manual', data_schema: JSON.parse(value.json), only_identity_required }; } catch { throw new Error('El JSON Schema no es un JSON válido.'); }
  }
  return { mode: 'manual', fields: value.fields.filter(field => field.name.trim()) };
}

// El editor del schema: modo manual (plantilla, tabla de campos o JSON) o automático (indicación para el agente).
export function SchemaOptions({ runId, step, value, onChange, disabled }: {
  runId: string; step: Step; value: SchemaOptionsValue; onChange: (v: SchemaOptionsValue) => void; disabled: boolean;
}) {
  const defaults = step.defaults as Defaults;

  // Carga el schema guardado (por ejemplo el que propuso el agente) en el editor JSON, para corregirlo.
  async function editSaved() {
    const saved = await fetchJson<unknown>(runId, '5_schema/schema.json');
    onChange({ ...value, mode: 'manual', editor: 'json', json: JSON.stringify(saved, null, 2) });
  }

  // Cambia una columna de un campo de la tabla.
  function updateField(index: number, change: Partial<Field>) {
    onChange({ ...value, fields: value.fields.map((field, i) => (i === index ? { ...field, ...change } : field)) });
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-4 text-sm" role="radiogroup" aria-label="Modo">
        <label className="flex items-center gap-2"><input type="radio" checked={value.mode === 'manual'} disabled={disabled} onChange={() => onChange({ ...value, mode: 'manual' })} /> Manual: los campos los escribo yo</label>
        <label className="flex items-center gap-2"><input type="radio" checked={value.mode === 'auto'} disabled={disabled} onChange={() => onChange({ ...value, mode: 'auto' })} /> Automático: los propone el agente de LlamaExtract</label>
      </div>

      {value.mode === 'auto' && (
        <label className="block space-y-1 text-sm">
          <span className="text-muted-foreground">Qué datos te interesan (opcional, ayuda al agente):</span>
          <textarea className={`${INPUT} min-h-20`} value={value.prompt} disabled={disabled} onChange={e => onChange({ ...value, prompt: e.target.value })} />
        </label>
      )}

      {(value.mode === 'auto' || value.editor === 'json') && (
        <label className="flex items-start gap-2 text-sm">
          <input type="checkbox" className="mt-1" checked={value.onlyIdentity} disabled={disabled} onChange={e => onChange({ ...value, onlyIdentity: e.target.checked })} />
          <span>
            Dejar obligatorios solo los datos de identidad (los campos sueltos: empresa, período, fecha…).
            <span className="block text-xs text-muted-foreground">Los datos dentro de grupos pasan a opcionales: si no están en el documento, Extract los deja vacíos en lugar de inventarlos.</span>
          </span>
        </label>
      )}

      {value.mode === 'manual' && (
        <>
          <div className="flex flex-wrap items-center gap-3 text-sm">
            <label className="flex items-center gap-2">
              Plantilla:
              <select className={`${INPUT} w-auto`} disabled={disabled} defaultValue=""
                onChange={e => e.target.value && onChange({ ...value, editor: 'tabla', fields: defaults.templates[e.target.value]! })}>
                <option value="">elegí una…</option>
                {Object.keys(defaults.templates).map(name => <option key={name} value={name}>{name}</option>)}
              </select>
            </label>
            <label className="flex items-center gap-2">
              Editar como:
              <select className={`${INPUT} w-auto`} value={value.editor} disabled={disabled} onChange={e => onChange({ ...value, editor: e.target.value as 'tabla' | 'json' })}>
                <option value="tabla">tabla de campos</option>
                <option value="json">JSON Schema</option>
              </select>
            </label>
            {step.state === 'done' && <Button variant="outline" size="sm" disabled={disabled} onClick={editSaved}>Cargar el schema guardado para corregirlo</Button>}
          </div>

          {value.editor === 'json' && (
            <textarea className={`${INPUT} min-h-72 font-mono text-xs`} value={value.json} disabled={disabled} spellCheck={false}
              onChange={e => onChange({ ...value, json: e.target.value })} aria-label="JSON Schema" />
          )}

          {value.editor === 'tabla' && (
            <div className="space-y-2">
              <div className="hidden grid-cols-[11rem_7rem_5rem_1fr_2.5rem] gap-2 text-xs text-muted-foreground md:grid">
                <span>Campo</span><span>Tipo</span><span>Obligatorio</span><span>Guía para el modelo</span>
              </div>
              {value.fields.map((field, index) => (
                <div key={index} className="grid gap-2 md:grid-cols-[11rem_7rem_5rem_1fr_2.5rem]">
                  <input className={`${INPUT} font-mono`} value={field.name} disabled={disabled} aria-label="Campo" onChange={e => updateField(index, { name: e.target.value })} />
                  <select className={INPUT} value={field.type} disabled={disabled} aria-label="Tipo" onChange={e => updateField(index, { type: e.target.value })}>
                    {FIELD_TYPES.map(type => <option key={type}>{type}</option>)}
                  </select>
                  <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={field.required} disabled={disabled} onChange={e => updateField(index, { required: e.target.checked })} /> sí</label>
                  <input className={INPUT} value={field.description} disabled={disabled} aria-label="Guía para el modelo" onChange={e => updateField(index, { description: e.target.value })} />
                  <Button variant="ghost" size="icon" disabled={disabled} aria-label="Sacar" onClick={() => onChange({ ...value, fields: value.fields.filter((_, i) => i !== index) })}><Trash2 /></Button>
                </div>
              ))}
              <Button variant="outline" size="sm" disabled={disabled}
                onClick={() => onChange({ ...value, fields: [...value.fields, { name: '', type: 'texto', required: false, description: '' }] })}><Plus /> Agregar campo</Button>
            </div>
          )}
        </>
      )}
    </div>
  );
}

// Recorre el schema y devuelve cada campo final con su ruta, tipo, guía y si es obligatorio.
function leafFields(schema: JsonSchema, prefix = ''): { path: string; type: string; description: string; required: boolean }[] {
  const leaves = [];
  for (const [name, field] of Object.entries(schema.properties ?? {})) {
    const path = `${prefix}${name}`;
    const type = Array.isArray(field.type) ? field.type.join('/') : field.type ?? 'any';
    if (type === 'object') leaves.push(...leafFields(field, `${path}.`));
    else if (type === 'array' && field.items?.type === 'object') leaves.push(...leafFields(field.items, `${path}[].`));
    else leaves.push({ path, type, description: field.description ?? '', required: schema.required?.includes(name) ?? false });
  }
  return leaves;
}

// Resultado del paso Schema: la lista de campos guardada en LlamaCloud y el JSON Schema completo.
export function SchemaStep({ runId, step }: { runId: string; step: Step }) {
  const [schema, setSchema] = useState<JsonSchema | null>(null);

  useEffect(() => {
    fetchJson<JsonSchema>(runId, '5_schema/schema.json').then(setSchema, () => setSchema(null));
  }, [runId, step.finished_at]);

  if (!schema) return null;
  return (
    <div className="space-y-4">
      <div className="overflow-x-auto rounded-xl border border-glass-border">
        <table className="w-full text-left text-sm">
          <thead className="bg-background/60 text-xs text-muted-foreground">
            <tr><th className="p-2">Campo</th><th className="p-2">Tipo</th><th className="p-2">Obligatorio</th><th className="p-2">Guía</th></tr>
          </thead>
          <tbody>
            {leafFields(schema).map(field => (
              <tr key={field.path} className="border-t border-glass-border align-top">
                <td className="p-2 font-mono text-xs">{field.path}</td>
                <td className="p-2">{field.type}</td>
                <td className="p-2">{field.required ? 'sí' : ''}</td>
                <td className="p-2 text-muted-foreground">{field.description}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <details>
        <summary className="cursor-pointer text-sm text-muted-foreground hover:text-foreground">JSON Schema completo</summary>
        <div className="mt-2"><JsonView data={schema} /></div>
      </details>
    </div>
  );
}
