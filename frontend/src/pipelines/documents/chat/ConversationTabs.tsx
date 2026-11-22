import { Plus, X } from 'lucide-react';
import type { Conversation } from '@/pipelines/documents/libraries/api';

// Las pestañas de conversación: una por conversación abierta, con una "×" para cerrarla y un "+" para abrir otra.
// Cerrar no borra nada: la conversación queda en disco para auditar. Mientras se responde, no se puede cambiar de pestaña.
export function ConversationTabs({ conversations, active, onSelect, onCreate, onClose, disabled }: {
  conversations: Conversation[]; active: string | null; disabled: boolean;
  onSelect: (id: string) => void; onCreate: () => void; onClose: (id: string) => void;
}) {
  return (
    <div role="tablist" aria-label="Conversaciones" className="flex flex-wrap items-center gap-1 border-b border-glass-border pb-2">
      {conversations.map(c => (
        <div key={c.id} className={`flex items-center rounded-full border text-sm ${c.id === active ? 'border-primary bg-primary/15 text-foreground' : 'border-glass-border text-muted-foreground'}`}>
          <button type="button" role="tab" aria-selected={c.id === active} disabled={disabled} onClick={() => onSelect(c.id)}
            className="max-w-56 truncate py-1 pl-3 pr-1" title={c.titulo}>{c.titulo}</button>
          <button type="button" aria-label={`Cerrar "${c.titulo}"`} disabled={disabled} onClick={() => onClose(c.id)}
            className="rounded-full p-1 pr-2 hover:text-destructive"><X className="size-3.5" /></button>
        </div>
      ))}
      <button type="button" aria-label="Conversación nueva" title="Conversación nueva" disabled={disabled} onClick={onCreate}
        className="rounded-full border border-glass-border p-1.5 text-muted-foreground hover:text-foreground"><Plus className="size-4" /></button>
    </div>
  );
}
