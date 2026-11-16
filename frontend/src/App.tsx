import { useEffect, useState } from 'react';
import { FileText, Library, LoaderCircle } from 'lucide-react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Brand } from '@/components/Brand';
import { getConfig, type AppConfig } from '@/lib/api';
import { DocumentsWizard } from '@/pipelines/documents/DocumentsWizard';
import { LibrariesView } from '@/pipelines/documents/libraries/LibrariesView';

const TABS = [
  {
    id: 'documentos', label: 'Documentos', icon: FileText, eyebrow: '01 · Documentos',
    title: <>Documentos que se <em className="text-primary">leen solos</em></>,
    lead: 'Subí un documento y recorré el pipeline paso por paso: en cada paso ves qué hizo LlamaCloud, cuánto costó y qué significa el resultado.',
  },
  {
    id: 'bibliotecas', label: 'Bibliotecas', icon: Library, eyebrow: '02 · Bibliotecas',
    title: <>Varios documentos, <em className="text-primary">una conversación</em></>,
    lead: 'Juntá documentos relacionados en un índice compartido. Probá la búsqueda y chateá con todos a la vez: se ve qué se buscó y de qué documento y página sale cada respuesta.',
  },
] as const;
type TabId = (typeof TABS)[number]['id'];

// Lee la pestaña inicial desde la URL (#documentos o #bibliotecas).
function initialTab(): TabId {
  const h = window.location.hash.slice(1);
  return TABS.some(t => t.id === h) ? (h as TabId) : 'documentos';
}

// Pantalla principal: encabezado con pestañas, la sección elegida y el pie.
export function App() {
  const [config, setConfig] = useState<AppConfig | null>(null);
  const [error, setError] = useState('');
  const [tab, setTab] = useState<TabId>(initialTab);

  useEffect(() => { getConfig().then(setConfig, e => setError(e instanceof Error ? e.message : 'No se pudo conectar con el backend.')); }, []);
  useEffect(() => { history.replaceState(null, '', `#${tab}`); }, [tab]);
  useEffect(() => {
    // Si cambia el # de la URL, cambia de pestaña.
    const onHash = () => setTab(initialTab());
    window.addEventListener('hashchange', onHash);
    return () => window.removeEventListener('hashchange', onHash);
  }, []);

  const current = TABS.find(t => t.id === tab)!;
  return (
    <Tabs value={tab} onValueChange={v => setTab(v as TabId)} className="flex min-h-screen flex-col gap-0">
      <header className="sticky top-0 z-30 border-b border-glass-border/70 bg-background/70 backdrop-blur-xl">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-x-6 gap-y-3 px-4 py-3 sm:px-6">
          <Brand />
          <TabsList className="order-3 h-auto w-full justify-start gap-1 overflow-x-auto rounded-full border border-glass-border bg-glass/60 p-1 sm:order-none sm:w-auto">
            {TABS.map(t => (
              <TabsTrigger key={t.id} value={t.id}
                className="flex-none gap-2 rounded-full px-4 py-1.5 text-muted-foreground data-[state=active]:bg-primary data-[state=active]:text-primary-foreground data-[state=active]:shadow-[0_0_24px_-6px_var(--primary)]">
                <t.icon className="size-4" /> {t.label}
              </TabsTrigger>
            ))}
          </TabsList>
          <div className="hidden items-center gap-2 md:flex">
            <Status label="LlamaCloud" detail={config?.documents.parseTier} ok={config?.documents.ready} />
          </div>
        </div>
      </header>

      <main className="mx-auto w-full max-w-6xl flex-1 px-4 pb-20 pt-10 sm:px-6 sm:pt-14">
        <div key={tab} className="max-w-3xl animate-rise">
          <p className="font-mono text-xs uppercase tracking-[0.2em] text-mint">{current.eyebrow}</p>
          <h1 className="mt-3 font-display text-5xl leading-[1.02] tracking-tight sm:text-6xl">{current.title}</h1>
          <p className="mt-4 max-w-2xl text-pretty text-muted-foreground">{current.lead}</p>
        </div>

        {error && <p role="alert" className="mt-8 rounded-xl border border-destructive/40 bg-destructive/10 p-4 text-sm text-destructive">{error} ¿Está corriendo el backend en el puerto 8000?</p>}
        {!config && !error && <p className="mt-8 flex items-center gap-2 text-sm text-muted-foreground"><LoaderCircle className="size-4 animate-spin" /> Conectando…</p>}
        {config && <>
          <TabsContent value="documentos">
            <DocumentsWizard ready={config.documents.ready} maxUploadMb={config.documents.maxUploadMb} />
          </TabsContent>
          <TabsContent value="bibliotecas"><LibrariesView ready={config.documents.ready} /></TabsContent>
        </>}
      </main>

      <footer className="border-t border-glass-border/70">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-3 px-4 py-6 text-xs text-muted-foreground sm:px-6">
          <span className="flex items-center gap-2"><span className="font-display text-base text-foreground">Parla RAG</span> documentos que se leen solos</span>
          <span>Documentos con LlamaCloud · Bibliotecas con LlamaIndex, Voyage AI y DeepSeek · Las claves nunca salen del servidor</span>
        </div>
      </footer>
    </Tabs>
  );
}

// Indicador de estado de un proveedor: verde si está listo, rojo si falta la API key.
function Status({ label, detail, ok }: { label: string; detail?: string | null; ok?: boolean }) {
  return (
    <span className="flex items-center gap-2 rounded-full border border-glass-border bg-glass/50 px-3 py-1 text-xs" title={ok === false ? 'Falta configurar la API key' : undefined}>
      <span className={`size-1.5 rounded-full ${ok === undefined ? 'bg-muted-foreground' : ok ? 'bg-mint shadow-[0_0_8px_var(--mint)]' : 'bg-destructive'}`} />
      <span>{label}</span>
      {detail && <span className="font-mono text-[10px] text-muted-foreground">{detail}</span>}
    </span>
  );
}
