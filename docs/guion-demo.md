# Guion de la demo · Parla RAG

Para mostrar en clase, en unos 15 minutos, cómo se arma un chat sobre las 14 clases de Aprendizaje Automático II y cómo se comprueba lo que responde.
Todo lo que dice "se espera" salió de pruebas reales del 21/11 (ver la [bitácora](bitacora.md)). El modelo es chico: el texto de la respuesta cambia un poco cada vez, pero las clases citadas y los números del detrás de escena tienen que coincidir.

## Antes de empezar

- Backend y frontend corriendo (ver [Reproducir](../README.md#reproducir)), o Docker en `http://localhost:8000`.
- La biblioteca "Aprendizaje Automático II" sincronizada (14 documentos, 410 páginas). Para preguntar hace falta internet (Voyage AI y OpenAI).
- Cerrar las pestañas de conversación de pruebas anteriores, así se arranca con una sola vacía.

## 1. El recorrido (3 minutos)

La app abre en **Chat**. Arriba está el recorrido fijo, con los colores de quién hace cada cosa:

| Caja | Qué mostrar | Número que se ve |
|---|---|---|
| Las clases (gris) | El material real: diapositivas con gráficos, tablas, código y fórmulas | 14 documentos · 410 páginas |
| Parse (azul, LlamaCloud) | Se parsea una sola vez; todo lo demás usa ese parse | 7.250 créditos en 14 corridas |
| 1 página = 1 chunk (verde, LlamaIndex) | Por qué no se corta más chico: separaba tablas de su encabezado | 410 chunks |
| Buscar y ordenar (violeta, Voyage AI) | Vectores para encontrar rápido, reranker para ordenar fino | voyage-4 · rerank-2.5 |
| Responder (rosa, OpenAI) | Un modelo chico que lee solo las páginas elegidas | gpt-5-nano |

Tocar cada caja para abrir su "qué hace" y "por qué".

## 2. Una pregunta que cruza clases (4 minutos)

> **¿Qué tienen en común ResNet y U-Net?**

- **Se espera:** una respuesta que relaciona las dos (ResNet con conexiones residuales, U-Net con skip connections) y citas agrupadas en **07 Clasificación de imágenes** (págs. 27, 28 y 32) y **10 Segmentación de imágenes** (págs. 12 y 13). Puede aparecer también la **00 Presentación**.
- **Mostrar:** tocar **pág. 12** de la clase 10: se abre la captura de Parse al lado del texto. *"La cita no hay que creerla: se comprueba."*
- **Abrir "Detrás de escena":**
  1. Búsqueda: 18 candidatos, modo `default`.
  2. Reranker: 6 páginas, con puntajes entre 0,64 y 0,50.
  3. Respuesta: `gpt-5-nano`, unos 2.400 tokens de entrada y 300 de salida, **USD 0,0002 (estimado)**, 0 créditos de LlamaCloud.

## 3. El mismo tema con filtro de unidad (3 minutos)

Abrir una pestaña nueva con **+**.

> **¿Cómo funciona una red convolucional para clasificar imágenes?**

1. **Sin filtros:** se espera la clase **07 Clasificación de imágenes**.
2. **Con Unidad = PLN** (misma pregunta): se espera que cite **solo la 05 PLN - Redes neuronales**, y que la respuesta aclare que esas páginas son de lenguaje natural y no describen redes convolucionales para imágenes.

*Las unidades las puso **Classify**, con las 4 unidades del programa como reglas: las 14 clases quedaron bien ubicadas y no costó créditos.*

## 4. La trampa (2 minutos)

> **¿Cómo funciona Q-learning y la ecuación de Bellman?**

- **Se espera:** que diga que **no aparece en los documentos** (aprendizaje por refuerzo no se da en la materia).
- **Ojo:** a veces igual sugiere "fragmentos relevantes que podrías consultar". Sirve para explicar que el modelo tiende a ayudar de más, y por qué se mide con evals.

## 5. Cómo sabemos que funciona (3 minutos)

Ir a **Bibliotecas › Aprendizaje Automático II › Evals** y abrir la corrida **21/11/2026 19:09:42 · 18 candidatos · con respuestas** (la configuración que usa el chat: 6 páginas, búsqueda `default`):
- 31 preguntas verificadas en el parse (29 con fuente y 2 trampas).
- Búsqueda: hit rate 1,0 · MRR 0,96 · cobertura de clases 0,966.
- Respuestas: 30 de 31 fieles y 24 de 31 correctas. Las corridas de las 18:52 a las 19:04 son **la misma configuración** y dieron entre 22 y 25: **el juez (OpenAI) también tiene ruido**. Leer sus explicaciones, no solo el número.
- Las dos de arriba (19:12 y 19:17, 36 candidatos) probaron 12 páginas y 12 con MMR: no mejoraron la cobertura (MMR la bajó a 0,957 y tardó casi el doble), así que quedó la configuración más simple y rápida.

## Si algo falla

- **"Todavía no hay ninguna biblioteca sincronizada":** ir a Bibliotecas, abrir "Aprendizaje Automático II" y sincronizar (6 s, sin créditos).
- **El chat no responde:** revisar que el backend tenga `OPENAI_API_KEY` y `VOYAGE_API_KEY` en `backend/.env`.
- **Una cita apunta a la página equivocada:** es un error conocido del modelo chico. Mostrarlo abriendo la captura es parte de la demo.
