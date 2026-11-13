// Una caja para dibujar sobre una página, en las coordenadas que usa LlamaCloud (puntos de la página).
export type PageBox = { x: number; y: number; w: number; h: number; color: string; label: string; active?: boolean };

// La captura de una página con cajas encima. Las cajas vienen en puntos de la página (por ejemplo 612 × 792)
// y se pasan a porcentajes, así quedan bien ubicadas sea cual sea el tamaño de la imagen en pantalla.
export function PageBoxes({ src, alt, pageWidth, pageHeight, boxes, onBoxClick }: {
  src: string;
  alt: string;
  pageWidth: number;
  pageHeight: number;
  boxes: PageBox[];
  onBoxClick?: (index: number) => void;
}) {
  return (
    <div className="relative w-full overflow-hidden rounded-lg border border-glass-border bg-white">
      <img src={src} alt={alt} className="block w-full" />
      {boxes.map((box, index) => (
        <button
          key={index}
          type="button"
          title={box.label}
          aria-label={box.label}
          onClick={() => onBoxClick?.(index)}
          className={`absolute border-2 transition-opacity ${box.active ? 'opacity-100' : 'opacity-60 hover:opacity-100'}`}
          style={{
            left: `${(box.x / pageWidth) * 100}%`,
            top: `${(box.y / pageHeight) * 100}%`,
            width: `${(box.w / pageWidth) * 100}%`,
            height: `${(box.h / pageHeight) * 100}%`,
            borderColor: box.color,
            backgroundColor: box.active ? `${box.color}55` : `${box.color}1f`,
          }}
        />
      ))}
    </div>
  );
}

// La leyenda de colores que va debajo de una página con cajas.
export function BoxLegend({ items }: { items: { color: string; label: string }[] }) {
  return (
    <ul className="flex flex-wrap gap-3 text-xs text-muted-foreground">
      {items.map(item => (
        <li key={item.label} className="flex items-center gap-1.5">
          <span className="inline-block size-3 rounded-sm border-2" style={{ borderColor: item.color, backgroundColor: `${item.color}33` }} />
          {item.label}
        </li>
      ))}
    </ul>
  );
}
