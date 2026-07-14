import { useState, useRef } from "react";
import {
  ChevronRight, ChevronDown, CheckCircle2, Clock, Play, AlertTriangle,
  FileText, Download, Settings, Plus, CornerDownRight, Pencil, X,
  Trash2, GripVertical, Hash, ArrowRight, FlaskConical,
} from "lucide-react";
import * as Dialog from "@radix-ui/react-dialog";
import CalculatorWidget from "../components/CalculatorWidget";
import type { WorkflowStep, IOItem, Param, StepStatus, BranchTrack } from "../types";

// ─── INITIAL DATA ──────────────────────────────────────────────────────────────
let _id = 100;
const uid = () => `s${++_id}`;
const pid = () => `p${++_id}`;
const iid = () => `i${++_id}`;

const mk = (id: string, index: number, label: string, sublabel: string | undefined, status: StepStatus, duration: string,
  inputs: Omit<IOItem, "id">[], parameters: Omit<Param, "id">[], outputs: Omit<IOItem, "id">[], notes?: string
): WorkflowStep => ({
  id, index, label, sublabel, status, duration,
  inputs: inputs.map(i => ({ ...i, id: iid() })),
  parameters: parameters.map(p => ({ ...p, id: pid() })),
  outputs: outputs.map(o => ({ ...o, id: iid() })),
  notes,
});

const BATCH1_INIT: WorkflowStep[] = [
  mk("b1-01", 1, "Cell Lysis", undefined, "complete", "2 hr",
    [{ name: "E. coli pellet (His-SUMO-ANC2)", type: "sample", value: "~8 g" },
     { name: "Lysis Buffer", type: "buffer", value: "40 mL", note: "50 mM Tris pH 8, 300 mM NaCl, 10 mM imidazole" },
     { name: "Lysozyme", type: "reagent", value: "1 mg/mL" },
     { name: "cOmplete Protease Inhibitor", type: "reagent", value: "1 tablet/50 mL" },
     { name: "Sonicator (Branson 450D)", type: "equipment" }],
    [{ label: "Sonication", value: "6×30s on/60s off, 40% amplitude" },
     { label: "Temperature", value: "4 °C (ice bath)" },
     { label: "Centrifugation", value: "15,000 × g, 30 min, 4 °C" }],
    [{ name: "Clarified lysate (Sup 1)", type: "sample", note: "Proceed to Ni-NTA" },
     { name: "Cell debris pellet", type: "waste" }],
    "Keep on ice throughout. Verify lysis by OD600 drop."
  ),
  mk("b1-02", 2, "Supernatant (Sup 1)", "Centrifugation", "complete", "45 min",
    [{ name: "Crude lysate", type: "sample" },
     { name: "Beckman Avanti J-26S", type: "equipment" }],
    [{ label: "Speed", value: "15,000 × g" }, { label: "Duration", value: "30 min" }, { label: "Temp", value: "4 °C" }],
    [{ name: "Sup 1 (clarified)", type: "sample" }, { name: "Pellet", type: "waste", note: "Save for troubleshooting" }]
  ),
  mk("b1-03", 3, "Ni-NTA Affinity Column", "Protein binds Ni resin", "complete", "3 hr",
    [{ name: "Sup 1", type: "sample" },
     { name: "Ni-NTA Agarose", type: "reagent", value: "5 mL bed" },
     { name: "Equilibration Buffer", type: "buffer", value: "25 mL", note: "50 mM Tris pH 8, 300 mM NaCl, 10 mM imidazole" },
     { name: "Wash Buffer", type: "buffer", value: "50 mL", note: "25 mM imidazole" },
     { name: "ÄKTA Pure FPLC", type: "equipment" }],
    [{ label: "Flow rate", value: "1 mL/min" }, { label: "Wash", value: "5 CV at 25 mM imidazole" }, { label: "Monitor", value: "A280" }],
    [{ name: "Column-bound His-SUMO-ANC2", type: "sample" }, { name: "Flow-through", type: "waste" }]
  ),
  mk("b1-04", 4, "Elution", "Imidazole Buffer", "complete", "1 hr",
    [{ name: "Bound protein on Ni-NTA", type: "sample" },
     { name: "Elution Buffer", type: "buffer", value: "15 mL", note: "250 mM imidazole" }],
    [{ label: "Imidazole", value: "250 mM" }, { label: "Mode", value: "Step elution" }, { label: "Fraction size", value: "2 mL" }],
    [{ name: "His-SUMO-ANC2 eluate", type: "sample", note: "Pool A280+ fractions" }]
  ),
  mk("b1-05", 5, "Dialysis", "Remove Imidazole", "running", "Overnight",
    [{ name: "Pooled eluate", type: "sample" },
     { name: "Dialysis Buffer", type: "buffer", value: "2×2 L", note: "50 mM Tris pH 8, 150 mM NaCl, 1 mM DTT" },
     { name: "SnakeSkin Tubing MWCO 10 kDa", type: "equipment" }],
    [{ label: "Temp", value: "4 °C" }, { label: "Duration", value: "Overnight" }, { label: "Buffer changes", value: "2×2 L" }],
    [{ name: "Imidazole-free His-SUMO-ANC2", type: "sample" }],
    "Confirm imidazole removal before cleavage step."
  ),
  mk("b1-06", 6, "SUMO Cleavage", "Remove His-SUMO Tag", "pending", "Overnight",
    [{ name: "Dialyzed His-SUMO-ANC2", type: "sample" },
     { name: "ULP1 SUMO Protease", type: "reagent", value: "1:100 w/w" }],
    [{ label: "Ratio", value: "1:100 (protease:protein)" }, { label: "Temp", value: "4 °C" }, { label: "Duration", value: "16 hr" }],
    [{ name: "Cleaved ANC2 (tag-free)", type: "sample" }, { name: "Free His-SUMO tag", type: "sample" }],
    "Verify cleavage by SDS-PAGE before next step. Expect ~12–15 kDa band shift."
  ),
  mk("b1-07", 7, "Reverse Ni-NTA Column", "Expected purification", "pending", "2 hr",
    [{ name: "Cleavage reaction mix", type: "sample" },
     { name: "Ni-NTA Agarose (pre-equilibrated)", type: "reagent", value: "2 mL bed" },
     { name: "Binding Buffer", type: "buffer", note: "10 mM imidazole" }],
    [{ label: "Mode", value: "Gravity flow / batch binding" }, { label: "Incubation", value: "30 min, 4 °C" }],
    [{ name: "Tag-free ANC2 (flow-through)", type: "sample" }, { name: "His-SUMO + ULP1 (bound)", type: "waste" }]
  ),
  mk("b1-08", 8, "SDS-PAGE", "Check cleavage & purity", "pending", "2 hr",
    [{ name: "ANC2 flow-through", type: "sample", value: "10 µL" },
     { name: "12% polyacrylamide gel", type: "equipment" },
     { name: "Protein Ladder (3–250 kDa)", type: "reagent", value: "5 µL" }],
    [{ label: "Voltage", value: "200 V, 45 min" }, { label: "Expected band", value: "~12–15 kDa (ANC2)" }],
    [{ name: "Gel image (.tiff)", type: "data" }, { name: "Purity assessment", type: "data", note: ">80% to proceed" }]
  ),
  mk("b1-09", 9, "Concentrate", undefined, "pending", "1 hr",
    [{ name: "ANC2 pool", type: "sample" }, { name: "Amicon Ultra-15 MWCO 10 kDa", type: "equipment" }],
    [{ label: "Speed", value: "3,000 × g" }, { label: "Target", value: "5–10 mg/mL" }, { label: "Final vol", value: "~1–2 mL" }],
    [{ name: "Concentrated ANC2", type: "sample" }]
  ),
  mk("b1-10", 10, "Preparative SEC", "Gel Filtration", "pending", "4 hr",
    [{ name: "Concentrated ANC2", type: "sample", value: "≤500 µL" },
     { name: "Superdex 75 16/600", type: "equipment", note: "120 mL bed" },
     { name: "SEC Running Buffer", type: "buffer", value: "500 mL", note: "20 mM HEPES pH 7.5, 150 mM NaCl, 1 mM DTT" }],
    [{ label: "Flow rate", value: "1 mL/min" }, { label: "Predicted elution", value: "~75 mL" }],
    [{ name: "SEC peak fractions", type: "sample" }, { name: "A280 chromatogram", type: "data" }],
    "Predicted elution at ~75 mL. Collect symmetric peak fractions only."
  ),
  mk("b1-11", 11, "Collect Fractions", "~75 mL predicted elution", "pending", "30 min",
    [{ name: "SEC peak fractions", type: "sample" }],
    [{ label: "Criterion", value: "A280 peak only" }, { label: "Pool volume", value: "~5–8 mL" }],
    [{ name: "Pooled peak fractions", type: "sample" }]
  ),
  mk("b1-12", 12, "SDS-PAGE", "Final purity check", "pending", "2 hr",
    [{ name: "Pooled SEC fractions", type: "sample", value: "10 µL/lane" },
     { name: "12% SDS-PAGE gel", type: "equipment" }],
    [{ label: "Expected band", value: "~12–15 kDa" }, { label: "Purity threshold", value: ">95%" }],
    [{ name: "Final purity gel image", type: "data" }, { name: "Final concentration (A280)", type: "data" }]
  ),
  mk("b1-13", 13, "Pure ANC2", "Final product", "pending", "—",
    [{ name: "Purified ANC2 fractions", type: "sample" }, { name: "Protein LoBind tubes", type: "equipment" }],
    [{ label: "Aliquot size", value: "50–100 µL" }, { label: "Storage", value: "-80 °C, flash-frozen" }],
    [{ name: "Pure ANC2 (flash-frozen aliquots)", type: "sample" }, { name: "Yield report", type: "data" }]
  ),
];

const BATCH2_INIT: WorkflowStep[] = [
  mk("b2-01", 1, "Cell Lysis", "Denaturing conditions", "pending", "2 hr",
    [{ name: "E. coli pellet (His-SUMO-ANC2)", type: "sample", value: "~8 g" },
     { name: "Denaturing Lysis Buffer", type: "buffer", value: "40 mL", note: "50 mM Tris pH 8, 300 mM NaCl, 10 mM imidazole, 8 M urea" }],
    [{ label: "Sonication", value: "6×30s on/60s off" }, { label: "Centrifugation", value: "15,000 × g, 30 min" }],
    [{ name: "Denatured lysate (Sup 1)", type: "sample" }, { name: "Insoluble pellet", type: "waste" }],
    "Denaturing lysis to solubilize inclusion bodies."
  ),
  mk("b2-02", 2, "Supernatant", "Sup 1 + Sup 2 + Refolded Fraction", "pending", "1 hr",
    [{ name: "Denatured lysate", type: "sample" }, { name: "Wash Buffer (8 M urea)", type: "buffer" }],
    [{ label: "Sup 2", value: "Re-extract pellet in denaturing buffer" }, { label: "Pool", value: "Sup 1 + Sup 2 + refolded fraction" }],
    [{ name: "Combined denatured supernatant", type: "sample" }]
  ),
  mk("b2-03", 3, "Ni-NTA Affinity Column", "Protein binds Ni resin", "pending", "3 hr",
    [{ name: "Combined denatured sup", type: "sample" },
     { name: "Ni-NTA Agarose", type: "reagent", value: "5 mL bed" },
     { name: "Denaturing Binding Buffer", type: "buffer", note: "8 M urea, 10 mM imidazole" }],
    [{ label: "Flow rate", value: "0.5–1 mL/min" }, { label: "Note", value: "His-tag binds under denaturing conditions" }],
    [{ name: "Denatured His-SUMO-ANC2 (bound)", type: "sample" }, { name: "Unbound contaminants", type: "waste" }]
  ),
  mk("b2-04", 4, "Elution", "Imidazole Buffer", "pending", "1 hr",
    [{ name: "Bound protein on Ni-NTA", type: "sample" },
     { name: "Denaturing Elution Buffer", type: "buffer", note: "8 M urea, 250 mM imidazole" }],
    [{ label: "Imidazole", value: "250 mM" }, { label: "Volume", value: "~10–15 mL" }],
    [{ name: "Denatured His-SUMO-ANC2 eluate", type: "sample" }]
  ),
  mk("b2-05", 5, "Dialysis", "Against 8.3% Acetic Acid", "pending", "Overnight",
    [{ name: "Denatured eluate", type: "sample" },
     { name: "8.3% Acetic Acid", type: "buffer", value: "2×2 L" },
     { name: "Dialysis Tubing MWCO 3.5 kDa", type: "equipment" }],
    [{ label: "Dialysate", value: "8.3% acetic acid (v/v)" }, { label: "Duration", value: "Overnight, 4 °C" }],
    [{ name: "Acid-treated sample", type: "sample" }, { name: "Precipitated contaminants", type: "waste" }],
    "Acetic acid selectively precipitates E. coli contaminants. Centrifuge after dialysis."
  ),
  mk("b2-06", 6, "Protein Refolding", "+100 mM NaCl additive", "pending", "Overnight",
    [{ name: "Clarified acid-treated sample", type: "sample" },
     { name: "Refolding Buffer", type: "buffer", note: "50 mM Tris pH 8, 150 mM NaCl, 1 mM DTT" },
     { name: "NaCl additive", type: "reagent", value: "+100 mM final" }],
    [{ label: "Method", value: "Stepwise dialysis into refolding buffer" }, { label: "NaCl additive", value: "+100 mM" }, { label: "Temp", value: "4 °C" }],
    [{ name: "Refolded His-SUMO-ANC2", type: "sample" }, { name: "Aggregate fraction", type: "waste" }],
    "+100 mM NaCl reduces non-specific electrostatic interactions during refolding."
  ),
  mk("b2-07", 7, "Concentrate Sample", "Final Volume = 20 mL, ~200 mM NaCl", "pending", "1 hr",
    [{ name: "Refolded His-SUMO-ANC2", type: "sample" }, { name: "Amicon Ultra-15 MWCO 10 kDa", type: "equipment" }],
    [{ label: "Target volume", value: "20 mL" }, { label: "NaCl final", value: "~200 mM" }],
    [{ name: "Concentrated ANC2 (20 mL)", type: "sample", note: "★ Rejoins standard protocol at Dialysis/Buffer Exchange" }],
    "★ Standard protocol resumes here — same as Batch 1 Dialysis step."
  ),
  mk("b2-08", 8, "ULFS Cleavage", "Remove tag", "pending", "Overnight",
    [{ name: "Refolded His-SUMO-ANC2 (post-exchange)", type: "sample" },
     { name: "SUMO Protease ULP1/ULFS", type: "reagent", value: "1:100 w/w" }],
    [{ label: "Ratio", value: "1:100 (w/w)" }, { label: "Temp", value: "4 °C" }, { label: "Duration", value: "16 hr" }],
    [{ name: "Cleaved ANC2 (tag-free)", type: "sample" }, { name: "Free His-SUMO tag", type: "sample" }]
  ),
  mk("b2-09", 9, "SP Sepharose Ion Exchange", "Buffer A: 25 mM NaCl · Buffer B: 1 M NaCl", "pending", "3 hr",
    [{ name: "Cleaved ANC2 mixture", type: "sample" },
     { name: "HiTrap SP HP 5 mL", type: "equipment" },
     { name: "Buffer A", type: "buffer", note: "50 mM Tris pH 8, 25 mM NaCl" },
     { name: "Buffer B", type: "buffer", note: "50 mM Tris pH 8, 1 M NaCl" }],
    [{ label: "Equilibration", value: "5 CV Buffer A" }, { label: "Gradient", value: "0–100% B over 20 CV" }, { label: "Flow rate", value: "2 mL/min" }],
    [{ name: "Purified ANC2 fractions (IEX)", type: "sample" }, { name: "IEX chromatogram", type: "data" }],
    "Cation exchange separates tag-free ANC2 from His-SUMO and contaminants."
  ),
  mk("b2-10", 10, "Purified Protein", "Final product (Batch 2)", "pending", "—",
    [{ name: "ANC2 from SP Sepharose", type: "sample" }, { name: "Protein LoBind tubes", type: "equipment" }],
    [{ label: "Aliquot size", value: "50–100 µL" }, { label: "Storage", value: "-80 °C, flash-frozen in LN2" }],
    [{ name: "Pure ANC2 Batch 2 (aliquots)", type: "sample" }, { name: "Final yield report", type: "data" }]
  ),
];

// ─── STATUS / TYPE CONFIGS ─────────────────────────────────────────────────────
const STATUS_CFG: Record<StepStatus, { label: string; text: string; bg: string; dot: string }> = {
  complete: { label: "DONE",    text: "text-emerald-400", bg: "bg-emerald-400/10 border-emerald-400/25", dot: "bg-emerald-400" },
  running:  { label: "RUNNING", text: "text-[#00c9a7]",   bg: "bg-[#00c9a7]/10 border-[#00c9a7]/30",   dot: "bg-[#00c9a7] animate-pulse" },
  pending:  { label: "PENDING", text: "text-slate-500",   bg: "bg-transparent border-slate-700/40",    dot: "bg-slate-600" },
  error:    { label: "ERROR",   text: "text-red-400",     bg: "bg-red-400/10 border-red-400/25",       dot: "bg-red-400" },
};
const IO_DOT: Record<IOItem["type"], string> = {
  sample: "bg-sky-400", reagent: "bg-violet-400", buffer: "bg-teal-400",
  equipment: "bg-amber-400", waste: "bg-slate-500", data: "bg-emerald-400",
};
const IO_LABEL: Record<IOItem["type"], string> = {
  sample: "SAMPLE", reagent: "REAGENT", buffer: "BUFFER",
  equipment: "EQUIP", waste: "WASTE", data: "DATA",
};
const IO_TYPES = ["sample","reagent","buffer","equipment","waste","data"] as const;

// ─── INNER SCHEMATIC ───────────────────────────────────────────────────────────
function InnerSchematic({ step }: { step: WorkflowStep }) {
  return (
    <div className="mt-1.5 ml-8 border border-border rounded-sm bg-[#0a0f16] p-4 space-y-4">
      <div className="text-[9px] font-mono tracking-[0.2em] text-muted-foreground uppercase">
        Inner Schematic — Step {String(step.index).padStart(2, "0")} / {step.label}
      </div>
      <div className="grid grid-cols-[1fr_110px_1fr] gap-3 items-start">
        {/* INPUTS */}
        <div>
          <div className="text-[9px] font-mono tracking-widest text-muted-foreground border-b border-border pb-1 mb-2">INPUTS</div>
          <div className="space-y-2">
            {step.inputs.map((inp) => (
              <div key={inp.id} className="flex items-start gap-2">
                <div className={`w-1.5 h-1.5 rounded-full flex-shrink-0 mt-[5px] ${IO_DOT[inp.type]}`} />
                <div>
                  <div className="text-[11px] font-mono text-foreground">
                    {inp.name}{inp.value && <span className="text-accent ml-1.5 text-[10px]">{inp.value}</span>}
                  </div>
                  <div className="text-[9px] font-mono text-muted-foreground">{IO_LABEL[inp.type]}{inp.note && ` · ${inp.note}`}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
        {/* CENTER */}
        <div className="flex flex-col items-center gap-1 pt-5">
          <ArrowRight className="w-3 h-3 text-[#00c9a7]/50" />
          <div className="border border-[#00c9a7]/30 bg-[#00c9a7]/5 rounded-sm px-2 py-3 text-center w-full">
            <div className="text-[9px] font-mono text-muted-foreground mb-1">PROCESS</div>
            <div className="text-[10px] font-mono text-[#00c9a7] font-medium leading-tight">{step.label}</div>
            {step.duration && step.duration !== "—" && (
              <div className="mt-1.5 pt-1.5 border-t border-border">
                <div className="text-[8px] font-mono text-muted-foreground">DURATION</div>
                <div className="text-[9px] font-mono text-foreground">{step.duration}</div>
              </div>
            )}
          </div>
          <ArrowRight className="w-3 h-3 text-[#00c9a7]/50" />
        </div>
        {/* OUTPUTS */}
        <div>
          <div className="text-[9px] font-mono tracking-widest text-muted-foreground border-b border-border pb-1 mb-2">OUTPUTS</div>
          <div className="space-y-2">
            {step.outputs.map((out) => (
              <div key={out.id} className="flex items-start gap-2">
                <div className={`w-1.5 h-1.5 rounded-full flex-shrink-0 mt-[5px] ${IO_DOT[out.type]}`} />
                <div>
                  <div className="text-[11px] font-mono text-foreground">{out.name}</div>
                  <div className="text-[9px] font-mono text-muted-foreground">{IO_LABEL[out.type]}{out.note && ` · ${out.note}`}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
      {step.parameters.length > 0 && (
        <div className="pt-3 border-t border-border">
          <div className="text-[9px] font-mono tracking-widest text-muted-foreground mb-2">PARAMETERS</div>
          <div className="flex flex-wrap gap-1.5">
            {step.parameters.map(p => (
              <div key={p.id} className="flex items-center gap-1.5 bg-secondary border border-border rounded-sm px-2 py-0.5">
                <span className="text-[9px] font-mono text-muted-foreground">{p.label}:</span>
                <span className="text-[9px] font-mono text-foreground font-medium">{p.value}</span>
              </div>
            ))}
          </div>
        </div>
      )}
      {step.notes && (
        <div className="pt-3 border-t border-border flex items-start gap-2">
          <FileText className="w-3 h-3 text-muted-foreground mt-0.5 flex-shrink-0" />
          <span className="text-[10px] font-mono text-muted-foreground">{step.notes}</span>
        </div>
      )}
    </div>
  );
}

// ─── STEP CONNECTOR (+ and branch buttons) ─────────────────────────────────────
function StepConnector({ onAddStep, onAddBranch }: { onAddStep: () => void; onAddBranch: () => void }) {
  const [hovered, setHovered] = useState(false);
  return (
    <div
      className="ml-4 h-7 flex items-center relative"
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
    >
      <div className="w-px h-full bg-border" />
      {hovered && (
        <div className="absolute left-2 flex items-center gap-1 z-10">
          <button
            onClick={onAddStep}
            title="Add step here"
            className="w-6 h-6 rounded-sm border border-[#00c9a7]/50 bg-card hover:bg-[#00c9a7]/15 flex items-center justify-center transition-colors group"
          >
            <Plus className="w-3 h-3 text-[#00c9a7]" />
          </button>
          <button
            onClick={onAddBranch}
            title="Diverge branch here"
            className="w-6 h-6 rounded-sm border border-amber-500/50 bg-card hover:bg-amber-500/15 flex items-center justify-center transition-colors"
          >
            <CornerDownRight className="w-3 h-3 text-amber-400" />
          </button>
        </div>
      )}
    </div>
  );
}

// ─── CALCULATOR POPUP ─────────────────────────────────────────────────────────
function CalcPopup({ open, onClose, onUse }: { open: boolean; onClose: () => void; onUse: (v: string) => void }) {
  return (
    <Dialog.Root open={open} onOpenChange={v => !v && onClose()}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/60 z-50" />
        <Dialog.Content className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-50 w-[680px] max-w-[95vw] max-h-[80vh] overflow-y-auto bg-background border border-border rounded-sm shadow-2xl p-5"
          style={{ fontFamily: "'JetBrains Mono', monospace" }}>
          <div className="flex items-center justify-between mb-4">
            <div>
              <div className="text-[9px] font-mono tracking-widest text-muted-foreground">QUICK CALCULATOR</div>
              <div className="text-sm font-mono text-foreground font-medium">Molarity Calculator</div>
            </div>
            <button onClick={onClose} className="text-muted-foreground hover:text-foreground transition-colors">
              <X className="w-4 h-4" />
            </button>
          </div>
          <CalculatorWidget onUseResult={(v) => { onUse(v); onClose(); }} compact />
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}

// ─── EDIT STEP DIALOG ─────────────────────────────────────────────────────────
function EditStepDialog({ step, open, onClose, onSave }: {
  step: WorkflowStep; open: boolean; onClose: () => void; onSave: (s: WorkflowStep) => void;
}) {
  const [draft, setDraft] = useState<WorkflowStep>(() => JSON.parse(JSON.stringify(step)));
  const [calcOpen, setCalcOpen] = useState(false);
  const insertRef = useRef<((v: string) => void) | null>(null);

  const openCalc = (setter: (v: string) => void) => {
    insertRef.current = setter;
    setCalcOpen(true);
  };

  const set = (key: keyof WorkflowStep, val: string) => setDraft(d => ({ ...d, [key]: val }));

  const setInput = (i: number, key: keyof IOItem, val: string) =>
    setDraft(d => { const inputs = [...d.inputs]; inputs[i] = { ...inputs[i], [key]: val }; return { ...d, inputs }; });

  const setOutput = (i: number, key: keyof IOItem, val: string) =>
    setDraft(d => { const outputs = [...d.outputs]; outputs[i] = { ...outputs[i], [key]: val }; return { ...d, outputs }; });

  const setParam = (i: number, key: keyof Param, val: string) =>
    setDraft(d => { const parameters = [...d.parameters]; parameters[i] = { ...parameters[i], [key]: val }; return { ...d, parameters }; });

  const addInput = () => setDraft(d => ({ ...d, inputs: [...d.inputs, { id: iid(), name: "", type: "reagent" }] }));
  const removeInput = (i: number) => setDraft(d => { const inputs = [...d.inputs]; inputs.splice(i, 1); return { ...d, inputs }; });
  const addOutput = () => setDraft(d => ({ ...d, outputs: [...d.outputs, { id: iid(), name: "", type: "sample" }] }));
  const removeOutput = (i: number) => setDraft(d => { const outputs = [...d.outputs]; outputs.splice(i, 1); return { ...d, outputs }; });
  const addParam = () => setDraft(d => ({ ...d, parameters: [...d.parameters, { id: pid(), label: "", value: "" }] }));
  const removeParam = (i: number) => setDraft(d => { const parameters = [...d.parameters]; parameters.splice(i, 1); return { ...d, parameters }; });

  const inputCls = "w-full bg-secondary border border-border text-[11px] font-mono text-foreground rounded-sm px-2 py-1 focus:outline-none focus:border-[#00c9a7]/50";
  const labelCls = "text-[9px] font-mono tracking-widest text-muted-foreground";

  return (
    <>
      <Dialog.Root open={open} onOpenChange={v => !v && onClose()}>
        <Dialog.Portal>
          <Dialog.Overlay className="fixed inset-0 bg-black/50 z-40" />
          <Dialog.Content
            className="fixed top-4 right-4 bottom-4 w-[520px] max-w-[95vw] overflow-y-auto bg-background border border-border rounded-sm shadow-2xl z-40 flex flex-col"
            style={{ fontFamily: "'JetBrains Mono', monospace" }}
          >
            {/* Header */}
            <div className="flex items-center justify-between px-5 py-4 border-b border-border flex-shrink-0">
              <div>
                <div className="text-[9px] font-mono tracking-widest text-muted-foreground">EDIT STEP</div>
                <div className="text-sm font-mono text-foreground font-medium">{step.label}</div>
              </div>
              <button onClick={onClose} className="text-muted-foreground hover:text-foreground"><X className="w-4 h-4" /></button>
            </div>

            <div className="flex-1 overflow-y-auto px-5 py-4 space-y-5">
              {/* Basic fields */}
              <div className="space-y-2">
                <div className="text-[9px] font-mono tracking-widest text-muted-foreground border-b border-border pb-1">STEP INFO</div>
                <div>
                  <div className={labelCls + " mb-1"}>Label</div>
                  <input className={inputCls} value={draft.label} onChange={e => set("label", e.target.value)} />
                </div>
                <div>
                  <div className={labelCls + " mb-1"}>Sublabel</div>
                  <input className={inputCls} value={draft.sublabel ?? ""} onChange={e => set("sublabel", e.target.value)} />
                </div>
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <div className={labelCls + " mb-1"}>Duration</div>
                    <input className={inputCls} value={draft.duration ?? ""} onChange={e => set("duration", e.target.value)} />
                  </div>
                  <div>
                    <div className={labelCls + " mb-1"}>Status</div>
                    <select className={inputCls + " cursor-pointer"} value={draft.status} onChange={e => set("status", e.target.value as StepStatus)}>
                      {(["complete","running","pending","error"] as StepStatus[]).map(s => (
                        <option key={s} value={s}>{s.toUpperCase()}</option>
                      ))}
                    </select>
                  </div>
                </div>
              </div>

              {/* Inputs */}
              <div className="space-y-2">
                <div className="flex items-center justify-between border-b border-border pb-1">
                  <div className="text-[9px] font-mono tracking-widest text-muted-foreground">INPUTS / MATERIALS</div>
                  <button onClick={addInput} className="flex items-center gap-1 text-[9px] font-mono text-[#00c9a7] hover:text-[#00b899] transition-colors">
                    <Plus className="w-3 h-3" />ADD
                  </button>
                </div>
                {draft.inputs.map((inp, i) => (
                  <div key={inp.id} className="border border-border rounded-sm p-2.5 space-y-1.5 relative bg-card">
                    <button onClick={() => removeInput(i)} className="absolute top-2 right-2 text-muted-foreground hover:text-red-400 transition-colors">
                      <Trash2 className="w-3 h-3" />
                    </button>
                    <div className="grid grid-cols-[1fr_80px] gap-1.5">
                      <div>
                        <div className={labelCls + " mb-0.5"}>Name</div>
                        <input className={inputCls} value={inp.name} onChange={e => setInput(i, "name", e.target.value)} />
                      </div>
                      <div>
                        <div className={labelCls + " mb-0.5"}>Type</div>
                        <select className={inputCls + " cursor-pointer"} value={inp.type} onChange={e => setInput(i, "type", e.target.value as IOItem["type"])}>
                          {IO_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
                        </select>
                      </div>
                    </div>
                    <div className="grid grid-cols-2 gap-1.5">
                      <div>
                        <div className={labelCls + " mb-0.5"}>Value / Amount</div>
                        <div className="flex gap-1">
                          <input className={inputCls} value={inp.value ?? ""} onChange={e => setInput(i, "value", e.target.value)} />
                          <button
                            onClick={() => openCalc(v => setInput(i, "value", v))}
                            title="Open calculator"
                            className="flex-shrink-0 w-7 h-[26px] border border-border bg-secondary hover:bg-[#00c9a7]/10 hover:border-[#00c9a7]/40 rounded-sm flex items-center justify-center text-muted-foreground hover:text-[#00c9a7] transition-colors"
                          >
                            <Hash className="w-3 h-3" />
                          </button>
                        </div>
                      </div>
                      <div>
                        <div className={labelCls + " mb-0.5"}>Note / Lot</div>
                        <input className={inputCls} value={inp.note ?? ""} onChange={e => setInput(i, "note", e.target.value)} />
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              {/* Parameters */}
              <div className="space-y-2">
                <div className="flex items-center justify-between border-b border-border pb-1">
                  <div className="text-[9px] font-mono tracking-widest text-muted-foreground">PARAMETERS</div>
                  <button onClick={addParam} className="flex items-center gap-1 text-[9px] font-mono text-[#00c9a7] hover:text-[#00b899] transition-colors">
                    <Plus className="w-3 h-3" />ADD
                  </button>
                </div>
                {draft.parameters.map((p, i) => (
                  <div key={p.id} className="flex items-center gap-1.5">
                    <div className="w-1 h-1 rounded-full bg-slate-500 flex-shrink-0" />
                    <input className={inputCls} placeholder="Parameter name" value={p.label} onChange={e => setParam(i, "label", e.target.value)} />
                    <span className="text-muted-foreground text-xs">:</span>
                    <input className={inputCls} placeholder="Value" value={p.value} onChange={e => setParam(i, "value", e.target.value)} />
                    <button onClick={() => openCalc(v => setParam(i, "value", v))}
                      title="Open calculator"
                      className="flex-shrink-0 w-7 h-[26px] border border-border bg-secondary hover:bg-[#00c9a7]/10 hover:border-[#00c9a7]/40 rounded-sm flex items-center justify-center text-muted-foreground hover:text-[#00c9a7] transition-colors"
                    >
                      <Hash className="w-3 h-3" />
                    </button>
                    <button onClick={() => removeParam(i)} className="flex-shrink-0 text-muted-foreground hover:text-red-400 transition-colors">
                      <Trash2 className="w-3 h-3" />
                    </button>
                  </div>
                ))}
              </div>

              {/* Outputs */}
              <div className="space-y-2">
                <div className="flex items-center justify-between border-b border-border pb-1">
                  <div className="text-[9px] font-mono tracking-widest text-muted-foreground">OUTPUTS</div>
                  <button onClick={addOutput} className="flex items-center gap-1 text-[9px] font-mono text-[#00c9a7] hover:text-[#00b899] transition-colors">
                    <Plus className="w-3 h-3" />ADD
                  </button>
                </div>
                {draft.outputs.map((out, i) => (
                  <div key={out.id} className="border border-border rounded-sm p-2.5 space-y-1.5 relative bg-card">
                    <button onClick={() => removeOutput(i)} className="absolute top-2 right-2 text-muted-foreground hover:text-red-400 transition-colors">
                      <Trash2 className="w-3 h-3" />
                    </button>
                    <div className="grid grid-cols-[1fr_80px] gap-1.5">
                      <div>
                        <div className={labelCls + " mb-0.5"}>Name</div>
                        <input className={inputCls} value={out.name} onChange={e => setOutput(i, "name", e.target.value)} />
                      </div>
                      <div>
                        <div className={labelCls + " mb-0.5"}>Type</div>
                        <select className={inputCls + " cursor-pointer"} value={out.type} onChange={e => setOutput(i, "type", e.target.value as IOItem["type"])}>
                          {IO_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
                        </select>
                      </div>
                    </div>
                    <div>
                      <div className={labelCls + " mb-0.5"}>Note / Expected value</div>
                      <div className="flex gap-1">
                        <input className={inputCls} value={out.note ?? ""} onChange={e => setOutput(i, "note", e.target.value)} />
                        <button onClick={() => openCalc(v => setOutput(i, "value", v))} title="Open calculator"
                          className="flex-shrink-0 w-7 h-[26px] border border-border bg-secondary hover:bg-[#00c9a7]/10 hover:border-[#00c9a7]/40 rounded-sm flex items-center justify-center text-muted-foreground hover:text-[#00c9a7] transition-colors">
                          <Hash className="w-3 h-3" />
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              {/* Notes */}
              <div>
                <div className={labelCls + " mb-1"}>NOTES</div>
                <textarea
                  className={inputCls + " min-h-[80px] resize-none"}
                  value={draft.notes ?? ""}
                  onChange={e => set("notes", e.target.value)}
                />
              </div>
            </div>

            {/* Footer */}
            <div className="flex items-center justify-end gap-2 px-5 py-3 border-t border-border flex-shrink-0">
              <button onClick={onClose} className="text-[10px] font-mono text-muted-foreground border border-border rounded-sm px-3 py-1.5 hover:bg-secondary transition-colors">
                CANCEL
              </button>
              <button
                onClick={() => { onSave(draft); onClose(); }}
                className="text-[10px] font-mono text-[#080c12] bg-[#00c9a7] hover:bg-[#00b899] border border-[#00c9a7] rounded-sm px-4 py-1.5 font-semibold transition-colors"
              >
                SAVE STEP
              </button>
            </div>
          </Dialog.Content>
        </Dialog.Portal>
      </Dialog.Root>

      {/* Nested calculator popup */}
      <CalcPopup
        open={calcOpen}
        onClose={() => setCalcOpen(false)}
        onUse={(v) => { insertRef.current?.(v); }}
      />
    </>
  );
}

// ─── ADD STEP MODAL ────────────────────────────────────────────────────────────
function AddStepModal({ open, onClose, onAdd }: {
  open: boolean; onClose: () => void; onAdd: (label: string, sublabel: string) => void;
}) {
  const [label, setLabel] = useState("");
  const [sublabel, setSublabel] = useState("");
  return (
    <Dialog.Root open={open} onOpenChange={v => !v && onClose()}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/50 z-50" />
        <Dialog.Content
          className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-50 w-80 bg-background border border-border rounded-sm shadow-2xl p-5"
          style={{ fontFamily: "'JetBrains Mono', monospace" }}
        >
          <div className="flex items-center justify-between mb-4">
            <div className="text-xs font-mono text-foreground font-medium">ADD NEW STEP</div>
            <button onClick={onClose}><X className="w-3.5 h-3.5 text-muted-foreground" /></button>
          </div>
          <div className="space-y-3">
            <div>
              <div className="text-[9px] font-mono tracking-widest text-muted-foreground mb-1">STEP NAME *</div>
              <input
                autoFocus
                className="w-full bg-secondary border border-border text-[11px] font-mono text-foreground rounded-sm px-2 py-1.5 focus:outline-none focus:border-[#00c9a7]/50"
                value={label}
                onChange={e => setLabel(e.target.value)}
                onKeyDown={e => e.key === "Enter" && label && (onAdd(label, sublabel), onClose(), setLabel(""), setSublabel(""))}
              />
            </div>
            <div>
              <div className="text-[9px] font-mono tracking-widest text-muted-foreground mb-1">SUBLABEL (optional)</div>
              <input
                className="w-full bg-secondary border border-border text-[11px] font-mono text-foreground rounded-sm px-2 py-1.5 focus:outline-none focus:border-[#00c9a7]/50"
                value={sublabel}
                onChange={e => setSublabel(e.target.value)}
              />
            </div>
            <div className="flex gap-2 pt-1">
              <button onClick={onClose} className="flex-1 text-[10px] font-mono text-muted-foreground border border-border rounded-sm py-1.5 hover:bg-secondary transition-colors">CANCEL</button>
              <button
                disabled={!label}
                onClick={() => { onAdd(label, sublabel); onClose(); setLabel(""); setSublabel(""); }}
                className="flex-1 text-[10px] font-mono text-[#080c12] bg-[#00c9a7] hover:bg-[#00b899] disabled:opacity-40 rounded-sm py-1.5 font-semibold transition-colors"
              >INSERT STEP</button>
            </div>
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}

// ─── ADD BRANCH MODAL ─────────────────────────────────────────────────────────
function AddBranchModal({ open, onClose, onAdd }: {
  open: boolean; onClose: () => void; onAdd: (label: string) => void;
}) {
  const [label, setLabel] = useState("");
  return (
    <Dialog.Root open={open} onOpenChange={v => !v && onClose()}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/50 z-50" />
        <Dialog.Content
          className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-50 w-80 bg-background border border-border rounded-sm shadow-2xl p-5"
          style={{ fontFamily: "'JetBrains Mono', monospace" }}
        >
          <div className="flex items-center justify-between mb-4">
            <div>
              <div className="text-[9px] font-mono tracking-widest text-muted-foreground">DIVERGE BRANCH</div>
              <div className="text-xs font-mono text-foreground font-medium">Add side track</div>
            </div>
            <button onClick={onClose}><X className="w-3.5 h-3.5 text-muted-foreground" /></button>
          </div>
          <div className="space-y-3">
            <p className="text-[10px] font-mono text-muted-foreground leading-relaxed">
              Branch steps run in parallel or as a detour before rejoining the main flow.
            </p>
            <div>
              <div className="text-[9px] font-mono tracking-widest text-muted-foreground mb-1">BRANCH LABEL *</div>
              <input
                autoFocus
                className="w-full bg-secondary border border-border text-[11px] font-mono text-foreground rounded-sm px-2 py-1.5 focus:outline-none focus:border-amber-400/50"
                value={label}
                onChange={e => setLabel(e.target.value)}
                placeholder="e.g. Troubleshooting run"
                onKeyDown={e => e.key === "Enter" && label && (onAdd(label), onClose(), setLabel(""))}
              />
            </div>
            <div className="flex gap-2 pt-1">
              <button onClick={onClose} className="flex-1 text-[10px] font-mono text-muted-foreground border border-border rounded-sm py-1.5 hover:bg-secondary transition-colors">CANCEL</button>
              <button
                disabled={!label}
                onClick={() => { onAdd(label); onClose(); setLabel(""); }}
                className="flex-1 text-[10px] font-mono text-[#080c12] bg-amber-400 hover:bg-amber-300 disabled:opacity-40 rounded-sm py-1.5 font-semibold transition-colors"
              >CREATE BRANCH</button>
            </div>
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}

// ─── STEP NODE ─────────────────────────────────────────────────────────────────
function StepNode({ step, expanded, onToggle, onEdit, isBranch }: {
  step: WorkflowStep; expanded: boolean; onToggle: () => void; onEdit: () => void; isBranch?: boolean;
}) {
  const sc = STATUS_CFG[step.status];
  return (
    <div>
      <button onClick={onToggle} className="w-full text-left group relative">
        <div className={`flex items-center gap-2.5 border rounded-sm px-3 py-2.5 transition-all duration-100 ${
          expanded ? sc.bg : `border-border bg-card hover:bg-secondary`
        } ${isBranch ? "border-dashed" : ""}`}>
          <span className="text-[10px] font-mono text-muted-foreground w-5 flex-shrink-0 text-center">
            {String(step.index).padStart(2, "0")}
          </span>
          <div className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${sc.dot}`} />
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-[11px] font-mono text-foreground font-medium">{step.label}</span>
              {step.sublabel && <span className="text-[10px] font-mono text-muted-foreground hidden sm:inline">{step.sublabel}</span>}
              <span className={`text-[9px] font-mono tracking-wider ${sc.text}`}>{sc.label}</span>
            </div>
            {step.duration && (
              <div className="text-[9px] font-mono text-muted-foreground mt-0.5">{step.duration} · {step.inputs.length}→{step.outputs.length}</div>
            )}
          </div>
          {/* Edit button */}
          <button
            onClick={e => { e.stopPropagation(); onEdit(); }}
            className="flex-shrink-0 w-6 h-6 rounded-sm border border-transparent hover:border-border hover:bg-secondary flex items-center justify-center text-muted-foreground hover:text-foreground transition-all opacity-0 group-hover:opacity-100"
            title="Edit step"
          >
            <Pencil className="w-3 h-3" />
          </button>
          {expanded ? <ChevronDown className="w-3 h-3 text-muted-foreground flex-shrink-0" /> : <ChevronRight className="w-3 h-3 text-muted-foreground flex-shrink-0" />}
        </div>
      </button>
      {expanded && <InnerSchematic step={step} />}
    </div>
  );
}

// ─── BATCH COLUMN ──────────────────────────────────────────────────────────────
function BatchColumn({
  title, subtitle, badge, steps, expandedSteps, onToggle,
  onEditStep, onAddStep, onAddBranch, onAddBranchStep, onEditBranchStep, onToggleBranchStep, expandedBranchSteps
}: {
  title: string; subtitle: string; badge: string;
  steps: WorkflowStep[];
  expandedSteps: Set<string>; onToggle: (id: string) => void;
  onEditStep: (step: WorkflowStep) => void;
  onAddStep: (afterIndex: number) => void;
  onAddBranch: (stepId: string) => void;
  onAddBranchStep: (stepId: string) => void;
  onEditBranchStep: (parentId: string, step: WorkflowStep) => void;
  onToggleBranchStep: (id: string) => void;
  expandedBranchSteps: Set<string>;
}) {
  const complete = steps.filter(s => s.status === "complete").length;
  const running = steps.filter(s => s.status === "running").length;

  return (
    <div className="flex flex-col min-w-0">
      <div className="border border-border bg-card rounded-sm px-4 py-3 mb-2">
        <div className="flex items-center justify-between gap-2">
          <div>
            <div className="text-[9px] font-mono tracking-[0.2em] text-muted-foreground">{badge}</div>
            <div className="text-sm font-mono font-semibold text-foreground mt-0.5">{title}</div>
            <div className="text-[10px] font-mono text-muted-foreground mt-0.5">{subtitle}</div>
          </div>
          <div className="text-right">
            <div className="text-[9px] font-mono text-muted-foreground">{complete}/{steps.length} done</div>
            {running > 0 && (
              <div className="flex items-center gap-1 justify-end mt-0.5">
                <div className="w-1.5 h-1.5 rounded-full bg-[#00c9a7] animate-pulse" />
                <span className="text-[9px] font-mono text-[#00c9a7]">IN PROGRESS</span>
              </div>
            )}
          </div>
        </div>
        <div className="mt-3 h-px bg-border relative">
          <div className="absolute left-0 top-0 h-full bg-[#00c9a7] transition-all" style={{ width: `${(complete / steps.length) * 100}%` }} />
        </div>
      </div>

      {/* Steps with connectors */}
      {steps.map((step, i) => (
        <div key={step.id}>
          {i > 0 && (
            <StepConnector
              onAddStep={() => onAddStep(i)}
              onAddBranch={() => onAddBranch(steps[i - 1].id)}
            />
          )}
          <StepNode
            step={step}
            expanded={expandedSteps.has(step.id)}
            onToggle={() => onToggle(step.id)}
            onEdit={() => onEditStep(step)}
          />
          {/* Branch track */}
          {step.branchTrack && (
            <div className="ml-8 mt-2 mb-1 border-l-2 border-amber-400/30 pl-3">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <CornerDownRight className="w-3 h-3 text-amber-400" />
                  <span className="text-[9px] font-mono text-amber-400 tracking-wider">{step.branchTrack.label}</span>
                </div>
                <button onClick={() => onAddBranchStep(step.id)}
                  className="flex items-center gap-1 text-[9px] font-mono text-muted-foreground hover:text-[#00c9a7] transition-colors">
                  <Plus className="w-3 h-3" />ADD STEP
                </button>
              </div>
              {step.branchTrack.steps.length === 0 && (
                <div className="text-[10px] font-mono text-muted-foreground/50 border border-dashed border-border rounded-sm p-3 text-center">
                  No steps yet — add one above
                </div>
              )}
              {step.branchTrack.steps.map((bs, bi) => (
                <div key={bs.id}>
                  {bi > 0 && <div className="ml-4 h-4 flex"><div className="w-px h-full bg-amber-400/30" /></div>}
                  <StepNode
                    step={bs}
                    expanded={expandedBranchSteps.has(bs.id)}
                    onToggle={() => onToggleBranchStep(bs.id)}
                    onEdit={() => onEditBranchStep(step.id, bs)}
                    isBranch
                  />
                </div>
              ))}
              <div className="flex items-center gap-1.5 mt-2 text-[9px] font-mono text-muted-foreground/50">
                <div className="h-px flex-1 border-t border-dashed border-border" />
                ↩ returns to main flow
                <div className="h-px flex-1 border-t border-dashed border-border" />
              </div>
            </div>
          )}
        </div>
      ))}
      {/* Add step at end */}
      <div className="ml-4 h-7 flex items-center relative group/conn cursor-pointer" onClick={() => onAddStep(steps.length)}>
        <div className="w-px h-full bg-border" />
        <div className="absolute left-2 opacity-0 group-hover/conn:opacity-100 transition-opacity">
          <div className="w-6 h-6 rounded-sm border border-[#00c9a7]/50 bg-card hover:bg-[#00c9a7]/15 flex items-center justify-center">
            <Plus className="w-3 h-3 text-[#00c9a7]" />
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── MAIN PAGE ─────────────────────────────────────────────────────────────────
export default function WorkflowPage() {
  const [b1, setB1] = useState<WorkflowStep[]>(BATCH1_INIT);
  const [b2, setB2] = useState<WorkflowStep[]>(BATCH2_INIT);
  const [expandedB1, setExpandedB1] = useState<Set<string>>(new Set(["b1-05"]));
  const [expandedB2, setExpandedB2] = useState<Set<string>>(new Set());
  const [expandedBranch, setExpandedBranch] = useState<Set<string>>(new Set());

  const [editTarget, setEditTarget] = useState<{ step: WorkflowStep; batchKey: "b1" | "b2"; branchParentId?: string } | null>(null);
  const [addTarget, setAddTarget] = useState<{ afterIndex: number; batchKey: "b1" | "b2" } | null>(null);
  const [branchTarget, setBranchTarget] = useState<{ stepId: string; batchKey: "b1" | "b2" } | null>(null);
  const [branchStepTarget, setBranchStepTarget] = useState<{ stepId: string; batchKey: "b1" | "b2" } | null>(null);

  const getBatch = (k: "b1" | "b2") => k === "b1" ? b1 : b2;
  const setBatch = (k: "b1" | "b2", v: WorkflowStep[]) => k === "b1" ? setB1(v) : setB2(v);

  const toggleB1 = (id: string) => setExpandedB1(s => { const n = new Set(s); n.has(id) ? n.delete(id) : n.add(id); return n; });
  const toggleB2 = (id: string) => setExpandedB2(s => { const n = new Set(s); n.has(id) ? n.delete(id) : n.add(id); return n; });
  const toggleBranch = (id: string) => setExpandedBranch(s => { const n = new Set(s); n.has(id) ? n.delete(id) : n.add(id); return n; });

  const handleSaveStep = (updated: WorkflowStep) => {
    if (!editTarget) return;
    const { batchKey, branchParentId } = editTarget;
    const steps = getBatch(batchKey);
    if (branchParentId) {
      setBatch(batchKey, steps.map(s => s.id === branchParentId && s.branchTrack
        ? { ...s, branchTrack: { ...s.branchTrack, steps: s.branchTrack.steps.map(bs => bs.id === updated.id ? updated : bs) } }
        : s
      ));
    } else {
      setBatch(batchKey, steps.map(s => s.id === updated.id ? updated : s));
    }
    setEditTarget(null);
  };

  const handleAddStep = (label: string, sublabel: string) => {
    if (!addTarget) return;
    const { afterIndex, batchKey } = addTarget;
    const steps = getBatch(batchKey);
    const newStep: WorkflowStep = mk(uid(), afterIndex + 1, label, sublabel || undefined, "pending", "—", [], [], []);
    const updated = [
      ...steps.slice(0, afterIndex),
      newStep,
      ...steps.slice(afterIndex).map((s, i) => ({ ...s, index: afterIndex + 2 + i })),
    ];
    setBatch(batchKey, updated);
    setAddTarget(null);
  };

  const handleAddBranch = (label: string) => {
    if (!branchTarget) return;
    const { stepId, batchKey } = branchTarget;
    const steps = getBatch(batchKey);
    setBatch(batchKey, steps.map(s => s.id === stepId ? { ...s, branchTrack: { id: uid(), label, steps: [] } } : s));
    setBranchTarget(null);
  };

  const handleAddBranchStep = (label: string, sublabel: string) => {
    if (!branchStepTarget) return;
    const { stepId, batchKey } = branchStepTarget;
    const steps = getBatch(batchKey);
    const newBranchStep: WorkflowStep = mk(uid(), 1, label, sublabel || undefined, "pending", "—", [], [], []);
    setBatch(batchKey, steps.map(s => s.id === stepId && s.branchTrack
      ? { ...s, branchTrack: { ...s.branchTrack, steps: [...s.branchTrack.steps, { ...newBranchStep, index: s.branchTrack.steps.length + 1 }] } }
      : s
    ));
    setBranchStepTarget(null);
  };

  const allB1 = b1.map(s => s.id);
  const allB2 = b2.map(s => s.id);

  return (
    <div className="min-h-full bg-background" style={{ fontFamily: "'JetBrains Mono', monospace" }}>
      {/* Top bar */}
      <div className="border-b border-border bg-card px-5 py-2.5 flex items-center gap-4 sticky top-0 z-10">
        <div className="flex items-center gap-2">
          <FlaskConical className="w-3.5 h-3.5 text-[#00c9a7]" />
          <span className="text-[10px] font-mono text-muted-foreground">WORKFLOW</span>
          <span className="text-muted-foreground/30">/</span>
          <span className="text-[10px] font-mono text-foreground">ANC2-PURIF-2026</span>
        </div>
        <div className="flex-1" />
        <div className="flex items-center gap-1.5 text-[9px] font-mono text-muted-foreground">
          <span className="text-amber-400">↗</span> = branch
          <span className="ml-2 text-[#00c9a7]">+</span> = add step
          <span className="ml-2"><Pencil className="w-2.5 h-2.5 inline" /></span> = edit
          <span className="ml-2"><Hash className="w-2.5 h-2.5 inline" /></span> = calculator
        </div>
        <button className="flex items-center gap-1.5 text-[10px] font-mono text-muted-foreground hover:text-foreground transition-colors">
          <Download className="w-3 h-3" />EXPORT
        </button>
      </div>

      <div className="max-w-6xl mx-auto px-5 py-7">
        {/* Header */}
        <div className="mb-5">
          <div className="text-[9px] font-mono tracking-[0.25em] text-muted-foreground mb-1">WORKFLOW SCHEMATIC</div>
          <h1 className="text-xl font-mono font-semibold">ANC2 Purification Strategies</h1>
          <div className="flex items-center gap-4 mt-1.5 text-[10px] font-mono text-muted-foreground flex-wrap">
            <span>His-SUMO-ANC2 · E. coli BL21(DE3)</span>
            <span>PI: Dr. A. Ferretti</span>
            <span>EXP-2026-0713</span>
          </div>
        </div>

        {/* Legend + controls */}
        <div className="flex items-center gap-5 mb-5 pb-4 border-b border-border flex-wrap">
          {Object.entries(STATUS_CFG).map(([k, v]) => (
            <div key={k} className="flex items-center gap-1.5">
              <div className={`w-1.5 h-1.5 rounded-full ${v.dot.replace(" animate-pulse","")}`} />
              <span className={`text-[9px] font-mono ${v.text}`}>{v.label}</span>
            </div>
          ))}
          <div className="flex-1" />
          <button onClick={() => { setExpandedB1(new Set(allB1)); setExpandedB2(new Set(allB2)); }}
            className="text-[9px] font-mono text-muted-foreground hover:text-foreground border border-border rounded-sm px-2 py-1 transition-colors">EXPAND ALL</button>
          <button onClick={() => { setExpandedB1(new Set()); setExpandedB2(new Set()); }}
            className="text-[9px] font-mono text-muted-foreground hover:text-foreground border border-border rounded-sm px-2 py-1 transition-colors">COLLAPSE ALL</button>
        </div>

        {/* Two-column batches */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <BatchColumn
            title="No Refolding" subtitle="Standard native-condition purification" badge="BATCH 1"
            steps={b1} expandedSteps={expandedB1} onToggle={toggleB1}
            onEditStep={s => setEditTarget({ step: s, batchKey: "b1" })}
            onAddStep={i => setAddTarget({ afterIndex: i, batchKey: "b1" })}
            onAddBranch={id => setBranchTarget({ stepId: id, batchKey: "b1" })}
            onAddBranchStep={id => setBranchStepTarget({ stepId: id, batchKey: "b1" })}
            onEditBranchStep={(pid, s) => setEditTarget({ step: s, batchKey: "b1", branchParentId: pid })}
            onToggleBranchStep={toggleBranch} expandedBranchSteps={expandedBranch}
          />
          <BatchColumn
            title="Refolding Protocol" subtitle="Denaturing lysis → acid precipitation → refolding" badge="BATCH 2"
            steps={b2} expandedSteps={expandedB2} onToggle={toggleB2}
            onEditStep={s => setEditTarget({ step: s, batchKey: "b2" })}
            onAddStep={i => setAddTarget({ afterIndex: i, batchKey: "b2" })}
            onAddBranch={id => setBranchTarget({ stepId: id, batchKey: "b2" })}
            onAddBranchStep={id => setBranchStepTarget({ stepId: id, batchKey: "b2" })}
            onEditBranchStep={(pid, s) => setEditTarget({ step: s, batchKey: "b2", branchParentId: pid })}
            onToggleBranchStep={toggleBranch} expandedBranchSteps={expandedBranch}
          />
        </div>
      </div>

      {/* Modals */}
      {editTarget && (
        <EditStepDialog
          step={editTarget.step} open
          onClose={() => setEditTarget(null)}
          onSave={handleSaveStep}
        />
      )}
      <AddStepModal
        open={!!addTarget} onClose={() => setAddTarget(null)}
        onAdd={handleAddStep}
      />
      <AddBranchModal
        open={!!branchTarget} onClose={() => setBranchTarget(null)}
        onAdd={handleAddBranch}
      />
      <AddStepModal
        open={!!branchStepTarget} onClose={() => setBranchStepTarget(null)}
        onAdd={handleAddBranchStep}
      />
    </div>
  );
}
