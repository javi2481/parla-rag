import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeRaw from 'rehype-raw';
import rehypeSanitize from 'rehype-sanitize';

// Muestra un Markdown con formato (títulos, listas y tablas).
// LlamaParse devuelve algunas tablas en HTML: rehypeRaw las interpreta y rehypeSanitize
// saca cualquier cosa peligrosa (scripts, eventos), porque el contenido viene del documento.
export function MarkdownView({ markdown }: { markdown: string }) {
  return (
    <div className="markdown max-h-[36rem] overflow-auto rounded-lg border border-glass-border bg-background/60 p-5 text-sm leading-relaxed">
      <ReactMarkdown remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeRaw, rehypeSanitize]}>
        {markdown}
      </ReactMarkdown>
    </div>
  );
}
