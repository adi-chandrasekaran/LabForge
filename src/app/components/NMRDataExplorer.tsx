import { useEffect, useMemo, useState } from "react";
import { Atom, Beaker, ChevronRight, FlaskConical, RefreshCw, Waves } from "lucide-react";
import { Button } from "./ui/button";
import {
  fetchNMRAssignments,
  fetchNMRChemicalShifts,
  fetchNMRLigands,
  fetchNMRPeaks,
  fetchNMRProteins,
  fetchNMRResidues,
  fetchNMRSamples,
  fetchNMRSpectra,
  type NMRAssignmentRecord,
  type NMRChemicalShiftRecord,
  type NMRLigandRecord,
  type NMRPeakRecord,
  type NMRProteinRecord,
  type NMRResidueRecord,
  type NMRSampleRecord,
  type NMRSpectrumRecord,
} from "../api";

const panel = "border border-border rounded-sm bg-card";

function Empty({ children }: { children: string }) {
  return <div className="p-5 text-[9px] text-muted-foreground">{children}</div>;
}

export default function NMRDataExplorer() {
  const [proteins, setProteins] = useState<NMRProteinRecord[]>([]);
  const [samples, setSamples] = useState<NMRSampleRecord[]>([]);
  const [ligands, setLigands] = useState<NMRLigandRecord[]>([]);
  const [spectra, setSpectra] = useState<NMRSpectrumRecord[]>([]);
  const [residues, setResidues] = useState<NMRResidueRecord[]>([]);
  const [peaks, setPeaks] = useState<NMRPeakRecord[]>([]);
  const [assignments, setAssignments] = useState<NMRAssignmentRecord[]>([]);
  const [shifts, setShifts] = useState<NMRChemicalShiftRecord[]>([]);
  const [proteinId, setProteinId] = useState<string | null>(null);
  const [spectrumId, setSpectrumId] = useState<string | null>(null);
  const [peakId, setPeakId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [residuesLoading, setResiduesLoading] = useState(false);
  const [spectrumLoading, setSpectrumLoading] = useState(false);
  const [assignmentsLoading, setAssignmentsLoading] = useState(false);
  const [refreshVersion, setRefreshVersion] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [residueError, setResidueError] = useState<string | null>(null);
  const [spectrumError, setSpectrumError] = useState<string | null>(null);
  const [assignmentError, setAssignmentError] = useState<string | null>(null);

  async function load() {
    setLoading(true);
    try {
      const [nextProteins, nextSamples, nextLigands, nextSpectra] = await Promise.all([
        fetchNMRProteins(), fetchNMRSamples(), fetchNMRLigands(), fetchNMRSpectra(),
      ]);
      setProteins(nextProteins); setSamples(nextSamples); setLigands(nextLigands); setSpectra(nextSpectra);
      setProteinId(current => current && nextProteins.some(value => value.id === current) ? current : nextProteins[0]?.id ?? null);
      setSpectrumId(current => current && nextSpectra.some(value => value.id === current) ? current : nextSpectra[0]?.id ?? null);
      setRefreshVersion(current => current + 1);
      setError(null);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Unable to load NMR records.");
    } finally { setLoading(false); }
  }

  useEffect(() => { void load(); }, []);
  useEffect(() => {
    let cancelled = false;
    setResidues([]);
    setResidueError(null);
    if (!proteinId) { setResiduesLoading(false); return; }
    setResiduesLoading(true);
    void fetchNMRResidues(proteinId)
      .then(values => { if (!cancelled) setResidues(values); })
      .catch(reason => { if (!cancelled) setResidueError(reason instanceof Error ? reason.message : "Unable to load residues for this protein."); })
      .finally(() => { if (!cancelled) setResiduesLoading(false); });
    return () => { cancelled = true; };
  }, [proteinId, refreshVersion]);
  useEffect(() => {
    let cancelled = false;
    setPeakId(null); setAssignments([]); setPeaks([]); setShifts([]);
    setSpectrumError(null);
    if (!spectrumId) { setSpectrumLoading(false); return; }
    setSpectrumLoading(true);
    void Promise.all([fetchNMRPeaks(spectrumId), fetchNMRChemicalShifts(spectrumId)])
      .then(([nextPeaks, nextShifts]) => {
        if (cancelled) return;
        setPeaks(nextPeaks); setShifts(nextShifts); setPeakId(nextPeaks[0]?.id ?? null);
      })
      .catch(reason => { if (!cancelled) setSpectrumError(reason instanceof Error ? reason.message : "Unable to load peaks and shifts for this spectrum."); })
      .finally(() => { if (!cancelled) setSpectrumLoading(false); });
    return () => { cancelled = true; };
  }, [spectrumId, refreshVersion]);
  useEffect(() => {
    let cancelled = false;
    setAssignments([]);
    setAssignmentError(null);
    if (!peakId) { setAssignmentsLoading(false); return; }
    setAssignmentsLoading(true);
    void fetchNMRAssignments(peakId)
      .then(values => { if (!cancelled) setAssignments(values); })
      .catch(reason => { if (!cancelled) setAssignmentError(reason instanceof Error ? reason.message : "Unable to load assignments for this peak."); })
      .finally(() => { if (!cancelled) setAssignmentsLoading(false); });
    return () => { cancelled = true; };
  }, [peakId, refreshVersion]);

  const selectedProtein = useMemo(() => proteins.find(value => value.id === proteinId), [proteins, proteinId]);
  const selectedSpectrum = useMemo(() => spectra.find(value => value.id === spectrumId), [spectra, spectrumId]);

  return <div data-testid="nmr-data-explorer">
    {(error || residueError || spectrumError || assignmentError) && <div role="alert" className="mb-4 border border-red-400/25 bg-red-400/10 p-3 text-[10px] text-red-200">{error ?? residueError ?? spectrumError ?? assignmentError}</div>}
    <div className="mb-5 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
      {[
        ["Proteins", proteins.length, Atom], ["Samples", samples.length, Beaker], ["Ligands", ligands.length, FlaskConical], ["Spectra", spectra.length, Waves],
      ].map(([name, count, Icon]) => <div key={String(name)} className={`${panel} p-4`}><div className="flex items-center justify-between"><span className="text-[9px] text-muted-foreground">{name as string}</span><Icon className="h-4 w-4 text-[#00c9a7]" /></div><div className="mt-2 text-xl text-foreground">{count as number}</div></div>)}
    </div>
    <div className="mb-4 flex justify-end"><Button variant="outline" size="sm" onClick={() => void load()} disabled={loading}><RefreshCw className={`h-3 w-3 ${loading ? "animate-spin" : ""}`} />Refresh records</Button></div>
    <div className="grid gap-5 xl:grid-cols-2">
      <section className={panel}>
        <div className="border-b border-border p-4"><h2 className="text-xs font-semibold">Proteins and residues</h2><p className="mt-1 text-[8px] text-muted-foreground">Select a protein to inspect its sequence records.</p></div>
        {proteins.length === 0 ? <Empty>No proteins have been added yet.</Empty> : <div className="grid min-h-72 sm:grid-cols-[0.8fr_1.2fr]">
          <div className="border-r border-border">{proteins.map(protein => <button key={protein.id} type="button" onClick={() => setProteinId(protein.id)} className={`flex w-full items-center justify-between border-b border-border p-3 text-left ${protein.id === proteinId ? "bg-[#00c9a7]/10 text-[#00c9a7]" : "text-muted-foreground hover:bg-secondary/40 hover:text-foreground"}`}><span><span className="block text-[10px]">{protein.name}</span><span className="mt-1 block text-[8px] opacity-70">{protein.constructName || `${protein.sequence.length} aa`} · {protein.residueCount} residues</span></span><ChevronRight className="h-3 w-3" /></button>)}</div>
          <div className="max-h-80 overflow-auto p-3">{selectedProtein && <div className="mb-3 text-[8px] text-muted-foreground">{selectedProtein.isotopeLabels.join(", ") || "No isotope labels"}</div>}{residuesLoading ? <Empty>Loading residues…</Empty> : residueError ? <Empty>Residue data unavailable.</Empty> : residues.length === 0 ? <Empty>No residues stored for this protein.</Empty> : <div className="space-y-1">{residues.map(residue => <div key={residue.id} className="grid grid-cols-[42px_1fr] border border-border bg-background px-2 py-1.5 text-[9px]"><span className="text-[#00c9a7]">{residue.oneLetterCode}{residue.sequenceNumber}{residue.insertionCode}</span><span className="text-muted-foreground">{residue.residueName}{residue.notes ? ` · ${residue.notes}` : ""}</span></div>)}</div>}</div>
        </div>}
      </section>

      <section className={panel}>
        <div className="border-b border-border p-4"><h2 className="text-xs font-semibold">Spectra and peak data</h2><p className="mt-1 text-[8px] text-muted-foreground">Inspect stored positions, assignments, and chemical shifts.</p></div>
        {spectra.length === 0 ? <Empty>No spectra have been added yet.</Empty> : <div className="p-3">
          <select value={spectrumId ?? ""} onChange={event => setSpectrumId(event.target.value)} className="w-full border border-border bg-background p-2 text-[9px] text-foreground" aria-label="Select spectrum">{spectra.map(spectrum => <option key={spectrum.id} value={spectrum.id}>{spectrum.name} · {spectrum.experimentType}</option>)}</select>
          {selectedSpectrum && <div className="mt-2 flex flex-wrap gap-1.5">{selectedSpectrum.nuclei.map(nucleus => <span key={nucleus} className="border border-violet-400/25 bg-violet-400/10 px-2 py-1 text-[8px] text-violet-200">{nucleus}</span>)}<span className="border border-border px-2 py-1 text-[8px] text-muted-foreground">{selectedSpectrum.status}</span></div>}
          <div className="mt-4 grid gap-3 sm:grid-cols-2">
            <div><div className="mb-2 text-[9px] text-foreground">Peaks ({peaks.length})</div><div className="max-h-56 space-y-1 overflow-auto">{spectrumLoading ? <Empty>Loading peaks…</Empty> : spectrumError ? <Empty>Peak data unavailable.</Empty> : peaks.length === 0 ? <Empty>No peaks stored.</Empty> : peaks.map(peak => <button key={peak.id} type="button" onClick={() => setPeakId(peak.id)} className={`w-full border p-2 text-left text-[9px] ${peak.id === peakId ? "border-[#00c9a7]/40 bg-[#00c9a7]/10" : "border-border bg-background"}`}><span className="text-foreground">{peak.label || "Unlabelled peak"}</span><span className="mt-1 block text-muted-foreground">{peak.positionsPpm.map(value => value.toFixed(3)).join(" / ")} ppm · {peak.assignmentCount} assignments</span></button>)}</div></div>
            <div><div className="mb-2 text-[9px] text-foreground">Assignments ({assignments.length})</div><div className="max-h-56 space-y-1 overflow-auto">{assignmentsLoading ? <Empty>Loading assignments…</Empty> : assignmentError ? <Empty>Assignment data unavailable.</Empty> : assignments.length === 0 ? <Empty>{peakId ? "No assignments stored for this peak." : "Select an assigned peak."}</Empty> : assignments.map(item => <div key={item.id} className="border border-border bg-background p-2 text-[9px]"><span className="text-violet-200">{item.atomNames.join(" / ")}</span><span className="block text-muted-foreground">{item.residueId} · {item.status}{item.confidence != null ? ` · ${(item.confidence * 100).toFixed(0)}%` : ""}</span></div>)}</div></div>
          </div>
          <div className="mt-4 border-t border-border pt-3"><div className="mb-2 text-[9px] text-foreground">Chemical shifts ({shifts.length})</div>{spectrumLoading ? <Empty>Loading chemical shifts…</Empty> : spectrumError ? <Empty>Chemical-shift data unavailable.</Empty> : shifts.length === 0 ? <Empty>No chemical shifts stored.</Empty> : <div className="max-h-44 overflow-auto"><table className="w-full text-left text-[8px]"><thead className="text-muted-foreground"><tr><th className="p-2">Residue</th><th className="p-2">Atom</th><th className="p-2">Nucleus</th><th className="p-2 text-right">ppm</th></tr></thead><tbody>{shifts.map(shift => <tr key={shift.id} className="border-t border-border"><td className="p-2 text-muted-foreground">{shift.residueId}</td><td className="p-2">{shift.atomName}</td><td className="p-2 text-violet-200">{shift.nucleus}</td><td className="p-2 text-right text-[#00c9a7]">{shift.valuePpm.toFixed(3)}</td></tr>)}</tbody></table></div>}</div>
        </div>}
      </section>
    </div>
    {(samples.length > 0 || ligands.length > 0) && <div className="mt-5 grid gap-5 xl:grid-cols-2"><section className={`${panel} p-4`}><h2 className="text-xs font-semibold">Samples</h2><div className="mt-3 space-y-2">{samples.map(sample => <div key={sample.id} className="border border-border bg-background p-3 text-[9px]"><span>{sample.name}</span><span className="block text-muted-foreground">{sample.sampleType}{sample.concentrationValue != null ? ` · ${sample.concentrationValue} ${sample.concentrationUnit ?? ""}` : ""}{sample.ph != null ? ` · pH ${sample.ph}` : ""}</span></div>)}</div></section><section className={`${panel} p-4`}><h2 className="text-xs font-semibold">Ligands</h2>{ligands.length === 0 ? <Empty>No ligands have been added yet.</Empty> : <div className="mt-3 space-y-2">{ligands.map(ligand => <div key={ligand.id} className="border border-border bg-background p-3 text-[9px]"><span>{ligand.name}</span><span className="block text-muted-foreground">{ligand.identifier || ligand.molecularFormula || "No identifier"}</span></div>)}</div>}</section></div>}
  </div>;
}
