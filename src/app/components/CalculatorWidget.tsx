import { useState } from "react";
import { ArrowRight } from "lucide-react";

// Unit multipliers → base SI units (M, g, L)
const CONC_MULT: Record<string, number> = { M: 1, mM: 1e-3, µM: 1e-6, nM: 1e-9, pM: 1e-12 };
const MASS_MULT: Record<string, number> = { g: 1, mg: 1e-3, µg: 1e-6, ng: 1e-9 };
const VOL_MULT: Record<string, number> = { L: 1, mL: 1e-3, µL: 1e-6, nL: 1e-9 };

const CONC_UNITS = Object.keys(CONC_MULT);
const MASS_UNITS = Object.keys(MASS_MULT);
const VOL_UNITS = Object.keys(VOL_MULT);

function fmt(n: number): string {
  if (!isFinite(n) || isNaN(n)) return "—";
  if (n === 0) return "0";
  const abs = Math.abs(n);
  if (abs >= 1000 || abs < 0.001) return n.toExponential(3);
  return parseFloat(n.toPrecision(4)).toString();
}

interface CalcSectionProps {
  title: string;
  number: number;
  children: React.ReactNode;
  result: string;
  resultLabel: string;
  onCalculate: () => void;
  onUseResult?: (v: string) => void;
}

function UnitSelect({ value, options, onChange }: { value: string; options: string[]; onChange: (v: string) => void }) {
  return (
    <select
      value={value}
      onChange={e => onChange(e.target.value)}
      className="bg-secondary border border-border text-[10px] font-mono text-foreground rounded-sm px-1.5 py-1 focus:outline-none focus:border-[#00c9a7]/50 cursor-pointer"
    >
      {options.map(u => <option key={u} value={u}>{u}</option>)}
    </select>
  );
}

function NumInput({ value, onChange, placeholder }: { value: string; onChange: (v: string) => void; placeholder?: string }) {
  return (
    <input
      type="number"
      value={value}
      onChange={e => onChange(e.target.value)}
      placeholder={placeholder ?? "0"}
      className="w-full bg-secondary border border-border text-[11px] font-mono text-foreground rounded-sm px-2 py-1 focus:outline-none focus:border-[#00c9a7]/50 placeholder:text-muted-foreground/40"
    />
  );
}

function CalcSection({ title, number, children, result, resultLabel, onCalculate, onUseResult }: CalcSectionProps) {
  return (
    <div className="border border-border rounded-sm p-4 bg-card">
      <div className="flex items-center gap-2 mb-3">
        <span className="text-[9px] font-mono text-muted-foreground border border-border rounded-sm px-1.5 py-0.5">{number}</span>
        <h3 className="text-[11px] font-mono text-foreground font-medium">{title}</h3>
      </div>
      <div className="space-y-2 mb-3">{children}</div>
      <div className="flex items-center gap-2">
        <button
          onClick={onCalculate}
          className="flex items-center gap-1.5 bg-[#00c9a7] hover:bg-[#00b899] text-[#080c12] text-[10px] font-mono font-semibold px-3 py-1.5 rounded-sm transition-colors"
        >
          {resultLabel} =
        </button>
        <div className="flex-1 bg-secondary border border-border rounded-sm px-2 py-1 text-[11px] font-mono text-[#00c9a7] min-h-[28px] flex items-center">
          {result || <span className="text-muted-foreground/40">—</span>}
        </div>
        {onUseResult && result && result !== "—" && (
          <button
            onClick={() => onUseResult(result)}
            className="text-[9px] font-mono text-amber-400 border border-amber-400/30 hover:bg-amber-400/10 px-2 py-1 rounded-sm transition-colors whitespace-nowrap"
          >
            Use ↗
          </button>
        )}
      </div>
    </div>
  );
}

interface CalculatorWidgetProps {
  onUseResult?: (value: string, label: string) => void;
  compact?: boolean;
}

export default function CalculatorWidget({ onUseResult, compact }: CalculatorWidgetProps) {
  // Calc 1: Mass from V & C
  const [c1conc, setC1conc] = useState(""); const [c1concU, setC1concU] = useState("mM");
  const [c1fw, setC1fw] = useState("");
  const [c1vol, setC1vol] = useState(""); const [c1volU, setC1volU] = useState("mL");
  const [c1res, setC1res] = useState("");

  // Calc 2: Volume from M & C
  const [c2mass, setC2mass] = useState(""); const [c2massU, setC2massU] = useState("mg");
  const [c2fw, setC2fw] = useState("");
  const [c2conc, setC2conc] = useState(""); const [c2concU, setC2concU] = useState("mM");
  const [c2res, setC2res] = useState("");

  // Calc 3: Molarity from M & V
  const [c3mass, setC3mass] = useState(""); const [c3massU, setC3massU] = useState("mg");
  const [c3fw, setC3fw] = useState("");
  const [c3vol, setC3vol] = useState(""); const [c3volU, setC3volU] = useState("mL");
  const [c3resU, setC3resU] = useState("mM");
  const [c3res, setC3res] = useState("");

  // Calc 4: Dilution C1V1=C2V2
  const [c4c1, setC4c1] = useState(""); const [c4c1U, setC4c1U] = useState("mM");
  const [c4c2, setC4c2] = useState(""); const [c4c2U, setC4c2U] = useState("µM");
  const [c4v2, setC4v2] = useState(""); const [c4v2U, setC4v2U] = useState("mL");
  const [c4resU, setC4resU] = useState("µL");
  const [c4res, setC4res] = useState("");

  const calc1 = () => {
    const c_M = parseFloat(c1conc) * CONC_MULT[c1concU];
    const v_L = parseFloat(c1vol) * VOL_MULT[c1volU];
    const fw = parseFloat(c1fw);
    const mass_g = c_M * v_L * fw;
    setC1res(fmt(mass_g / MASS_MULT["mg"]) + " mg");
  };

  const calc2 = () => {
    const m_g = parseFloat(c2mass) * MASS_MULT[c2massU];
    const c_M = parseFloat(c2conc) * CONC_MULT[c2concU];
    const fw = parseFloat(c2fw);
    const vol_L = m_g / (c_M * fw);
    setC2res(fmt(vol_L / VOL_MULT["mL"]) + " mL");
  };

  const calc3 = () => {
    const m_g = parseFloat(c3mass) * MASS_MULT[c3massU];
    const fw = parseFloat(c3fw);
    const v_L = parseFloat(c3vol) * VOL_MULT[c3volU];
    const mol_M = m_g / (fw * v_L);
    setC3res(fmt(mol_M / CONC_MULT[c3resU]) + " " + c3resU);
  };

  const calc4 = () => {
    const c1_M = parseFloat(c4c1) * CONC_MULT[c4c1U];
    const c2_M = parseFloat(c4c2) * CONC_MULT[c4c2U];
    const v2_L = parseFloat(c4v2) * VOL_MULT[c4v2U];
    const reqVol_L = (c2_M * v2_L) / c1_M;
    setC4res(fmt(reqVol_L / VOL_MULT[c4resU]) + " " + c4resU);
  };

  const gridClass = compact ? "grid grid-cols-1 gap-3" : "grid grid-cols-1 md:grid-cols-2 gap-4";

  return (
    <div className="space-y-4">
      {!compact && (
        <div>
          <div className="text-[9px] font-mono tracking-[0.2em] text-muted-foreground mb-1">MOLARITY CALCULATOR</div>
          <p className="text-[10px] font-mono text-muted-foreground leading-relaxed">
            Calculators are independent and can be used in any order. Results of one calculator can be used as inputs for another.
          </p>
        </div>
      )}

      <div className={gridClass}>
        {/* 1. Mass from V & C */}
        <CalcSection number={1} title="Mass from volume & concentration" result={c1res} resultLabel="Mass" onCalculate={calc1} onUseResult={onUseResult ? (v) => onUseResult(v, "Mass") : undefined}>
          <div className="flex items-center gap-2">
            <span className="text-[10px] font-mono text-muted-foreground w-32 flex-shrink-0">Concentration:</span>
            <NumInput value={c1conc} onChange={setC1conc} />
            <UnitSelect value={c1concU} options={CONC_UNITS} onChange={setC1concU} />
          </div>
          <div className="flex items-center gap-2">
            <span className="text-[10px] font-mono text-muted-foreground w-32 flex-shrink-0">Formula Weight (g/mol):</span>
            <NumInput value={c1fw} onChange={setC1fw} />
          </div>
          <div className="flex items-center gap-2">
            <span className="text-[10px] font-mono text-muted-foreground w-32 flex-shrink-0">Volume:</span>
            <NumInput value={c1vol} onChange={setC1vol} />
            <UnitSelect value={c1volU} options={VOL_UNITS} onChange={setC1volU} />
          </div>
        </CalcSection>

        {/* 2. Volume from M & C */}
        <CalcSection number={2} title="Volume from mass & concentration" result={c2res} resultLabel="Volume" onCalculate={calc2} onUseResult={onUseResult ? (v) => onUseResult(v, "Volume") : undefined}>
          <div className="flex items-center gap-2">
            <span className="text-[10px] font-mono text-muted-foreground w-32 flex-shrink-0">Mass:</span>
            <NumInput value={c2mass} onChange={setC2mass} />
            <UnitSelect value={c2massU} options={MASS_UNITS} onChange={setC2massU} />
          </div>
          <div className="flex items-center gap-2">
            <span className="text-[10px] font-mono text-muted-foreground w-32 flex-shrink-0">Formula Weight (g/mol):</span>
            <NumInput value={c2fw} onChange={setC2fw} />
          </div>
          <div className="flex items-center gap-2">
            <span className="text-[10px] font-mono text-muted-foreground w-32 flex-shrink-0">Concentration:</span>
            <NumInput value={c2conc} onChange={setC2conc} />
            <UnitSelect value={c2concU} options={CONC_UNITS} onChange={setC2concU} />
          </div>
        </CalcSection>

        {/* 3. Molarity from M & V */}
        <CalcSection number={3} title="Molarity from mass & volume" result={c3res} resultLabel="Molarity" onCalculate={calc3} onUseResult={onUseResult ? (v) => onUseResult(v, "Molarity") : undefined}>
          <div className="flex items-center gap-2">
            <span className="text-[10px] font-mono text-muted-foreground w-32 flex-shrink-0">Mass:</span>
            <NumInput value={c3mass} onChange={setC3mass} />
            <UnitSelect value={c3massU} options={MASS_UNITS} onChange={setC3massU} />
          </div>
          <div className="flex items-center gap-2">
            <span className="text-[10px] font-mono text-muted-foreground w-32 flex-shrink-0">Formula Weight (g/mol):</span>
            <NumInput value={c3fw} onChange={setC3fw} />
          </div>
          <div className="flex items-center gap-2">
            <span className="text-[10px] font-mono text-muted-foreground w-32 flex-shrink-0">Volume:</span>
            <NumInput value={c3vol} onChange={setC3vol} />
            <UnitSelect value={c3volU} options={VOL_UNITS} onChange={setC3volU} />
          </div>
          <div className="flex items-center gap-2">
            <span className="text-[10px] font-mono text-muted-foreground w-32 flex-shrink-0">Result unit:</span>
            <UnitSelect value={c3resU} options={CONC_UNITS} onChange={setC3resU} />
          </div>
        </CalcSection>

        {/* 4. Dilute a stock */}
        <CalcSection number={4} title="Dilute a stock solution" result={c4res} resultLabel="Required volume" onCalculate={calc4} onUseResult={onUseResult ? (v) => onUseResult(v, "Required Volume") : undefined}>
          <div className="flex items-center gap-2">
            <span className="text-[10px] font-mono text-muted-foreground w-32 flex-shrink-0">Stock concentration:</span>
            <NumInput value={c4c1} onChange={setC4c1} />
            <UnitSelect value={c4c1U} options={CONC_UNITS} onChange={setC4c1U} />
          </div>
          <div className="flex items-center gap-2">
            <span className="text-[10px] font-mono text-muted-foreground w-32 flex-shrink-0">Desired concentration:</span>
            <NumInput value={c4c2} onChange={setC4c2} />
            <UnitSelect value={c4c2U} options={CONC_UNITS} onChange={setC4c2U} />
          </div>
          <div className="flex items-center gap-2">
            <span className="text-[10px] font-mono text-muted-foreground w-32 flex-shrink-0">Desired volume:</span>
            <NumInput value={c4v2} onChange={setC4v2} />
            <UnitSelect value={c4v2U} options={VOL_UNITS} onChange={setC4v2U} />
          </div>
          <div className="flex items-center gap-2">
            <span className="text-[10px] font-mono text-muted-foreground w-32 flex-shrink-0">Result unit:</span>
            <UnitSelect value={c4resU} options={VOL_UNITS} onChange={setC4resU} />
          </div>
        </CalcSection>
      </div>
    </div>
  );
}
