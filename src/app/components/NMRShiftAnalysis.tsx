import { useEffect, useState } from "react";
import { Activity, Calculator, Sigma } from "lucide-react";
import { Button } from "./ui/button";
import {
  calculateNMRCSP, compareNMRSpectra, fetchNMRSpectra,
  type NMRCSPRecord, type NMRSpectrumComparisonRecord, type NMRSpectrumRecord,
} from "../api";

const panel = "border border-border rounded-sm bg-card";

export default function NMRShiftAnalysis() {
  const [spectra, setSpectra] = useState<NMRSpectrumRecord[]>([]);
  const [referenceId, setReferenceId] = useState("");
  const [comparisonId, setComparisonId] = useState("");
  const [mode, setMode] = useState<"comparison" | "csp">("comparison");
  const [hWeight, setHWeight] = useState("1");
  const [nWeight, setNWeight] = useState("0.154");
  const [comparison, setComparison] = useState<NMRSpectrumComparisonRecord | null>(null);
  const [csp, setCsp] = useState<NMRCSPRecord | null>(null);
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    void fetchNMRSpectra().then(values => {
      if (cancelled) return;
      setSpectra(values); setReferenceId(values[0]?.id ?? ""); setComparisonId(values[1]?.id ?? ""); setError(null);
    }).catch(reason => { if (!cancelled) setError(reason instanceof Error ? reason.message : "Unable to load spectra."); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, []);

  function clearResults() {
    setComparison(null);
    setCsp(null);
    setError(null);
  }

  const ready = Boolean(referenceId && comparisonId && referenceId !== comparisonId);
  async function run() {
    if (!ready) return;
    setBusy(true); setError(null); setComparison(null); setCsp(null);
    try {
      if (mode === "comparison") setComparison(await compareNMRSpectra(referenceId, comparisonId));
      else setCsp(await calculateNMRCSP(referenceId, comparisonId, { "1H": Number(hWeight), "15N": Number(nWeight) }));
    } catch (reason) { setError(reason instanceof Error ? reason.message : "The analysis could not be completed."); }
    finally { setBusy(false); }
  }

  return <div data-testid="nmr-shift-analysis">
    <section className={`${panel} p-5`}>
      <div className="flex items-center gap-2"><Activity className="h-4 w-4 text-[#00c9a7]" /><h2 className="text-xs font-semibold">Spectrum pair</h2></div>
      <p className="mt-1 text-[8px] text-muted-foreground">Only stored, matched chemical shifts are used. Missing experimental values are never inferred.</p>
      {loading ? <div className="mt-5 text-[9px] text-muted-foreground">Loading spectra…</div> : spectra.length < 2 ? <div className="mt-5 border border-amber-400/25 bg-amber-400/5 p-4 text-[9px] text-amber-200">Add at least two spectra and their chemical shifts before running an analysis.</div> : <>
        <div className="mt-5 grid gap-4 md:grid-cols-2">
          <SpectrumSelect label="Reference spectrum" value={referenceId} spectra={spectra} onChange={value => { setReferenceId(value); clearResults(); }} />
          <SpectrumSelect label="Comparison spectrum" value={comparisonId} spectra={spectra} onChange={value => { setComparisonId(value); clearResults(); }} />
        </div>
        {referenceId === comparisonId && <div className="mt-3 text-[9px] text-amber-300">Choose two different spectra.</div>}
        <div className="mt-5 flex flex-wrap items-end justify-between gap-4 border-t border-border pt-5">
          <div className="flex border border-border bg-background p-1">
            <ModeButton active={mode === "comparison"} onClick={() => { setMode("comparison"); clearResults(); }}><Sigma className="h-3.5 w-3.5" />Shift deltas</ModeButton>
            <ModeButton active={mode === "csp"} onClick={() => { setMode("csp"); clearResults(); }}><Calculator className="h-3.5 w-3.5" />CSP</ModeButton>
          </div>
          {mode === "csp" && <div className="flex gap-2"><WeightInput label="1H weight" value={hWeight} onChange={setHWeight} /><WeightInput label="15N weight" value={nWeight} onChange={setNWeight} /></div>}
          <Button onClick={() => void run()} disabled={!ready || busy || (mode === "csp" && (!(Number(hWeight) > 0) || !(Number(nWeight) > 0)))}>{busy ? "Calculating…" : mode === "comparison" ? "Compare spectra" : "Calculate CSP"}</Button>
        </div>
      </>}
    </section>
    {error && <div role="alert" className="mt-4 border border-red-400/25 bg-red-400/10 p-3 text-[9px] text-red-200">{error}</div>}
    {comparison && <ComparisonResult value={comparison} />}
    {csp && <CSPResult value={csp} />}
  </div>;
}

function SpectrumSelect({ label, value, spectra, onChange }: { label: string; value: string; spectra: NMRSpectrumRecord[]; onChange: (value: string) => void }) {
  return <label className="text-[9px] text-muted-foreground">{label}<select aria-label={label} value={value} onChange={event => onChange(event.target.value)} className="mt-2 w-full border border-border bg-background p-2.5 text-[9px] text-foreground">{spectra.map(spectrum => <option key={spectrum.id} value={spectrum.id}>{spectrum.name} · {spectrum.experimentType}</option>)}</select></label>;
}

function ModeButton({ active, onClick, children }: { active: boolean; onClick: () => void; children: React.ReactNode }) {
  return <button type="button" onClick={onClick} className={`flex items-center gap-2 px-3 py-2 text-[9px] ${active ? "bg-violet-400/10 text-violet-200" : "text-muted-foreground"}`}>{children}</button>;
}

function WeightInput({ label, value, onChange }: { label: string; value: string; onChange: (value: string) => void }) {
  return <label className="text-[8px] text-muted-foreground">{label}<input aria-label={label} type="number" min="0.001" step="0.001" value={value} onChange={event => onChange(event.target.value)} className="mt-1 block w-24 border border-border bg-background p-2 text-foreground" /></label>;
}

function ComparisonResult({ value }: { value: NMRSpectrumComparisonRecord }) {
  return <section className={`${panel} mt-5 p-5`} data-testid="spectrum-comparison-result">
    <div className="grid gap-2 sm:grid-cols-3">{[["Matched shifts", value.matchedShiftCount], ["Reference only", value.referenceOnlyCount], ["Comparison only", value.comparisonOnlyCount]].map(([name, count]) => <div key={String(name)} className="border border-border bg-background p-3"><div className="text-lg">{count}</div><div className="text-[8px] text-muted-foreground">{name}</div></div>)}</div>
    {value.deltas.length === 0 ? <div className="mt-4 border border-amber-400/25 bg-amber-400/5 p-3 text-[9px] text-amber-200">No chemical shifts matched between these spectra.</div> : <div className="mt-4 overflow-auto"><table className="w-full text-left text-[9px]"><thead className="text-muted-foreground"><tr><th className="p-2">Residue</th><th className="p-2">Atom</th><th className="p-2">Nucleus</th><th className="p-2 text-right">Reference</th><th className="p-2 text-right">Comparison</th><th className="p-2 text-right">Δ ppm</th></tr></thead><tbody>{value.deltas.map((item, index) => <tr key={`${item.residueId}-${item.atomName}-${index}`} className="border-t border-border"><td className="p-2">{item.residueName} {item.sequenceNumber}</td><td className="p-2">{item.atomName}</td><td className="p-2 text-violet-200">{item.nucleus}</td><td className="p-2 text-right">{item.referencePpm.toFixed(3)}</td><td className="p-2 text-right">{item.comparisonPpm.toFixed(3)}</td><td className="p-2 text-right text-[#00c9a7]">{item.deltaPpm.toFixed(3)}</td></tr>)}</tbody></table></div>}
  </section>;
}

function CSPResult({ value }: { value: NMRCSPRecord }) {
  return <section className={`${panel} mt-5 p-5`} data-testid="csp-result">
    <div className="flex justify-between gap-3"><div><h2 className="text-xs font-semibold">Chemical-shift perturbation</h2><p className="mt-1 text-[8px] text-muted-foreground">{value.formula}</p></div><div className="text-[9px] text-[#00c9a7]">{value.residueCount} matched residues</div></div>
    {value.residues.length === 0 ? <div className="mt-4 border border-amber-400/25 bg-amber-400/5 p-3 text-[9px] text-amber-200">No residues had the weighted nuclei required for CSP.</div> : <div className="mt-4 overflow-auto"><table className="w-full text-left text-[9px]"><thead className="text-muted-foreground"><tr><th className="p-2">Residue</th><th className="p-2">Atoms</th><th className="p-2">Component deltas</th><th className="p-2 text-right">CSP ppm</th></tr></thead><tbody>{value.residues.map(item => <tr key={item.residueId} className="border-t border-border"><td className="p-2">{item.residueName} {item.sequenceNumber}</td><td className="p-2">{item.matchedAtoms.join(" / ")}</td><td className="p-2 text-muted-foreground">{Object.entries(item.componentDeltasPpm).map(([atom, delta]) => `${atom}: ${delta.toFixed(3)}`).join(" · ")}</td><td className="p-2 text-right text-[#00c9a7]">{item.perturbationPpm.toFixed(4)}</td></tr>)}</tbody></table></div>}
  </section>;
}
