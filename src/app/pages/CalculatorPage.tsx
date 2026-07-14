import CalculatorWidget from "../components/CalculatorWidget";

export default function CalculatorPage() {
  return (
    <div className="min-h-full bg-background px-7 py-7" style={{ fontFamily: "'JetBrains Mono', monospace" }}>
      <div className="max-w-3xl mx-auto">
        <div className="mb-6">
          <div className="text-[9px] font-mono tracking-[0.25em] text-muted-foreground mb-1">LAB TOOLS</div>
          <h1 className="text-xl font-mono font-semibold text-foreground">Molarity Calculator</h1>
          <p className="text-[10px] font-mono text-muted-foreground mt-1.5 leading-relaxed max-w-xl">
            Calculators are independent and can be used in any order. Results of one calculator can be used as inputs for another. The same calculator is available inline when editing workflow steps (# button).
          </p>
        </div>
        <CalculatorWidget />
      </div>
    </div>
  );
}
