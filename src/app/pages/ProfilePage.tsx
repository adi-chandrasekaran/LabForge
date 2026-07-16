import { useEffect, useState } from "react";
import { FlaskConical, Mail, Building2, BookOpen, Award, Beaker } from "lucide-react";
import { fetchProfileSummary, type ProfileSummaryRecord } from "../api";

function formatRole(role: string) {
  return role
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

export default function ProfilePage() {
  const [summary, setSummary] = useState<ProfileSummaryRecord | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        setLoading(true);
        setError(null);
        const nextSummary = await fetchProfileSummary();
        if (!cancelled) {
          setSummary(nextSummary);
        }
      } catch (loadError) {
        if (!cancelled) {
          setError(loadError instanceof Error ? loadError.message : "Failed to load profile");
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    void load();
    return () => {
      cancelled = true;
    };
  }, []);

  const user = summary?.user;
  const initials = user?.displayName
    .split(/[\s,]+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase() ?? "")
    .join("") || "YC";

  return (
    <div className="min-h-full bg-background px-7 py-7" style={{ fontFamily: "'JetBrains Mono', monospace" }}>
      <div className="text-[9px] font-mono tracking-[0.25em] text-muted-foreground mb-6">PROFILE</div>

      {error && (
        <div className="border border-red-400/25 rounded-sm bg-red-400/10 px-4 py-4 mb-5">
          <div className="text-[10px] font-mono text-red-300">Profile API error</div>
          <div className="text-[10px] font-mono text-red-200/80 mt-1 break-words">{error}</div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-[280px_1fr] gap-6">
        <div className="space-y-4">
          <div className="border border-border bg-card rounded-sm p-5 text-center">
            <div className="w-16 h-16 rounded-sm bg-[#00c9a7]/20 border-2 border-[#00c9a7]/40 flex items-center justify-center mx-auto mb-3">
              <span className="text-xl font-mono text-[#00c9a7] font-semibold">{initials}</span>
            </div>
            <div className="text-base font-mono font-semibold text-foreground">{user?.displayName ?? "Loading..."}</div>
            <div className="text-[10px] font-mono text-muted-foreground mt-0.5">
              {user ? `${formatRole(user.role)} · Structural Biology` : "Loading profile"}
            </div>
            <div className="mt-3 pt-3 border-t border-border space-y-1.5 text-left">
              {[
                { icon: Building2, text: summary ? `${summary.labName}, ${summary.institution}` : "Loading lab..." },
                { icon: Mail, text: user?.email ?? "Loading email..." },
                { icon: FlaskConical, text: summary?.focus ?? "Loading focus..." },
              ].map(({ icon: Icon, text }) => (
                <div key={text} className="flex items-center gap-2">
                  <Icon className="w-3 h-3 text-muted-foreground flex-shrink-0" />
                  <span className="text-[10px] font-mono text-muted-foreground">{text}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="border border-border bg-card rounded-sm p-4">
            <div className="text-[9px] font-mono tracking-widest text-muted-foreground mb-3">EXPERTISE</div>
            <div className="flex flex-wrap gap-1.5">
              {loading ? (
                <span className="text-[10px] font-mono text-muted-foreground">Loading expertise...</span>
              ) : (
                (summary?.expertise ?? []).map((skill) => (
                  <span key={skill} className="text-[9px] font-mono text-muted-foreground border border-border px-1.5 py-0.5 rounded-sm hover:border-[#00c9a7]/30 hover:text-foreground transition-colors cursor-default">
                    {skill}
                  </span>
                ))
              )}
            </div>
          </div>
        </div>

        <div className="space-y-5">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {[
              { label: "EXPERIMENTS", value: summary?.experimentCount ?? 0, icon: FlaskConical, color: "text-[#00c9a7]" },
              { label: "PROTOCOLS", value: summary?.protocolCount ?? 0, icon: BookOpen, color: "text-violet-400" },
              { label: "PROJECTS", value: summary?.projectCount ?? 0, icon: Beaker, color: "text-sky-400" },
              { label: "COMPLETED", value: summary?.completedExperimentCount ?? 0, icon: Award, color: "text-amber-400" },
            ].map(({ label, value, icon: Icon, color }) => (
              <div key={label} className="border border-border bg-card rounded-sm px-4 py-3">
                <div className="flex items-center justify-between mb-1.5">
                  <span className="text-[9px] font-mono tracking-widest text-muted-foreground">{label}</span>
                  <Icon className={`w-3.5 h-3.5 ${color}`} />
                </div>
                <div className={`text-2xl font-mono font-semibold ${color}`}>{loading ? "—" : value}</div>
              </div>
            ))}
          </div>

          <div className="border border-border bg-card rounded-sm overflow-hidden">
            <div className="px-4 py-3 border-b border-border">
              <div className="text-[9px] font-mono tracking-widest text-muted-foreground">ACTIVITY LOG</div>
            </div>
            {loading ? (
              <div className="px-4 py-5 text-[11px] font-mono text-muted-foreground">Loading activity...</div>
            ) : summary && summary.recentActivity.length > 0 ? (
              summary.recentActivity.map((activity, index) => (
                <div key={`${activity.occurredAt}-${index}`} className={`flex items-start gap-3 px-4 py-3 ${index < summary.recentActivity.length - 1 ? "border-b border-border" : ""}`}>
                  <div className={`w-1.5 h-1.5 rounded-full flex-shrink-0 mt-1.5 ${activity.type === "running" ? "bg-[#00c9a7] animate-pulse" : activity.type === "error" ? "bg-red-400" : "bg-emerald-400"}`} />
                  <div className="flex-1 min-w-0">
                    <div className="text-[10px] font-mono text-foreground">{activity.message}</div>
                    <div className="text-[9px] font-mono text-muted-foreground mt-0.5">{activity.occurredAt.slice(0, 10)}</div>
                  </div>
                </div>
              ))
            ) : (
              <div className="px-4 py-5 text-[11px] font-mono text-muted-foreground">No profile activity yet.</div>
            )}
          </div>

          <div className="border border-border bg-card rounded-sm p-4">
            <div className="text-[9px] font-mono tracking-widest text-muted-foreground mb-3">EXPERIMENT ACTIVITY · 2026</div>
            <div className="flex items-end gap-0.5 h-12">
              {(summary?.monthlyActivity ?? new Array(12).fill(0)).flatMap((value, monthIndex) =>
                Array.from({ length: 4 }, (_, weekIndex) => {
                  const cellValue = weekIndex === 0 ? value : Math.max(0, value - weekIndex);
                  return (
                    <div key={`${monthIndex}-${weekIndex}`} className="flex-1 flex flex-col items-center gap-0.5">
                      {[6, 5, 4, 3, 2, 1, 0].map((level) => (
                        <div
                          key={level}
                          className={`w-full flex-1 rounded-[1px] ${cellValue > level ? "bg-[#00c9a7]" : "bg-border"}`}
                          style={{ opacity: cellValue > level ? 0.2 + (level / 6) * 0.8 : 1 }}
                        />
                      ))}
                    </div>
                  );
                }),
              )}
            </div>
            <div className="flex justify-between mt-1">
              {["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"].map((month) => (
                <div key={month} className="text-[8px] font-mono text-muted-foreground/50">
                  {month}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
