import { fileUrl, type Step } from '../api';

// Resultado del paso Subir: muestra el documento original (los PDF y las imágenes se ven en el navegador).
export function UploadStep({ runId, step }: { runId: string; step: Step }) {
  const original = step.files.find(file => file.path.startsWith('1_upload/original'));
  if (!original) return null;

  const url = fileUrl(runId, original.path);
  if (/\.(jpe?g|png|webp)$/i.test(original.path)) {
    return <img src={url} alt="Documento original" className="max-h-[36rem] rounded-lg border border-glass-border" />;
  }
  if (original.path.endsWith('.pdf')) {
    return <iframe src={url} title="Documento original" className="h-[36rem] w-full rounded-lg border border-glass-border bg-white" />;
  }
  return <a href={url} className="text-sm text-primary underline">Descargar el original</a>;
}
