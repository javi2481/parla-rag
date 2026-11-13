import { useEffect, useState } from 'react';
import { FileSpreadsheet } from 'lucide-react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { MarkdownView } from '@/components/wizard/MarkdownView';
import { fetchText, fileUrl, type Step } from '../api';

type PageMeta = { page_number: number; confidence: number | null };

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

  // Cuando cambia la corrida o se re-ejecuta el paso, se vuelven a leer los archivos guardados.
  useEffect(() => {
    fetchText(runId, '2_parse/document.md').then(setMarkdown, () => setMarkdown(''));
    fetchText(runId, '2_parse/text.txt').then(setText, () => setText(''));
    fetchText(runId, '2_parse/metadata.json').then(json => setPages(JSON.parse(json).pages ?? []), () => setPages([]));
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

      <TabsContent value="paginas" className="mt-4">
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
          {screenshots.map(file => {
            const number = pageNumber(file.path);
            const confidence = pages.find(page => page.page_number === number)?.confidence;
            const low = confidence != null && confidence < 0.8;
            return (
              <a key={file.path} href={fileUrl(runId, file.path)} target="_blank" rel="noreferrer"
                className={`block overflow-hidden rounded-lg border ${low ? 'border-destructive' : 'border-glass-border'}`}>
                <img src={fileUrl(runId, file.path)} alt={`Página ${number}`} loading="lazy" className="w-full bg-white" />
                <span className={`flex justify-between px-2 py-1 text-xs ${low ? 'bg-destructive/15 text-destructive' : 'bg-background/60'}`}>
                  <span>Página {number}</span>
                  {confidence != null && <span>confianza {Math.round(confidence * 100)}%</span>}
                </span>
              </a>
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
