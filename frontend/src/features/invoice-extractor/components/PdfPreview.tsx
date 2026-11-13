import { useEffect, useRef, useState } from 'react';

export type PdfBox = { field: string; page: number; x: number; y: number; w: number; h: number };

const PALETTE = ['--chart-1', '--chart-2', '--chart-3', '--chart-4', '--chart-5'];
export function fieldColor(index: number) { return `var(${PALETTE[index % PALETTE.length]})`; }

/** Renders each PDF page to a canvas (browser only) and overlays the extracted-field boxes. */
export function PdfPreview({ file, boxes, fieldOrder, labels, active, onHover }: {
  file: File; boxes: PdfBox[]; fieldOrder: string[]; labels: Record<string, string>;
  active: string | null; onHover: (field: string | null) => void;
}) {
  const [pages, setPages] = useState<{ url: string; ratio: number }[]>([]);
  const [error, setError] = useState('');
  const token = useRef(0);

  useEffect(() => {
    const run = ++token.current;
    setPages([]); setError('');
    (async () => {
      try {
        if (file.type.startsWith('image/') || /\.(jpe?g|png|webp)$/i.test(file.name)) {
          const url = URL.createObjectURL(file);
          const img = new Image();
          await new Promise<void>((ok, fail) => { img.onload = () => ok(); img.onerror = () => fail(new Error('img')); img.src = url; });
          if (run === token.current) setPages([{ url, ratio: img.naturalHeight / img.naturalWidth }]);
          return;
        }
        const pdfjs = await import('pdfjs-dist');
        pdfjs.GlobalWorkerOptions.workerSrc = new URL('pdfjs-dist/build/pdf.worker.min.mjs', import.meta.url).toString();
        const doc = await pdfjs.getDocument({ data: new Uint8Array(await file.arrayBuffer()) }).promise;
        const out: { url: string; ratio: number }[] = [];
        for (let i = 1; i <= Math.min(doc.numPages, 3); i++) {
          const page = await doc.getPage(i);
          const viewport = page.getViewport({ scale: 1.6 });
          const canvas = document.createElement('canvas');
          canvas.width = viewport.width; canvas.height = viewport.height;
          const ctx = canvas.getContext('2d');
          if (!ctx) continue;
          await page.render({ canvasContext: ctx, viewport }).promise;
          out.push({ url: canvas.toDataURL('image/png'), ratio: viewport.height / viewport.width });
        }
        if (run === token.current) setPages(out);
        void doc.destroy();
      } catch { if (run === token.current) setError('No se pudo mostrar la vista previa del PDF.'); }
    })();
  }, [file]);

  if (error) return <p className="text-sm text-muted-foreground">{error}</p>;
  if (!pages.length) return <div className="grid aspect-[3/4] place-items-center rounded-lg border border-border bg-background/40 text-sm text-muted-foreground">Cargando vista previa…</div>;
  return <div className="space-y-4">
    {pages.map((p, i) => <div key={i} className="relative overflow-hidden rounded-lg border border-border bg-card shadow-lg">
      <img src={p.url} alt={`Página ${i + 1} de la factura`} className="block w-full" />
      {boxes.filter(b => b.page === i + 1).map((b, j) => {
        const color = fieldColor(Math.max(0, fieldOrder.indexOf(b.field)));
        const on = active === b.field; const dim = active && !on;
        return <div key={j} title={labels[b.field]} onMouseEnter={() => onHover(b.field)} onMouseLeave={() => onHover(null)}
          className="absolute rounded-sm border-2 transition-opacity motion-safe:animate-in motion-safe:fade-in motion-safe:duration-500"
          style={{ left: `${b.x * 100}%`, top: `${b.y * 100}%`, width: `${b.w * 100}%`, height: `${b.h * 100}%`, borderColor: color, background: `color-mix(in oklab, ${color} ${on ? 35 : 18}%, transparent)`, opacity: dim ? 0.25 : 1 }}>
          {(on || j === 0) && <span className="absolute -top-5 left-0 whitespace-nowrap rounded px-1.5 py-0.5 text-[10px] font-semibold text-background" style={{ background: color }}>{labels[b.field]}</span>}
        </div>;
      })}
    </div>)}
  </div>;
}
