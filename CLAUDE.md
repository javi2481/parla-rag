# Parla RAG · reglas del proyecto

Demo de clase que tiene que quedar como plantilla: un wizard de documentos con LlamaCloud y bibliotecas (RAG) con LlamaIndex, Voyage AI y DeepSeek.
Antes de cualquier cosa, leé [docs/estado.md](docs/estado.md): ahí está lo hecho, lo pendiente en orden y el roadmap.

## Idioma

- **Todo texto al usuario, en español rioplatense** (voseo), nunca en inglés, incluso después de mucha salida técnica en inglés.
- Toda la documentación y los comentarios del código, en español.

## Código

- **Simple, no "senior":** fácil de leer para alguien que está aprendiendo. Nada de abstracciones de más.
- **Un comentario `#` (o `//` en TypeScript) en español rioplatense arriba de cada función**, que diga qué hace y por qué.
- **Cada pipeline vive en su carpeta** (`backend/app/pipelines/documents/`): configuración, cliente, pasos y rutas juntos. En `core/` solo lo compartido.
- **Sin base de datos:** todo en carpetas dentro de `backend/data/` (la "carpeta-DB", `app/core/runs/store.py`).

## Solo lo nativo

- **No implementar nada que LlamaCloud, LlamaParse o LlamaIndex no hagan de forma nativa.** Nada de código innecesario. Si la plataforma no lo hace, se dice y se decide con el usuario.
- El framework LlamaIndex (código abierto) y sus **integraciones oficiales** (Voyage AI, DeepSeek) cuentan como nativos. No sumar otros frameworks ni herramientas.
- Las bibliotecas usan el motor **local** (`local_library.py`) porque el índice v2 de LlamaCloud da 403 con el plan gratis. El motor de LlamaCloud (`library.py`) se mantiene para cuando haya plan.

## Traer todo, medir e interpretar

- **El parse es el corazón:** se parsea **una vez**, completo, con todas las opciones y salidas. Split, Classify y Extract usan ese parse (`pjb-...`).
- Cada paso **pide toda la información** que ofrece la plataforma, la **guarda** (`request.json`, `response.json` y sus partes), la **mide** y la **interpreta solo con datos de la API**. No inventar frases: si la API no dice el motivo de algo, decirlo así.

## Registrar todo para auditar

- Cada prueba, hallazgo y decisión va a [docs/bitacora.md](docs/bitacora.md), en orden cronológico.
- **Cada llamada paga** va al registro de créditos de la bitácora (LlamaCloud). Los tokens de Voyage y el costo de DeepSeek también se anotan.
- Los datos crudos de las pruebas, en `backend/data/verificacion/` o en la corrida (fuera de git).

## Créditos y seguridad

- **Pedir el OK antes de una llamada que gaste créditos**, salvo que el usuario ya la haya aprobado. Las llamadas que no cuestan (volver a pedir un resultado, validar, listar) se pueden hacer.
- **Nunca subir `backend/.env`** (tiene las API keys). `.env.example` va sin claves.
- Los datos generados (`backend/data/` salvo `samples/`) no van a git.
- No mandar datos personales del usuario a servicios externos.

## Comandos

```bash
cd backend && uv run pytest                         # tests (clientes falsos, sin red ni créditos)
cd backend && uv run uvicorn app.main:app --reload --port 8000
cd frontend && npm run dev                          # http://localhost:5173
cd frontend && npm run build                        # compila y chequea TypeScript
```
