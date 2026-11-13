import { api } from '@/lib/api';
import type { PdfBox } from '@/pipelines/documents/PdfPreview';
import type { Invoice } from './invoice';

// Sube el archivo y arranca la extracción. Devuelve un ticket para consultar.
export function extractInvoice(file: File) {
  const form = new FormData();
  form.append('file', file);
  return api<{ ticket: string }>('/api/documents/extract', { method: 'POST', body: form });
}

export type InvoiceStatus =
  | { status: 'pending'; data: null; boxes: PdfBox[]; confidence: Record<string, number> }
  | { status: 'complete'; data: Invoice; boxes: PdfBox[]; confidence: Record<string, number> };
// Consulta cómo va la extracción de un ticket.
export const invoiceStatus = (ticket: string) => api<InvoiceStatus>(`/api/documents/status/${encodeURIComponent(ticket)}`);
