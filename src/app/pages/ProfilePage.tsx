import { FlaskConical, Mail, Building2, BookOpen, Award, Clock, CheckCircle2, Beaker, TrendingUp } from "lucide-react";

const ACTIVITY = [
  { date: "2026-07-13", action: "Started Dialysis step — ANC2 Batch 1", type: "running" },
  { date: "2026-07-13", action: "Completed Ni-NTA Elution — ANC2 Batch 1", type: "complete" },
  { date: "2026-07-12", action: "Cell lysis protocol reviewed and approved", type: "complete" },
  { date: "2026-07-11", action: "Initiated ANC2 Purification project", type: "complete" },
  { date: "2026-06-28", action: "BRCA1 Sanger Sequencing — project closed", type: "complete" },
  { date: "2026-06-15", action: "Submitted sequencing samples to GENEWIZ", type: "complete" },
];

const SKILLS = ["Protein Purification", "FPLC/ÄKTA", "Crystallography", "SDS-PAGE", "NMR spectroscopy", "PCR & Cloning", "Cell culture", "Western blotting", "Mass spectrometry", "Python / BioPython"];

const STATS = [
  { label: "EXPERIMENTS", value: "47", icon: FlaskConical, color: "text-[#00c9a7]" },
  { label: "PROTOCOLS", value: "12", icon: BookOpen, color: "text-violet-400" },
  { label: "SAMPLES", value: "312", icon: Beaker, color: "text-sky-400" },
  { label: "PUBLICATIONS", value: "4", icon: Award, color: "text-amber-400" },
];

export default function ProfilePage() {
  return (
    <div className="min-h-full bg-background px-7 py-7" style={{ fontFamily: "'JetBrains Mono', monospace" }}>
      <div className="text-[9px] font-mono tracking-[0.25em] text-muted-foreground mb-6">PROFILE</div>

      <div className="grid grid-cols-1 lg:grid-cols-[280px_1fr] gap-6">
        {/* Left: identity */}
        <div className="space-y-4">
          <div className="border border-border bg-card rounded-sm p-5 text-center">
            <div className="w-16 h-16 rounded-sm bg-[#00c9a7]/20 border-2 border-[#00c9a7]/40 flex items-center justify-center mx-auto mb-3">
              <span className="text-xl font-mono text-[#00c9a7] font-semibold">YC</span>
            </div>
            <div className="text-base font-mono font-semibold text-foreground">Chen, Yuna</div>
            <div className="text-[10px] font-mono text-muted-foreground mt-0.5">Researcher II · Structural Biology</div>
            <div className="mt-3 pt-3 border-t border-border space-y-1.5 text-left">
              {[
                { icon: Building2, text: "Ferretti Lab, MIT" },
                { icon: Mail, text: "ychen@mit.edu" },
                { icon: FlaskConical, text: "Protein biochemistry focus" },
              ].map(({ icon: Icon, text }) => (
                <div key={text} className="flex items-center gap-2">
                  <Icon className="w-3 h-3 text-muted-foreground flex-shrink-0" />
                  <span className="text-[10px] font-mono text-muted-foreground">{text}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Skills */}
          <div className="border border-border bg-card rounded-sm p-4">
            <div className="text-[9px] font-mono tracking-widest text-muted-foreground mb-3">EXPERTISE</div>
            <div className="flex flex-wrap gap-1.5">
              {SKILLS.map(s => (
                <span key={s} className="text-[9px] font-mono text-muted-foreground border border-border px-1.5 py-0.5 rounded-sm hover:border-[#00c9a7]/30 hover:text-foreground transition-colors cursor-default">
                  {s}
                </span>
              ))}
            </div>
          </div>
        </div>

        {/* Right: stats + activity */}
        <div className="space-y-5">
          {/* Stats */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {STATS.map(({ label, value, icon: Icon, color }) => (
              <div key={label} className="border border-border bg-card rounded-sm px-4 py-3">
                <div className="flex items-center justify-between mb-1.5">
                  <span className="text-[9px] font-mono tracking-widest text-muted-foreground">{label}</span>
                  <Icon className={`w-3.5 h-3.5 ${color}`} />
                </div>
                <div className={`text-2xl font-mono font-semibold ${color}`}>{value}</div>
              </div>
            ))}
          </div>

          {/* Activity history */}
          <div className="border border-border bg-card rounded-sm overflow-hidden">
            <div className="px-4 py-3 border-b border-border">
              <div className="text-[9px] font-mono tracking-widest text-muted-foreground">ACTIVITY LOG</div>
            </div>
            {ACTIVITY.map((a, i) => (
              <div key={i} className={`flex items-start gap-3 px-4 py-3 ${i < ACTIVITY.length - 1 ? "border-b border-border" : ""}`}>
                <div className={`w-1.5 h-1.5 rounded-full flex-shrink-0 mt-1.5 ${a.type === "running" ? "bg-[#00c9a7] animate-pulse" : "bg-emerald-400"}`} />
                <div className="flex-1 min-w-0">
                  <div className="text-[10px] font-mono text-foreground">{a.action}</div>
                  <div className="text-[9px] font-mono text-muted-foreground mt-0.5">{a.date}</div>
                </div>
              </div>
            ))}
          </div>

          {/* Contribution chart placeholder */}
          <div className="border border-border bg-card rounded-sm p-4">
            <div className="text-[9px] font-mono tracking-widest text-muted-foreground mb-3">EXPERIMENT ACTIVITY · 2026</div>
            <div className="flex items-end gap-0.5 h-12">
              {Array.from({ length: 52 }, (_, i) => {
                const h = [0,0,0,0,1,2,3,2,1,3,4,5,3,2,4,6,5,4,3,5,4,3,2,4,5,6,5,4,3,2,1,3,4,5,4,3,5,6,5,4,3,4,5,6,5,4,3,2,1,2,3,4][i] || 0;
                return (
                  <div key={i} className="flex-1 flex flex-col items-center gap-0.5">
                    {[6,5,4,3,2,1,0].map(lvl => (
                      <div key={lvl} className={`w-full flex-1 rounded-[1px] ${h > lvl ? "bg-[#00c9a7]" : "bg-border"}`} style={{ opacity: h > lvl ? 0.2 + (lvl / 6) * 0.8 : 1 }} />
                    ))}
                  </div>
                );
              })}
            </div>
            <div className="flex justify-between mt-1">
              {["JAN","FEB","MAR","APR","MAY","JUN","JUL","AUG","SEP","OCT","NOV","DEC"].map(m => (
                <div key={m} className="text-[8px] font-mono text-muted-foreground/50">{m}</div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
