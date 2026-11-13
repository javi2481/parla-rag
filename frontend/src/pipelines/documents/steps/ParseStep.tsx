import { useEffect, useState } from 'react';
import { FileSpreadsheet } from 'lucide-react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { MarkdownView } from '@/components/wizard/MarkdownView';
import { BoxLegend, PageBoxes, type PageBox } from '@/components/wizard/PageBoxes';
import { fetchText, fileUrl, screenshotPath, type Step } from '../api';

type PageMeta = { page_number: number; confidence: number | null };
type Bbox = { x: number; y: number; w: number; h: number; label?: string | null; confidence?: number | null };
type ItemsPage = { page_number: number; page_width: number; page_height: number; items: { type: string; bbox?: Bbox[] | null }[] };

// Color y nombre de cada tipo de elemento que identifica LlamaParse en la página.
const ITEM_TYPES: Record<string, { color: string; label: string }> = {
  heading: { color: '#7c3aed', label: 'Título' },
  text: { color: '#2563eb', label: 'Texto' },
  list: { color: '#0891b2', label: 'Lista' },
  table: { color: '#16a34a', label: 'Tabla' },
  image: { color: '#ea580c', label: 'Imagen o gráfico' },
  chart: { color: '#ea580c', label: 'Imagen o gráfico' },
  header: { color: '#6b7280', label: 'Encabezado o pie' },
  footer: { color: '#6b7280', label: 'Encabezado o pie' },
};
const OTHER_TYPE = { color: '#db2777', label: 'Otro' };

// Saca el número de página de una captura: "2_parse/images/page_8.jpg" → 8.
function pageNumber(path: string) {
  return Number(path.match(/page_(\d+)\.jpg$/)?.[1] ?? 0);
}

// Resultado del paso Parse, en pestañas: Markdown, páginas (capturas con su confianza),
// tablas y gráficos (los recortes y el Excel) y texto plano.
export function ParseStep({ runId, step }: { runId: string; step: Step }) {
  const [markdown, setMarkdown] = useState('');
  const [text, setText] = useState('');
  const [pages, setPages] = useState<PageMeta[]>([]);
  const [items, setItems] = useState<ItemsPage[]>([]);
  const [selectedPage, setSelectedPage] = useState<number | null>(null);

  // Cuando cambia la corrida o se re-ejecuta el paso, se vuelven a leer los archivos guardados.
  useEffect(() => {
    fetchText(runId, '2_parse/document.md').then(setMarkdown, () => setMarkdown(''));
    fetchText(runId, '2_parse/text.txt').then(setText, () => setText(''));
    fetchText(runId, '2_parse/metadata.json').then(json => setPages(JSON.parse(json).pages ?? []), () => setPages([]));
    fetchText(runId, '2_parse/items.json').then(json => setItems(JSON.parse(json).pages ?? []), () => setItems([]));
    setSelectedPage(null);
  }, [runId, step.finished_at]);

  const screenshots = step.files.filter(file => /images\/page_\d+\.jpg$/.test(file.path)).sort((a, b) => pageNumber(a.path) - pageNumber(b.path));
  const crops = step.files.filter(file => /_(table|chart)_\d+_v\d+\.jpg$/.test(file.path));
  const excel = step.files.find(file => file.path.endsWith('tables.xlsx'));

  return (
    <Tabs defaultValue="markdown">
      <TabsList className="flex-wrap">
        <TabsTrigger value="markdown">Markdown</TabsTrigger>
        <TabsTrigger value="paginas">Páginas ({screenshots.length})</TabsTrigger>
        <TabsTrigger value="tablas">Tablas y gráficos ({crops.length})</TabsTrigger>
        <TabsTrigger value="texto">Texto plano</TabsTrigger>
      </TabsList>

      <TabsContent value="markdown" className="mt-4">
        <MarkdownView markdown={markdown} />
      </TabsContent>

      <TabsContent value="paginas" className="mt-4 space-y-4">
        <p className="text-sm text-muted-foreground">Tocá una página para verla grande con las cajas de lo que identificó LlamaParse.</p>
        {selectedPage != null && (
          <PageWithItems runId={runId} page={items.find(p => p.page_number === selectedPage)} number={selectedPage}
            onClose={() => setSelectedPage(null)} />
        )}
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
          {screenshots.map(file => {
            const number = pageNumber(file.path);
            const confidence = pages.find(page => page.page_number === number)?.confidence;
            const low = confidence != null && confidence < 0.8;
            return (
              <button key={file.path} type="button" onClick={() => setSelectedPage(number)}
                className={`block overflow-hidden rounded-lg border text-left ${low ? 'border-destructive' : 'border-glass-border'} ${selectedPage === number ? 'ring-2 ring-primary' : ''}`}>
                <img src={fileUrl(runId, file.path)} alt={`Página ${number}`} loading="lazy" className="w-full bg-white" />
                <span className={`flex justify-between px-2 py-1 text-xs ${low ? 'bg-destructive/15 text-destructive' : 'bg-background/60'}`}>
                  <span>Página {number}</span>
                  {confidence != null && <span>confianza {Math.round(confidence * 100)}%</span>}
                </span>
              </button>
            );
          })}
        </div>
      </TabsContent>

      <TabsContent value="tablas" className="mt-4 space-y-4">
        {excel && (
          <a href={fileUrl(runId, excel.path)} className="inline-flex items-center gap-2 text-sm text-primary hover:underline">
            <FileSpreadsheet className="size-4" /> Descargar todas las tablas en Excel
          </a>
        )}
        <div className="grid gap-4 sm:grid-cols-2">
          {crops.map(file => (
            <figure key={file.path} className="overflow-hidden rounded-lg border border-glass-border">
              <img src={fileUrl(runId, file.path)} alt={file.path} loading="lazy" className="w-full bg-white" />
              <figcaption className="bg-background/60 px-2 py-1 font-mono text-xs">{file.path.split('/').pop()}</figcaption>
            </figure>
          ))}
        </div>
      </TabsContent>

      <TabsContent value="texto" className="mt-4">
        <pre className="max-h-[36rem] overflow-auto whitespace-pre-wrap rounded-lg border border-glass-border bg-background/60 p-4 text-xs">{text}</pre>
      </TabsContent>
    </Tabs>
  );
}

// Una página grande con una caja por cada elemento que identificó LlamaParse (títulos, texto, tablas, gráficos…).
function PageWithItems({ runId, page, number, onClose }: { runId: string; page?: ItemsPage; number: number; onClose: () => void }) {
  const boxes: PageBox[] = [];
  const used = new Map<string, { color: string; label: string }>();
  for (const item of page?.items ?? []) {
    const kind = ITEM_TYPES[item.type] ?? OTHER_TYPE;
    used.set(kind.label, kind);
    for (const bbox of item.bbox ?? []) {
      const confidence = bbox.confidence != null ? ` · confianza ${Math.round(bbox.confidence * 100)}%` : '';
      boxes.push({ ...bbox, color: kind.color, label: `${kind.label} (${bbox.label ?? item.type})${confidence}` });
    }
  }
  return (
    <div className="space-y-2 rounded-xl border border-glass-border bg-background/40 p-3">
      <div className="flex items-center justify-between text-sm">
        <span>Página {number} · {boxes.length} elementos identificados</span>
        <button type="button" onClick={onClose} className="text-muted-foreground hover:text-foreground">Cerrar</button>
      </div>
      <div className="mx-auto max-w-3xl">
        {page
          ? <PageBoxes src={fileUrl(runId, screenshotPath(number))} alt={`Página ${number}`} pageWidth={page.page_width} pageHeight={page.page_height} boxes={boxes} />
          : <img src={fileUrl(runId, screenshotPath(number))} alt={`Página ${number}`} className="w-full bg-white" />}
      </div>
      <BoxLegend items={[...used.values()]} />
    </div>
  );
}
