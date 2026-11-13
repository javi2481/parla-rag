import { useEffect, useState } from 'react';
import { FileUp, LoaderCircle } from 'lucide-react';
import { Dropzone } from '@/components/Dropzone';
import { RunList } from '@/components/wizard/RunList';
import { StepPanel } from '@/components/wizard/StepPanel';
import { Stepper } from '@/components/wizard/Stepper';
import { checkStep, createRun, deleteRun, fileUrl, getRun, listRuns, startStep, type Run, type Step } from './api';
import { ClassifyOptions, ClassifyStep, initialClassifyOptions } from './steps/ClassifyStep';
import { ExtractOptions, ExtractStep, initialExtractOptions } from './steps/ExtractStep';
import { ParseStep } from './steps/ParseStep';
import { initialSchemaOptions, SchemaOptions, SchemaStep, schemaRequest } from './steps/SchemaStep';
import { initialSplitOptions, SplitOptions, SplitStep } from './steps/SplitStep';
import { UploadStep } from './steps/UploadStep';

// Cada cuánto se le pregunta a LlamaCloud cómo va un paso que está corriendo.
const POLL_MS = 3000;

// La vista del resultado de cada paso.
const STEP_VIEWS: Record<string, (props: { runId: string; step: Step }) => React.ReactNode> = {
  upload: UploadStep,
  parse: ParseStep,
  split: SplitStep,
  classify: ClassifyStep,
  schema: SchemaStep,
  extract: ExtractStep,
};

// Lo que recibe el editor de opciones de un paso.
type OptionsProps = { runId: string; step: Step; value: any; onChange: (value: unknown) => void; disabled: boolean };

// Los pasos que se configuran en el wizard: su editor, con qué opciones arranca
// y, si hace falta, cómo se pasan a lo que espera el backend.
const STEP_OPTIONS: Record<string, { Editor: (props: OptionsProps) => React.ReactNode; initial: (step: Step) => unknown; toRequest?: (value: any) => unknown }> = {
  split: { Editor: SplitOptions, initial: initialSplitOptions },
  classify: { Editor: ClassifyOptions, initial: initialClassifyOptions },
  schema: { Editor: SchemaOptions, initial: initialSchemaOptions, toRequest: schemaRequest },
  extract: { Editor: ExtractOptions, initial: initialExtractOptions },
};

// Sección Documentos: subir un documento y recorrer el wizard paso por paso.
export function DocumentsWizard({ ready, maxUploadMb }: { ready: boolean; maxUploadMb: number }) {
  const [runs, setRuns] = useState<Run[]>([]);
  const [run, setRun] = useState<Run | null>(null);
  const [selected, setSelected] = useState('upload');
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');
  // Las opciones que se van editando en cada paso, por nombre de paso.
  const [options, setOptions] = useState<Record<string, unknown>>({});

  // Al cambiar de corrida, los editores vuelven a arrancar con lo guardado en esa corrida.
  useEffect(() => { setOptions({}); }, [run?.id]);

  // Al entrar se cargan las corridas guardadas.
  useEffect(() => { refreshRuns(); }, []);

  // Mientras haya un paso corriendo, se consulta cada POLL_MS hasta que termine.
  useEffect(() => {
    const running = run?.steps.find(step => step.state === 'running');
    if (!run || !running) return;
    const timer = setTimeout(async () => {
      try {
        const updated = await checkStep(run.id, running.name);
        setRun(updated);
        if (updated.steps.find(step => step.name === running.name)?.state !== 'running') refreshRuns();
      } catch (e) {
        setError(message(e));
      }
    }, POLL_MS);
    return () => clearTimeout(timer);
  }, [run]);

  // Vuelve a pedir la lista de corridas.
  async function refreshRuns() {
    try { setRuns(await listRuns()); } catch (e) { setError(message(e)); }
  }

  // Sube el archivo elegido y abre la corrida nueva en el paso Parse.
  async function upload(file: File) {
    if (file.size > maxUploadMb * 1024 * 1024) { setError(`El archivo supera los ${maxUploadMb} MB.`); return; }
    setUploading(true); setError('');
    try {
      const created = await createRun(file);
      setRun(created);
      setSelected('parse');
      refreshRuns();
    } catch (e) {
      setError(message(e));
    } finally {
      setUploading(false);
    }
  }

  // Abre una corrida guardada, en su primer paso sin terminar.
  async function open(runId: string) {
    setError('');
    try {
      const opened = await getRun(runId);
      setRun(opened);
      setSelected(opened.steps.find(step => step.state !== 'done')?.name ?? opened.steps[opened.steps.length - 1]!.name);
    } catch (e) {
      setError(message(e));
    }
  }

  // Borra una corrida y, si era la abierta, la cierra.
  async function remove(runId: string) {
    try {
      await deleteRun(runId);
      if (run?.id === runId) setRun(null);
      refreshRuns();
    } catch (e) {
      setError(message(e));
    }
  }

  // Arranca (o repite) el paso elegido, con las opciones del editor si el paso las tiene.
  async function start(target: Step) {
    if (!run) return;
    setError('');
    try {
      const config = STEP_OPTIONS[target.name];
      const value = options[target.name] ?? config?.initial(target);
      const body = config ? (config.toRequest ? config.toRequest(value) : value) : undefined;
      setRun(await startStep(run.id, target.name, body));
    } catch (e) {
      setError(message(e));
    }
  }

  const step = run?.steps.find(s => s.name === selected);
  const View = step ? STEP_VIEWS[step.name] : undefined;
  const anyRunning = run?.steps.some(s => s.state === 'running') ?? false;
  const optionsConfig = step ? STEP_OPTIONS[step.name] : undefined;

  return (
    <div className="mt-10 grid gap-8 lg:grid-cols-[18rem_1fr]">
      <aside className="space-y-4">
        <Dropzone id="document-file" accept="*" disabled={!ready || uploading} onFile={upload} icon={FileUp}
          title={uploading ? 'Subiendo…' : 'Subí un documento'} hint={`PDF, imagen, Word, Excel… hasta ${maxUploadMb} MB`}>
          {uploading && <LoaderCircle className="size-5 animate-spin text-primary" />}
        </Dropzone>
        {!ready && <p className="text-sm text-destructive">Falta configurar LLAMA_CLOUD_API_KEY en el backend.</p>}
        <h3 className="pt-2 text-sm font-medium text-muted-foreground">Corridas guardadas</h3>
        <RunList runs={runs} selected={run?.id} onOpen={open} onDelete={remove} />
      </aside>

      <div className="min-w-0 space-y-6">
        {error && <p role="alert" className="rounded-xl border border-destructive/40 bg-destructive/10 p-4 text-sm text-destructive">{error}</p>}
        {!run && <p className="text-muted-foreground">Subí un documento o abrí una corrida guardada para ver el wizard.</p>}
        {run && (
          <>
            <div className="flex flex-wrap items-baseline justify-between gap-2">
              <h2 className="truncate font-display text-2xl">{run.name}</h2>
              <span className="font-mono text-xs text-muted-foreground">Total gastado: {run.total_credits} créditos</span>
            </div>
            <Stepper steps={run.steps} selected={selected} onSelect={setSelected} />
            {step && (
              <StepPanel step={step} fileHref={path => fileUrl(run.id, path)}
                onStart={step.name === 'upload' ? undefined : () => start(step)} canStart={!anyRunning}
                options={optionsConfig && step.defaults && (
                  <optionsConfig.Editor runId={run.id} step={step} disabled={anyRunning}
                    value={options[step.name] ?? optionsConfig.initial(step)}
                    onChange={value => setOptions(current => ({ ...current, [step.name]: value }))} />
                )}>
                {View && <View runId={run.id} step={step} />}
              </StepPanel>
            )}
          </>
        )}
      </div>
    </div>
  );
}

// Saca el mensaje de un error para mostrarlo.
function message(e: unknown) {
  return e instanceof Error ? e.message : 'Algo salió mal. Intentá de nuevo.';
}
