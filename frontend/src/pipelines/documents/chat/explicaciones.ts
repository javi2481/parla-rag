// Los textos fijos que explican el proyecto, todos en un solo lugar.
// Acá no va ningún número: los números (páginas, créditos, chunks) los arma la página con lo que devuelve la API.

export type PasoDelRecorrido = {
  id: 'pdf' | 'parse' | 'chunks' | 'voyage' | 'openai';
  titulo: string;
  herramienta: string;
  queHace: string;
  porQue: string;
};

// Las 5 cajas del recorrido, en el orden en que viaja un documento hasta la respuesta.
export const RECORRIDO: PasoDelRecorrido[] = [
  {
    id: 'pdf', titulo: 'Las clases', herramienta: 'Los PDF de la materia',
    queHace: 'Son las diapositivas de Aprendizaje Automático II: texto, gráficos, tablas, código y fórmulas.',
    porQue: 'Es un material real y difícil de leer para una máquina, así que sirve para probar el pipeline de verdad.',
  },
  {
    id: 'parse', titulo: 'Parse', herramienta: 'LlamaCloud',
    queHace: 'Lee cada PDF una sola vez y lo pasa a Markdown, con las tablas, los gráficos como datos y una captura de cada página.',
    porQue: 'Todo lo demás (clasificar, buscar, responder) trabaja sobre este parse, así que no se vuelve a pagar por leer el PDF.',
  },
  {
    id: 'chunks', titulo: '1 página = 1 chunk', herramienta: 'LlamaIndex',
    queHace: 'Arma el índice: cada página del parse es un pedazo (chunk) con su documento, su número de página y su unidad.',
    porQue: 'Fue el corte que mejor buscó en los evals: cortar por oraciones separaba una tabla de su encabezado y el chat suponía lo que faltaba.',
  },
  {
    id: 'voyage', titulo: 'Buscar y ordenar', herramienta: 'Voyage AI',
    queHace: 'Convierte la pregunta en un vector, trae las páginas más parecidas y después un reranker las vuelve a ordenar leyendo pregunta y página juntas.',
    porQue: 'Los vectores encuentran rápido; el reranker es más fino y deja arriba las páginas que de verdad responden.',
  },
  {
    id: 'openai', titulo: 'Responder', herramienta: 'OpenAI',
    queHace: 'El modelo lee solo las páginas elegidas y escribe la respuesta citando de qué clase y página sale cada cosa.',
    porQue: 'Es un modelo chico y barato; la búsqueda ya le deja solo las páginas que importan, así que no necesita leer todas las clases.',
  },
];

// Las tres líneas del "detrás de escena" de cada respuesta.
export const DETRAS_DE_ESCENA: Record<'busqueda' | 'reranker' | 'respuesta', string> = {
  busqueda: 'Voyage AI pasó la pregunta a un vector y trajo las páginas más parecidas de todas las clases (los candidatos).',
  reranker: 'El reranker de Voyage AI leyó cada candidato junto con la pregunta y se quedó con los mejores; el puntaje va de 0 a 1.',
  respuesta: 'OpenAI escribió la respuesta leyendo solo esas páginas. Los tokens los informa OpenAI; el costo en dólares es estimado con su lista de precios.',
};
