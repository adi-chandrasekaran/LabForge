import { useEffect, useMemo, useRef, useState } from "react";
import { AlertTriangle, CheckCircle2, Database, Download, FileSpreadsheet, Upload, X } from "lucide-react";
import { Button } from "../components/ui/button";
import ConfirmDialog from "../components/ConfirmDialog";
import {
  fetchNMRImportFormats,
  uploadNMRImport,
  type NMRImportFormatRecord,
  type NMRImportResultRecord,
} from "../api";

const panel = "border border-border rounded-sm bg-card";

function label(value: string) {
  return value.replaceAll("_", " ").replace(/\b\w/g, character => character.toUpperCase());
}

export default function NMRDataPage() {
  const inputRef = useRef<HTMLInputElement>(null);
  const [formats, setFormats] = useState<NMRImportFormatRecord[]>([]);
  const [entityType, setEntityType] = useState("residues");
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<NMRImportResultRecord | null>(null);
  const [imported, setImported] = useState<NMRImportResultRecord | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [confirmOpen, setConfirmOpen] = useState(false);

  useEffect(() => {
    fetchNMRImportFormats().then(setFormats).catch(reason => {
      setError(reason instanceof Error ? reason.message : "Unable to load NMR import formats.");
    });
  }, []);

  const selected = useMemo(() => formats.find(value => value.entityType === entityType), [formats, entityType]);
  const canImport = Boolean(preview && preview.errors.length === 0 && preview.validRows > 0 && file);

  function resetSelection(nextFile: File | null) {
    setFile(nextFile);
    setPreview(null);
    setImported(null);
    setError(null);
  }

  async function previewFile() {
    if (!file) return;
    setBusy(true);
    setError(null);
    try {
      setPreview(await uploadNMRImport(entityType, file, true));
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Unable to validate this CSV file.");
    } finally {
      setBusy(false);
    }
  }

  async function commitImport() {
    if (!file || !canImport) return;
    setBusy(true);
    setError(null);
    try {
      const result = await uploadNMRImport(entityType, file, false);
      setImported(result);
      setPreview(result);
      setConfirmOpen(false);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Unable to import this dataset.");
    } finally {
      setBusy(false);
    }
  }

  function downloadTemplate() {
    if (!selected) return;
    const columns = [...selected.requiredColumns, ...selected.optionalColumns];
    const blob = new Blob([`${columns.join(",")}\n`], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `${selected.entityType}-template.csv`;
    anchor.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div className="min-h-full bg-background px-7 py-7" style={{ fontFamily: "'JetBrains Mono', monospace" }}>
      <div className="mb-6">
        <div className="text-[9px] tracking-[0.25em] text-muted-foreground">EXPERIMENTAL DATA</div>
        <h1 className="mt-1 text-xl font-semibold" data-testid="nmr-data-title">Import NMR datasets</h1>
        <p className="mt-1 max-w-2xl text-[10px] text-muted-foreground">Validate CSV data against your existing proteins and spectra before saving it to LabForge.</p>
      </div>

      {error && <div className="mb-4 border border-red-400/25 bg-red-400/10 p-3 text-[10px] text-red-200">{error}</div>}
      <div className="mb-5 grid gap-2 sm:grid-cols-3">
        {["1 · Choose data", "2 · Preview validation", "3 · Confirm import"].map((step, index) => <div key={step} className={`${panel} px-3 py-2 text-[9px] ${index === 0 || preview ? "text-[#00c9a7]" : "text-muted-foreground"}`}>{step}</div>)}
      </div>

      <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_minmax(320px,0.7fr)]">
        <section className={`${panel} p-5`}>
          <div className="mb-4 flex items-center gap-2"><Database className="h-4 w-4 text-[#00c9a7]" /><h2 className="text-xs font-semibold">Dataset type</h2></div>
          <div className="grid gap-2 sm:grid-cols-2">
            {formats.map(format => <button key={format.entityType} type="button" onClick={() => { setEntityType(format.entityType); resetSelection(null); }} className={`border p-3 text-left transition-colors ${entityType === format.entityType ? "border-[#00c9a7]/50 bg-[#00c9a7]/10 text-[#00c9a7]" : "border-border bg-background text-muted-foreground hover:text-foreground"}`}><div className="text-[10px] font-semibold">{label(format.entityType)}</div><div className="mt-1 text-[8px] opacity-75">{format.requiredColumns.length} required fields</div></button>)}
          </div>

          <div className="mt-5 flex items-start justify-between gap-3 border-t border-border pt-5">
            <div><div className="text-[10px] text-foreground">CSV columns</div><div className="mt-1 text-[8px] text-muted-foreground">Required fields are marked in teal.</div></div>
            <Button variant="outline" size="sm" onClick={downloadTemplate} disabled={!selected}><Download className="h-3 w-3" />Template</Button>
          </div>
          {selected && <div className="mt-3 flex flex-wrap gap-1.5">{selected.requiredColumns.map(column => <span key={column} className="border border-[#00c9a7]/30 bg-[#00c9a7]/10 px-2 py-1 text-[8px] text-[#00c9a7]">{column}</span>)}{selected.optionalColumns.map(column => <span key={column} className="border border-border bg-secondary/40 px-2 py-1 text-[8px] text-muted-foreground">{column}</span>)}</div>}
          {selected?.listSeparator && <div className="mt-3 text-[8px] text-muted-foreground">Separate multiple values with <span className="text-foreground">{selected.listSeparator}</span>.</div>}

          <input ref={inputRef} className="hidden" type="file" accept=".csv,text/csv" onChange={event => resetSelection(event.target.files?.[0] ?? null)} data-testid="nmr-file-input" />
          <button type="button" onClick={() => inputRef.current?.click()} className="mt-5 flex min-h-32 w-full flex-col items-center justify-center border border-dashed border-border bg-background px-4 text-center hover:border-[#00c9a7]/40" data-testid="nmr-file-picker">
            <FileSpreadsheet className="mb-2 h-6 w-6 text-violet-300" />
            <span className="text-[10px] text-foreground">{file ? file.name : "Choose a CSV file"}</span>
            <span className="mt-1 text-[8px] text-muted-foreground">UTF-8 CSV · maximum 1 MB</span>
          </button>
          {file && <div className="mt-3 flex items-center justify-between gap-3"><span className="text-[8px] text-muted-foreground">{Math.max(1, Math.ceil(file.size / 1024))} KB selected</span><button type="button" className="flex items-center gap-1 text-[8px] text-muted-foreground hover:text-foreground" onClick={() => resetSelection(null)}><X className="h-3 w-3" />Remove</button></div>}
          <div className="mt-4 flex justify-end"><Button onClick={() => void previewFile()} disabled={!file || busy}><Upload className="h-3 w-3" />{busy ? "Validating…" : "Preview validation"}</Button></div>
        </section>

        <section className={`${panel} p-5`} data-testid="nmr-import-preview">
          <h2 className="text-xs font-semibold">Validation preview</h2>
          {!preview && <div className="mt-4 text-[9px] leading-relaxed text-muted-foreground">Choose a dataset and CSV file, then preview it. Nothing is written during validation.</div>}
          {preview && <>
            <div className="mt-4 grid grid-cols-3 gap-2">{[["Rows", preview.totalRows], ["Valid", preview.validRows], ["Errors", preview.errors.length]].map(([name, value]) => <div key={String(name)} className="border border-border bg-background p-3"><div className="text-base text-foreground">{value}</div><div className="text-[8px] text-muted-foreground">{name}</div></div>)}</div>
            {preview.errors.length > 0 ? <div className="mt-4 space-y-2">{preview.errors.map((item, index) => <div key={`${item.row}-${index}`} className="flex gap-2 border border-amber-400/25 bg-amber-400/5 p-2 text-[9px] text-amber-200"><AlertTriangle className="h-3.5 w-3.5 shrink-0" /><span>Row {item.row}{item.field ? ` · ${item.field}` : ""}: {item.message}</span></div>)}</div> : <div className="mt-4 flex gap-2 border border-emerald-400/25 bg-emerald-400/5 p-3 text-[9px] text-emerald-200"><CheckCircle2 className="h-4 w-4 shrink-0" />All rows passed validation. Review the count before importing.</div>}
            {imported && <div className="mt-4 border border-[#00c9a7]/30 bg-[#00c9a7]/10 p-3 text-[9px] text-[#00c9a7]" data-testid="nmr-import-success">Imported {imported.importedCount} {label(imported.entityType).toLowerCase()} successfully.</div>}
            {!imported && <div className="mt-4 flex justify-end"><Button onClick={() => setConfirmOpen(true)} disabled={!canImport || busy}>Import {preview.validRows} rows</Button></div>}
          </>}
        </section>
      </div>

      <ConfirmDialog open={confirmOpen} onOpenChange={setConfirmOpen} title={`Import ${preview?.validRows ?? 0} ${label(entityType).toLowerCase()}?`} description="This will create new NMR records in your local LabForge database. The validated source file will not be stored." confirmLabel="Import dataset" destructive={false} busy={busy} onConfirm={() => void commitImport()} />
    </div>
  );
}
