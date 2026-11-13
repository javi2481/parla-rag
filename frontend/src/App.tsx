import { useEffect, useState } from 'react';
import { AudioLines, FileText, LoaderCircle, Mic } from 'lucide-react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Brand } from '@/components/Brand';
import { getConfig, type AppConfig } from '@/lib/api';
import { InvoiceExtractor } from '@/pipelines/documents/InvoiceExtractor';
import { TextToSpeech } from '@/pipelines/audio/TextToSpeech';
import { SpeechToText } from '@/pipelines/audio/SpeechToText';

const TABS = [
  {
    id: 'facturas', label: 'Facturas', icon: FileText, eyebrow: '01 · Documentos',
    title: <>Facturas que se <em className="text-primary">leen solas</em></>,
    lead: 'Subí un PDF o una foto. Extraemos los datos clave, los marcamos sobre el documento y te los llevás en CSV, Markdown o en audio.',
  },
  {
    id: 'tts', label: 'Texto a voz', icon: AudioLines, eyebrow: '02 · Voz',
    title: <>Tu voz, en <em className="text-primary">cualquier texto</em></>,
    lead: 'Pegá un texto y escuchalo con tu voz clonada. Se limpia antes de enviarlo y lo repetido sale de la caché: pagás solo lo nuevo.',
  },
  {
    id: 'stt', label: 'Voz a texto', icon: Mic, eyebrow: '03 · Transcripción',
    title: <>Hablá, <em className="text-primary">nosotros escribimos</em></>,
    lead: 'Grabá o subí un audio. Lo transcribimos y le sacamos muletillas, tartamudeos y repeticiones para que quede listo para usar.',
  },
] as const;
type TabId = (typeof TABS)[number]['id'];

// Lee la pestaña inicial desde la URL (#facturas, #tts, #stt).
function initialTab(): TabId {
  const h = window.location.hash.slice(1);
  return TABS.some(t => t.id === h) ? (h as TabId) : 'facturas';
}

const MODEL_NAMES: Record<string, string> = {
  eleven_flash_v2_5: 'Flash v2.5', eleven_v4: 'v4', eleven_multilingual_v2: 'Multilingual v2', eleven_v4_turbo: 'v4 Turbo',
};

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
            <Status label="LlamaCloud" detail={config?.documents.tier} ok={config?.documents.ready} />
            <Status label="ElevenLabs" detail={config && (MODEL_NAMES[config.audio.ttsModel] ?? config.audio.ttsModel)} ok={config?.audio.ready} />
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
          <TabsContent value="facturas">
            <InvoiceExtractor ready={config.documents.ready} fields={config.documents.fields} maxPages={config.documents.maxPages} dailyLimit={config.documents.dailyLimit} audioReady={config.audio.ready} />
          </TabsContent>
          <TabsContent value="tts"><TextToSpeech ready={config.audio.ready} maxChars={config.audio.ttsMaxChars} model={MODEL_NAMES[config.audio.ttsModel] ?? config.audio.ttsModel} /></TabsContent>
          <TabsContent value="stt"><SpeechToText ready={config.audio.ready} maxSeconds={config.audio.sttMaxSeconds} /></TabsContent>
        </>}
      </main>

      <footer className="border-t border-glass-border/70">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-3 px-4 py-6 text-xs text-muted-foreground sm:px-6">
          <span className="flex items-center gap-2"><span className="font-display text-base text-foreground">Parla</span> documentos que hablan, voces que escriben</span>
          <span>Extracción con LlamaCloud · Voz con ElevenLabs · Las claves nunca salen del servidor</span>
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
