import { Link, useLocation, Outlet } from "react-router";
import {
  Home, FolderOpen, GitBranch, Calculator, User,
  Users, BrainCircuit, FlaskConical, ChevronRight,
} from "lucide-react";

const NAV = [
  { path: "/", label: "HOME", icon: Home },
  { path: "/projects", label: "PROJECTS", icon: FolderOpen },
  { path: "/workflow", label: "WORKFLOW", icon: GitBranch },
  { path: "/calculator", label: "CALCULATOR", icon: Calculator },
  { path: "/profile", label: "PROFILE", icon: User },
];

const PLACEHOLDER_NAV = [
  { path: "/teams", label: "TEAMS & CHATS", icon: Users },
  { path: "/ai-model", label: "AI MODEL", icon: BrainCircuit },
];

export default function Root() {
  const { pathname } = useLocation();

  const isActive = (path: string) =>
    path === "/" ? pathname === "/" : pathname.startsWith(path);

  return (
    <div
      className="flex h-screen overflow-hidden bg-background text-foreground"
      style={{ fontFamily: "'JetBrains Mono', monospace" }}
    >
      {/* Sidebar */}
      <aside className="w-52 flex-shrink-0 border-r border-border bg-card flex flex-col">
        {/* Logo */}
        <div className="px-4 py-4 border-b border-border flex items-center gap-2">
          <FlaskConical className="w-4 h-4 text-[#00c9a7]" />
          <div>
            <div className="text-[11px] font-mono font-semibold text-foreground tracking-tight">NMR lab</div>
            <div className="text-[9px] font-mono text-muted-foreground tracking-widest">v0.9.4</div>
          </div>
        </div>

        {/* Primary nav */}
        <nav className="flex-1 py-3 px-2 space-y-0.5 overflow-y-auto">
          {NAV.map(({ path, label, icon: Icon }) => (
            <Link
              key={path}
              to={path}
              className={`flex items-center gap-2.5 px-3 py-2 rounded-sm text-[10px] font-mono tracking-wider transition-all duration-100 group ${
                isActive(path)
                  ? "bg-[#00c9a7]/10 text-[#00c9a7] border border-[#00c9a7]/25"
                  : "text-muted-foreground hover:text-foreground hover:bg-secondary border border-transparent"
              }`}
            >
              <Icon className="w-3.5 h-3.5 flex-shrink-0" />
              <span className="flex-1">{label}</span>
              {isActive(path) && <ChevronRight className="w-3 h-3 opacity-60" />}
            </Link>
          ))}

          <div className="pt-3 pb-1 px-3">
            <div className="h-px bg-border" />
          </div>

          {PLACEHOLDER_NAV.map(({ path, label, icon: Icon }) => (
            <Link
              key={path}
              to={path}
              className={`flex items-center gap-2.5 px-3 py-2 rounded-sm text-[10px] font-mono tracking-wider transition-all duration-100 ${
                isActive(path)
                  ? "bg-[#00c9a7]/10 text-[#00c9a7] border border-[#00c9a7]/25"
                  : "text-muted-foreground hover:text-foreground hover:bg-secondary border border-transparent"
              }`}
            >
              <Icon className="w-3.5 h-3.5 flex-shrink-0" />
              <span className="flex-1">{label}</span>
              <span className="text-[8px] font-mono bg-amber-400/15 text-amber-400 border border-amber-400/20 px-1 py-0.5 rounded-sm tracking-widest">
                SOON
              </span>
            </Link>
          ))}
        </nav>

        {/* Footer */}
        <div className="px-4 py-3 border-t border-border">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded-sm bg-[#00c9a7]/20 border border-[#00c9a7]/30 flex items-center justify-center">
              <span className="text-[9px] font-mono text-[#00c9a7] font-semibold">YC</span>
            </div>
            <div>
              <div className="text-[10px] font-mono text-foreground">Chen, Y.</div>
              <div className="text-[9px] font-mono text-muted-foreground">Researcher II</div>
            </div>
          </div>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-y-auto min-w-0">
        <Outlet />
      </main>
    </div>
  );
}
