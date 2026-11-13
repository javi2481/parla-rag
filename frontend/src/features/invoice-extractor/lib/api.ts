import { api } from '@/lib/api';
import type { PdfBox } from '@/features/invoice-extractor/components/PdfPreview';
import type { Invoice } from './invoice';

export function extractInvoice(file: File) {
  const form = new FormData();
  form.append('file', file);
  return api<{ ticket: string }>('/api/invoice/extract', { method: 'POST', body: form });
}

export type InvoiceStatus =
  | { status: 'pending'; data: null; boxes: PdfBox[]; confidence: Record<string, number> }
  | { status: 'complete'; data: Invoice; boxes: PdfBox[]; confidence: Record<string, number> };
export const invoiceStatus = (ticket: string) => api<InvoiceStatus>(`/api/invoice/status/${encodeURIComponent(ticket)}`);
