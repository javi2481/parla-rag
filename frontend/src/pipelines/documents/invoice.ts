export type Invoice = Record<string, string | number | null>;
export type Fields = Record<string, string>;

export const PDF_MAX_BYTES = 5 * 1024 * 1024;
export const ACCEPTED_FILES = 'application/pdf,.pdf,image/jpeg,.jpg,.jpeg,image/png,.png,image/webp,.webp';

// Revisa extensión y tamaño antes de subir, para avisar rápido sin gastar un pedido.
export function validatePdf(file: { size: number; name: string }) {
  if (!/\.(pdf|jpe?g|png|webp)$/i.test(file.name) || file.size < 5 || file.size > PDF_MAX_BYTES) throw new Error('Elegí un PDF o una foto (JPG, PNG o WebP) de hasta 5 MB.');
}

// Arma un CSV (separado por ;) con los datos extraídos. Se genera en el navegador.
export function invoiceCsv(data: Invoice, fields: Fields) {
  // Convierte un valor en una celda CSV segura (neutraliza fórmulas de planilla).
  const cell = (v: unknown) => {
    let text = String(v ?? '');
    if (typeof v === 'string' && /^[\s]*[=+@-]/.test(text)) text = `'${text}`; // neutraliza fórmulas de planilla
    return `"${text.replaceAll('"', '""')}"`;
  };
  return '﻿' + Object.values(fields).map(cell).join(';') + '\r\n' + Object.keys(fields).map(k => cell(data[k])).join(';') + '\r\n';
}

// Arma una tabla Markdown con los datos extraídos.
export function invoiceMarkdown(data: Invoice, fields: Fields) {
  // Escapa los caracteres que romperían la tabla Markdown.
  const escape = (v: unknown) => String(v ?? '—').replaceAll('\\', '\\\\').replaceAll('|', '\\|').replace(/\r?\n/g, '<br>').replaceAll('<', '&lt;').replaceAll('>', '&gt;');
  return '# Factura extraída\n\n| Campo | Valor |\n| --- | --- |\n' + Object.entries(fields).map(([key, label]) => `| ${label} | ${escape(data[key])} |`).join('\n') + '\n\nRevisá los datos contra el comprobante original.\n';
}

// Arma un resumen corto para escuchar (proveedor, número, fecha, total, IVA). Se paga por carácter.
// Omite CUIT, detalle y cliente: leídos en voz alta son largos y poco útiles.
export function invoiceSpeech(data: Invoice) {
  // Devuelve el valor de un campo como texto, o '' si está vacío.
  const v = (k: string) => { const x = data[k]; return x === null || x === undefined || String(x).trim() === '' ? '' : String(x).trim(); };
  const parts = [
    v('proveedor') && `Comprobante de ${v('proveedor')}`,
    v('numero') && `número ${v('numero')}`,
    v('fecha') && `del ${v('fecha')}`,
  ].filter(Boolean).join(', ');
  return [parts && parts + '.', v('total') && `Total: ${v('total')}.`, v('iva') && `IVA: ${v('iva')}.`].filter(Boolean).join(' ');
}
