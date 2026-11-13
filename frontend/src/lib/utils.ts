import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

// Junta clases de Tailwind y resuelve las que se pisan (ej. dos colores de fondo).
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
