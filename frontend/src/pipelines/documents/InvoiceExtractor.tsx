import { useEffect, useRef, useState } from 'react';
import { FileText, ScanText, Download, LoaderCircle, ShieldCheck } from 'lucide-react';
import { Dropzone } from '@/components/Dropzone';
import { Button } from '@/components/ui/button';
import { extractInvoice, invoiceStatus } from '@/pipelines/documents/api';
import { PdfPreview, fieldColor, type PdfBox } from '@/pipelines/documents/PdfPreview';
import { invoiceCsv, invoiceMarkdown, invoiceSpeech, validatePdf, ACCEPTED_FILES, type Fields, type Invoice } from '@/pipelines/documents/invoice';
import { ListenButton } from '@/pipelines/audio/ListenButton';

const STAGES = [
  { at: 0, short: 'Subida', label: 'Verificando y subiendo el comprobante…' },
  { at: 20, short: 'Lectura', label: 'Leyendo el documento (texto u OCR)…' },
  { at: 50, short: 'Extracción', label: 'Identificando proveedor, CUIT, importes y fechas…' },
  { at: 80, short: 'Validación', label: 'Validando datos y ubicándolos en la factura…' },
];

// Sección Facturas: subir el documento, ver la vista previa con las cajas y los datos extraídos.
export function InvoiceExtractor({ ready, fields, maxPages, dailyLimit, audioReady }: { ready: boolean; fields: Fields; maxPages: number; dailyLimit: number; audioReady: boolean }) {
  const [file, setFile] = useState<File | null>(null);
  const [data, setData] = useState<Invoice | null>(null);
  const [boxes, setBoxes] = useState<PdfBox[]>([]);
  const [confidence, setConfidence] = useState<Record<string, number>>({});
  const [active, setActive] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const alive = useRef(true);

  useEffect(() => { alive.current = true; return () => { alive.current = false; }; }, []);

  const [progress, setProgress] = useState(0);
  useEffect(() => {
    if (!busy) return;
    const began = Date.now();
    const id = setInterval(() => {
      const s = (Date.now() - began) / 1000;
      // Curva estimada: se acerca al 95% en ~40 s; salta a 100% cuando llega el resultado.
      setProgress(p => Math.max(p, Math.min(95, Math.round(95 * (1 - Math.exp(-s / 14))))));
    }, 500);
    return () => clearInterval(id);
  }, [busy]);
  const stage = [...STAGES].reverse().find(s => progress >= s.at) ?? STAGES[0]!;

  // Manda el archivo y consulta cada tanto hasta que llega el resultado.
  async function submit() {
    if (!file || busy) return;
    setBusy(true); setError(''); setData(null); setBoxes([]); setConfidence({}); setProgress(3);
    try {
      validatePdf(file);
      const { ticket } = await extractInvoice(file);
      setProgress(p => Math.max(p, 20));
      const until = Date.now() + 10 * 60 * 1000;
      let delay = 4000;
      while (alive.current) {
        await new Promise(resolve => setTimeout(resolve, delay));
        if (!alive.current) return;
        const result = await invoiceStatus(ticket);
        if (result.status === 'complete') { setProgress(100); setData(result.data); setBoxes(result.boxes); setConfidence(result.confidence ?? {}); return; }
        if (Date.now() >= until) throw new Error('El procesamiento superó el tiempo permitido.');
        delay = Math.min(15000, delay + 2000);
      }
    } catch (e) { if (alive.current) setError(e instanceof Error ? e.message : 'No se pudo procesar el comprobante.'); }
    finally { if (alive.current) setBusy(false); }
  }
  // Descarga los datos en CSV o Markdown.
  function download(format: 'csv' | 'md') {
    if (!data) return;
    const blob = new Blob([format === 'csv' ? invoiceCsv(data, fields) : invoiceMarkdown(data, fields)], { type: format === 'csv' ? 'text/csv;charset=utf-8' : 'text/markdown;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a'); a.href = url; a.download = 'factura-extraida.' + format; a.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  // Guarda el archivo elegido, si pasa la validación.
  function pick(selected: File) {
    setData(null); setBoxes([]); setConfidence({}); setError(''); setFile(null);
    try { validatePdf(selected); setFile(selected); } catch (err) { setError(err instanceof Error ? err.message : 'Archivo inválido.'); }
  }
  const speech = data ? invoiceSpeech(data) : '';
  const found = data ? Object.keys(fields).filter(k => data[k] != null).length : 0;
  return (
    <div className="mt-10 space-y-8">
      <section aria-label="Subir factura" className="rounded-2xl border border-glass-border bg-glass/60 p-4 sm:p-5">
        <div className="grid grid-cols-1 items-center gap-4 md:grid-cols-[minmax(0,1fr)_auto]">
          <Dropzone id="invoice-pdf" accept={ACCEPTED_FILES} disabled={busy || !ready} onFile={pick} icon={FileText}
            title={file?.name || 'Soltá un PDF o una foto, o hacé clic para elegir'} hint={`Hasta 5 MB · ${maxPages} páginas · un comprobante`} />
          <Button onClick={submit} disabled={!ready || !file || busy} size="lg" className="h-12 rounded-full px-6">
            {busy ? <LoaderCircle className="animate-spin motion-reduce:animate-none" /> : <ScanText />}
            {busy ? 'Extrayendo…' : 'Extraer datos'}
          </Button>
        </div>
        <div className="mt-4 flex flex-wrap items-center gap-1.5 text-xs">
          {Object.values(fields).map((label, i) => <span key={label} className="flex items-center gap-1.5 rounded-full border border-glass-border bg-background/40 px-2.5 py-1 text-muted-foreground"><span className="size-1.5 rounded-full" style={{ background: fieldColor(i) }} />{label}</span>)}
        </div>
        {busy && <div className="mt-5" aria-live="polite">
          <div className="flex justify-between text-sm"><span className="text-primary">{stage.label}</span><span className="font-mono text-muted-foreground">{progress}%</span></div>
          <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-background/60" role="progressbar" aria-valuenow={progress} aria-valuemin={0} aria-valuemax={100}>
            <div className="h-full rounded-full bg-gradient-to-r from-primary to-mint transition-[width] duration-500" style={{ width: `${progress}%` }} />
          </div>
          <ol className="mt-3 grid grid-cols-2 gap-1 text-xs sm:grid-cols-4">
            {STAGES.map(s => <li key={s.label} className={progress >= s.at ? 'text-foreground' : 'text-muted-foreground'}>{progress >= s.at ? '●' : '○'} {s.short}</li>)}
          </ol>
        </div>}
        <p className="mt-4 flex flex-wrap items-center gap-2 text-xs text-muted-foreground"><ShieldCheck className="size-4 shrink-0 text-mint" /> {dailyLimit > 0 ? `Hasta ${dailyLimit} extracciones por día. ` : ''}El archivo se borra de LlamaCloud al terminar. Suele tardar entre 15 y 40 segundos.</p>
        {!ready && <p role="status" className="mt-2 text-sm text-muted-foreground">Falta configurar LLAMA_CLOUD_API_KEY en el backend.</p>}
        {error && <p role="alert" className="mt-2 break-words text-sm text-destructive">{error}</p>}
      </section>
      {file ? <div className="grid grid-cols-1 items-start gap-8 lg:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
        <section aria-label="Tu factura" className="animate-rise">
          <PdfPreview file={file} boxes={boxes} fieldOrder={Object.keys(fields)} labels={fields} active={active} onHover={setActive} />
        </section>
        <section aria-labelledby="invoice-results" className="rounded-2xl border border-glass-border bg-glass/60 p-5 lg:sticky lg:top-24">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h2 id="invoice-results" className="text-lg font-semibold">Datos extraídos</h2>
              {data && <p className="text-xs text-muted-foreground">{found} de {Object.keys(fields).length} campos encontrados · pasá el mouse para verlos en el documento</p>}
            </div>
            {data && <div className="flex gap-2">
              <Button variant="outline" size="sm" className="rounded-full" onClick={() => download('csv')}><Download /> CSV</Button>
              <Button variant="outline" size="sm" className="rounded-full" onClick={() => download('md')}><Download /> MD</Button>
            </div>}
          </div>
          {busy && <ul className="mt-4 space-y-2" aria-hidden="true">{Object.keys(fields).map(k => <li key={k} className="h-9 animate-pulse rounded-lg bg-background/50" />)}</ul>}
          {!busy && !data && <p className="mt-4 text-sm text-muted-foreground">Tocá «Extraer datos» para verlos acá.</p>}
          {data && <>
            {audioReady && speech && <div className="mt-4"><ListenButton text={speech} label="Escuchar resumen" /></div>}
            {boxes.length === 0 && <p className="mt-4 text-xs text-muted-foreground">No se recibieron ubicaciones para marcar en el documento.</p>}
            <dl className="mt-4 divide-y divide-glass-border/70">
              {Object.entries(fields).map(([key, label], i) => <div key={key} onMouseEnter={() => setActive(key)} onMouseLeave={() => setActive(null)} className={`grid grid-cols-[minmax(0,1fr)_minmax(0,2fr)] gap-4 rounded-lg px-2 py-2.5 text-sm transition-colors ${active === key ? 'bg-primary/10' : ''}`}>
                <dt className="flex items-center gap-2 text-muted-foreground"><span className="size-2 shrink-0 rounded-full" style={{ background: fieldColor(i) }} />{label}</dt><dd className="flex items-start justify-between gap-3"><span className={`min-w-0 whitespace-pre-wrap break-words ${data[key] == null ? 'text-muted-foreground/60' : ''}`}>{data[key] ?? 'No consta'}</span>{data[key] != null && confidence[key] !== undefined && <ConfidenceBadge value={confidence[key]} />}</dd>
              </div>)}
            </dl>
            <p className="mt-4 text-xs text-muted-foreground">Revisá los datos contra el original antes de usarlos, sobre todo los marcados «revisar».</p>
          </>}
        </section>
      </div>
      : <div className="grid min-h-64 place-items-center rounded-2xl border border-dashed border-glass-border text-center text-muted-foreground">
        <div><FileText className="mx-auto size-8 opacity-60" /><p className="mt-3 text-sm">Tu comprobante va a aparecer acá, con cada dato marcado</p></div>
      </div>}
    </div>
  );
}

// Muestra la confianza de un campo. Debajo de 70% se marca para revisar.
function ConfidenceBadge({ value }: { value: number }) {
  const pct = Math.round(value * 100);
  const low = value < 0.7;
  return <span title={`Confianza del modelo: ${pct}%`} className={`shrink-0 rounded-full border px-2 py-0.5 font-mono text-[10px] ${low ? 'border-destructive/50 text-destructive' : 'border-glass-border text-muted-foreground'}`}>
    {low ? `revisar · ${pct}%` : `${pct}%`}
  </span>;
}
