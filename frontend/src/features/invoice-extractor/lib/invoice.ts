export type Invoice = Record<string, string | number | null>;
export type Fields = Record<string, string>;

export const PDF_MAX_BYTES = 5 * 1024 * 1024;
export const ACCEPTED_FILES = 'application/pdf,.pdf,image/jpeg,.jpg,.jpeg,image/png,.png,image/webp,.webp';

export function validatePdf(file: { size: number; name: string }) {
  if (!/\.(pdf|jpe?g|png|webp)$/i.test(file.name) || file.size < 5 || file.size > PDF_MAX_BYTES) throw new Error('Elegí un PDF o una foto (JPG, PNG o WebP) de hasta 5 MB.');
}

// Las exportaciones se generan en el navegador a partir de lo que se ve, sin pedidos pagos extra.
export function invoiceCsv(data: Invoice, fields: Fields) {
  const cell = (v: unknown) => {
    let text = String(v ?? '');
    if (typeof v === 'string' && /^[\s]*[=+@-]/.test(text)) text = `'${text}`; // neutraliza fórmulas de planilla
    return `"${text.replaceAll('"', '""')}"`;
  };
  return '﻿' + Object.values(fields).map(cell).join(';') + '\r\n' + Object.keys(fields).map(k => cell(data[k])).join(';') + '\r\n';
}

export function invoiceMarkdown(data: Invoice, fields: Fields) {
  const escape = (v: unknown) => String(v ?? '—').replaceAll('\\', '\\\\').replaceAll('|', '\\|').replace(/\r?\n/g, '<br>').replaceAll('<', '&lt;').replaceAll('>', '&gt;');
  return '# Factura extraída\n\n| Campo | Valor |\n| --- | --- |\n' + Object.entries(fields).map(([key, label]) => `| ${label} | ${escape(data[key])} |`).join('\n') + '\n\nRevisá los datos contra el comprobante original.\n';
}

/**
 * Resumen corto para escuchar: solo lo esencial (se paga por carácter).
 * Omite CUIT, detalle y cliente, que leídos en voz alta son largos y poco útiles.
 */
export function invoiceSpeech(data: Invoice) {
  const v = (k: string) => { const x = data[k]; return x === null || x === undefined || String(x).trim() === '' ? '' : String(x).trim(); };
  const parts = [
    v('proveedor') && `Comprobante de ${v('proveedor')}`,
    v('numero') && `número ${v('numero')}`,
    v('fecha') && `del ${v('fecha')}`,
  ].filter(Boolean).join(', ');
  return [parts && parts + '.', v('total') && `Total: ${v('total')}.`, v('iva') && `IVA: ${v('iva')}.`].filter(Boolean).join(' ');
}
