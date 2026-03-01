import { useState } from "react";

// ── Design Tokens ────────────────────────────────────────────────────────────
const T = {
  bg: "#F5F6F8",
  white: "#FFFFFF",
  border: "#E5E7EB",
  divider: "#F0F1F3",
  textPrimary: "#111827",
  textSecondary: "#6B7280",
  primary: "#2563EB",
  primaryHover: "#1D4ED8",
  primaryLight: "#EFF6FF",
  success: "#16A34A",
  successLight: "#F0FDF4",
  error: "#DC2626",
  errorLight: "#FEF2F2",
  warning: "#F59E0B",
  warningLight: "#FFFBEB",
  episodic: "#F59E0B",
  episodicLight: "#FFFBEB",
  semantic: "#16A34A",
  semanticLight: "#F0FDF4",
  graph: "#2563EB",
  graphLight: "#EFF6FF",
};

// ── Mock Data ────────────────────────────────────────────────────────────────
const PROJECTS = [
  { id: "tauri-app", name: "Tauri Desktop App", desc: "Rust + React desktop application", obs: 142, entities: 38, sessions: 12, updated: "2 hours ago", langs: ["Rust", "React"], health: 94, status: "active" },
  { id: "ecommerce", name: "E-Commerce Webapp", desc: "Next.js storefront with PostgreSQL", obs: 89, entities: 21, sessions: 7, updated: "1 day ago", langs: ["Next.js", "PostgreSQL"], health: 78, status: "active" },
  { id: "cli-scripts", name: "CLI Automation Scripts", desc: "Python automation toolchain", obs: 34, entities: 9, sessions: 4, updated: "3 days ago", langs: ["Python"], health: 60, status: "idle" },
  { id: "mobile-api", name: "Mobile App Backend", desc: "FastAPI + Redis microservice", obs: 211, entities: 64, sessions: 19, updated: "5 hours ago", langs: ["FastAPI", "Redis"], health: 88, status: "active" },
];

const OBS = [
  { id: "o1", time: "14:32", type: "FILE_READ", title: "Read AppState mutex implementation", summary: "Examined Rust AppState struct wrapped in Arc<Mutex<T>> for thread-safe access across Tauri commands.", entities: ["AppState", "main.rs"], tokens: 180 },
  { id: "o2", time: "14:35", type: "BUG_FIX", title: "Fixed deadlock in save_settings command", summary: "Resolved deadlock caused by double-locking AppState. Restructured lock acquisition order in save_settings() and load_settings().", entities: ["save_settings", "AppState"], tokens: 210 },
  { id: "o3", time: "14:41", type: "FILE_WRITE", title: "Refactored IPC bridge layer", summary: "Moved all tauri::command handlers into commands/ directory. Updated invoke() calls in App.jsx to match new paths.", entities: ["App.jsx", "commands/mod.rs"], tokens: 195 },
  { id: "o4", time: "15:02", type: "DECISION", title: "Switched from app.emit() to app.emit_to()", summary: "Deprecated global event broadcasting. Now targeting specific windows by label.", entities: ["app.emit_to", "main_window"], tokens: 160, deprecated: true },
];

const SEM_RESULTS = [
  { id: "s1", score: 0.94, title: "Fixed deadlock in save_settings command", type: "BUG_FIX", tokens: 210, accessed: "2h ago" },
  { id: "s2", score: 0.87, title: "Refactored IPC bridge layer", type: "FILE_WRITE", tokens: 195, accessed: "2h ago" },
  { id: "s3", score: 0.71, title: "Switched event emission pattern", type: "DECISION", tokens: 160, accessed: "1d ago" },
];

const NODES = [
  { id: "n1", name: "App.jsx", type: "component", x: 18, y: 38 },
  { id: "n2", name: "save_settings()", type: "function", x: 38, y: 20 },
  { id: "n3", name: "AppState", type: "state", x: 58, y: 42 },
  { id: "n4", name: "main.rs", type: "file", x: 76, y: 22 },
  { id: "n5", name: "load_settings()", type: "function", x: 76, y: 62 },
  { id: "n6", name: "commands/mod.rs", type: "file", x: 55, y: 72 },
];
const EDGES = [
  { f: "n1", t: "n2", l: "CALLS" }, { f: "n2", t: "n3", l: "LOCKS" },
  { f: "n3", t: "n4", l: "DEFINED_IN" }, { f: "n4", t: "n5", l: "CONTAINS" },
  { f: "n5", t: "n3", l: "READS" }, { f: "n1", t: "n6", l: "IMPORTS" },
];
const nodeColors = { component: "#2563EB", function: "#16A34A", state: "#F59E0B", file: "#6B7280" };
const typeColors = { FILE_READ: "#6B7280", BUG_FIX: "#DC2626", FILE_WRITE: "#16A34A", DECISION: "#F59E0B" };

// ── Shared Components ────────────────────────────────────────────────────────
const Badge = ({ label, color = T.textSecondary, bg = "#F3F4F6" }) => (
  <span style={{ background: bg, color, padding: "3px 10px", borderRadius: 999, fontSize: 11, fontWeight: 500, whiteSpace: "nowrap" }}>{label}</span>
);

const Btn = ({ children, variant = "primary", onClick, style = {} }) => (
  <button onClick={onClick} style={{
    padding: "8px 16px", borderRadius: 8, fontSize: 13, fontWeight: 500, cursor: "pointer", border: "none", transition: "all 0.15s ease",
    ...(variant === "primary" ? { background: T.primary, color: "#fff" } : { background: T.white, color: T.textPrimary, border: `1px solid ${T.border}` }),
    ...style
  }}
    onMouseEnter={e => e.currentTarget.style.background = variant === "primary" ? T.primaryHover : "#F9FAFB"}
    onMouseLeave={e => e.currentTarget.style.background = variant === "primary" ? T.primary : T.white}>
    {children}
  </button>
);

const Card = ({ children, style = {}, onClick, hover = false }) => {
  const [h, setH] = useState(false);
  return (
    <div onClick={onClick}
      onMouseEnter={() => hover && setH(true)}
      onMouseLeave={() => hover && setH(false)}
      style={{
        background: T.white, borderRadius: 12, border: `1px solid ${T.border}`, padding: 24,
        boxShadow: h ? "0 4px 12px rgba(0,0,0,0.08)" : "0 1px 2px rgba(0,0,0,0.05)",
        transform: h ? "translateY(-1px)" : "none",
        transition: "all 0.2s ease",
        cursor: onClick ? "pointer" : "default",
        ...style
      }}>
      {children}
    </div>
  );
};

const Input = ({ placeholder, value, onChange, icon, style = {} }) => (
  <div style={{ display: "flex", alignItems: "center", gap: 8, background: T.white, border: `1px solid ${T.border}`, borderRadius: 8, padding: "8px 12px", ...style }}>
    {icon && <span style={{ color: T.textSecondary, fontSize: 15 }}>{icon}</span>}
    <input value={value} onChange={onChange} placeholder={placeholder}
      style={{ border: "none", outline: "none", background: "none", fontSize: 13, color: T.textPrimary, flex: 1 }} />
  </div>
);

const Stat = ({ label, value, icon }) => (
  <div style={{ textAlign: "center" }}>
    <div style={{ fontSize: 10, color: T.textSecondary, textTransform: "uppercase", letterSpacing: 1, marginBottom: 4 }}>{icon} {label}</div>
    <div style={{ fontSize: 22, fontWeight: 600, color: T.textPrimary }}>{value}</div>
  </div>
);

const HealthBar = ({ value }) => {
  const c = value >= 85 ? T.success : value >= 60 ? T.warning : T.error;
  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
        <span style={{ fontSize: 11, color: T.textSecondary }}>Memory Health</span>
        <span style={{ fontSize: 11, fontWeight: 600, color: c }}>{value}%</span>
      </div>
      <div style={{ height: 4, background: T.bg, borderRadius: 2 }}>
        <div style={{ width: `${value}%`, height: "100%", background: c, borderRadius: 2, transition: "width 0.4s ease" }} />
      </div>
    </div>
  );
};

// ── Sidebar ──────────────────────────────────────────────────────────────────
function Sidebar({ active, setScreen }) {
  const items = [
    { id: "home", icon: "⊞", label: "Projects" },
    { id: "keys", icon: "⚿", label: "API Keys" },
    { id: "settings", icon: "⚙", label: "Settings" },
  ];
  return (
    <div style={{ width: 240, background: T.white, borderRight: `1px solid ${T.border}`, display: "flex", flexDirection: "column", flexShrink: 0 }}>
      {/* Logo */}
      <div style={{ padding: "20px 20px 16px", borderBottom: `1px solid ${T.divider}` }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <div style={{ width: 32, height: 32, borderRadius: 8, background: T.primary, display: "flex", alignItems: "center", justifyContent: "center", color: "#fff", fontSize: 14, fontWeight: 700 }}>M</div>
          <div>
            <div style={{ fontSize: 14, fontWeight: 600, color: T.textPrimary }}>Memory Layer</div>
            <div style={{ fontSize: 11, color: T.textSecondary }}>Persistent AI Memory</div>
          </div>
        </div>
      </div>

      {/* Nav */}
      <nav style={{ padding: "12px 12px", flex: 1 }}>
        <div style={{ fontSize: 10, color: T.textSecondary, letterSpacing: 1.5, textTransform: "uppercase", padding: "4px 8px", marginBottom: 4 }}>Navigation</div>
        {items.map(item => {
          const isActive = active === item.id || (active.startsWith("project") && item.id === "home");
          return (
            <div key={item.id} onClick={() => setScreen(item.id)}
              style={{ display: "flex", alignItems: "center", gap: 10, padding: "9px 12px", borderRadius: 8, marginBottom: 2, cursor: "pointer", transition: "all 0.15s ease",
                background: isActive ? T.primaryLight : "transparent", color: isActive ? T.primary : T.textSecondary, fontWeight: isActive ? 500 : 400, fontSize: 13 }}
              onMouseEnter={e => !isActive && (e.currentTarget.style.background = T.bg)}
              onMouseLeave={e => !isActive && (e.currentTarget.style.background = "transparent")}>
              <span style={{ fontSize: 16 }}>{item.icon}</span>
              {item.label}
            </div>
          );
        })}
      </nav>

      {/* User */}
      <div style={{ padding: "12px 16px", borderTop: `1px solid ${T.divider}`, display: "flex", alignItems: "center", gap: 10 }}>
        <div style={{ width: 32, height: 32, borderRadius: "50%", background: T.primary, display: "flex", alignItems: "center", justifyContent: "center", color: "#fff", fontSize: 13, fontWeight: 700 }}>U</div>
        <div>
          <div style={{ fontSize: 13, fontWeight: 500, color: T.textPrimary }}>User</div>
          <div style={{ fontSize: 11, color: T.textSecondary }}>Free Plan</div>
        </div>
      </div>
    </div>
  );
}

// ── Page Header ──────────────────────────────────────────────────────────────
function PageHeader({ title, subtitle, actions, breadcrumb }) {
  return (
    <div style={{ padding: "24px 32px 0", borderBottom: `1px solid ${T.border}`, background: T.white }}>
      {breadcrumb && (
        <div style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 12, color: T.textSecondary, marginBottom: 12 }}>
          {breadcrumb.map((b, i) => (
            <span key={i} style={{ display: "flex", alignItems: "center", gap: 6 }}>
              {i > 0 && <span style={{ color: T.border }}>›</span>}
              <span onClick={b.onClick} style={{ cursor: b.onClick ? "pointer" : "default", color: b.onClick ? T.primary : T.textPrimary, fontWeight: b.onClick ? 400 : 500 }}
                onMouseEnter={e => b.onClick && (e.currentTarget.style.textDecoration = "underline")}
                onMouseLeave={e => b.onClick && (e.currentTarget.style.textDecoration = "none")}>{b.label}</span>
            </span>
          ))}
        </div>
      )}
      <div style={{ display: "flex", alignItems: "flex-end", justifyContent: "space-between", paddingBottom: 20 }}>
        <div>
          <h1 style={{ fontSize: 20, fontWeight: 600, color: T.textPrimary, margin: 0 }}>{title}</h1>
          {subtitle && <p style={{ fontSize: 13, color: T.textSecondary, margin: "4px 0 0" }}>{subtitle}</p>}
        </div>
        {actions && <div style={{ display: "flex", gap: 8 }}>{actions}</div>}
      </div>
    </div>
  );
}

// ── HOME SCREEN ───────────────────────────────────────────────────────────────
function HomeScreen({ setScreen, setProject }) {
  const [q, setQ] = useState("");
  const filtered = PROJECTS.filter(p => p.name.toLowerCase().includes(q.toLowerCase()));

  return (
    <div style={{ flex: 1, display: "flex", flexDirection: "column", overflow: "hidden" }}>
      <PageHeader title="Projects" subtitle="All your isolated AI memory workspaces — click any project to explore its memory."
        actions={[<Btn key="new">+ New Project</Btn>]} />

      <div style={{ flex: 1, overflow: "auto", padding: 32 }}>
        {/* Global stats */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: 16, marginBottom: 28 }}>
          {[
            { label: "Total Projects", value: "4", icon: "⊞" },
            { label: "Total Observations", value: "476", icon: "◎" },
            { label: "Graph Entities", value: "132", icon: "◈" },
            { label: "Tokens Saved", value: "~94k", icon: "◆" },
          ].map(s => (
            <Card key={s.label} style={{ padding: 20 }}>
              <div style={{ fontSize: 22, marginBottom: 8 }}>{s.icon}</div>
              <div style={{ fontSize: 24, fontWeight: 600, color: T.textPrimary }}>{s.value}</div>
              <div style={{ fontSize: 12, color: T.textSecondary, marginTop: 2 }}>{s.label}</div>
            </Card>
          ))}
        </div>

        {/* Search bar */}
        <div style={{ display: "flex", gap: 12, marginBottom: 20 }}>
          <Input placeholder="Search projects by name…" value={q} onChange={e => setQ(e.target.value)} icon="⌕" style={{ flex: 1 }} />
          <select style={{ background: T.white, border: `1px solid ${T.border}`, borderRadius: 8, padding: "8px 12px", fontSize: 13, color: T.textPrimary, outline: "none" }}>
            <option>All status</option><option>Active</option><option>Idle</option>
          </select>
        </div>

        {/* Section label */}
        <div style={{ fontSize: 12, color: T.textSecondary, fontWeight: 500, marginBottom: 14, textTransform: "uppercase", letterSpacing: 1 }}>
          {filtered.length} project{filtered.length !== 1 ? "s" : ""}
        </div>

        {/* Project grid */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(2,1fr)", gap: 16 }}>
          {filtered.map(p => (
            <Card key={p.id} hover onClick={() => { setProject(p); setScreen("project"); }} style={{ padding: 0, overflow: "hidden" }}>
              {/* Top colored bar per status */}
              <div style={{ height: 3, background: p.status === "active" ? T.primary : T.border, borderRadius: "12px 12px 0 0" }} />
              <div style={{ padding: 20 }}>
                {/* Header */}
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 12 }}>
                  <div>
                    <div style={{ fontSize: 15, fontWeight: 600, color: T.textPrimary, marginBottom: 3 }}>{p.name}</div>
                    <div style={{ fontSize: 12, color: T.textSecondary }}>{p.desc}</div>
                  </div>
                  <Badge label={p.status} color={p.status === "active" ? T.success : T.textSecondary} bg={p.status === "active" ? T.successLight : "#F3F4F6"} />
                </div>

                {/* Lang tags */}
                <div style={{ display: "flex", gap: 6, marginBottom: 16, flexWrap: "wrap" }}>
                  {p.langs.map(l => <Badge key={l} label={l} color={T.textSecondary} bg="#F3F4F6" />)}
                </div>

                {/* Memory layer pills */}
                <div style={{ display: "grid", gridTemplateColumns: "repeat(3,1fr)", gap: 8, marginBottom: 16 }}>
                  {[
                    { label: "Episodic", val: p.obs, unit: "obs", color: T.episodic, bg: T.episodicLight },
                    { label: "Semantic", val: p.obs, unit: "embed", color: T.semantic, bg: T.semanticLight },
                    { label: "Graph", val: p.entities, unit: "nodes", color: T.graph, bg: T.graphLight },
                  ].map(m => (
                    <div key={m.label} style={{ background: m.bg, borderRadius: 8, padding: "10px 12px" }}>
                      <div style={{ fontSize: 10, color: m.color, fontWeight: 600, textTransform: "uppercase", letterSpacing: 0.8, marginBottom: 3 }}>{m.label}</div>
                      <div style={{ fontSize: 18, fontWeight: 700, color: T.textPrimary }}>{m.val}</div>
                      <div style={{ fontSize: 10, color: T.textSecondary }}>{m.unit}</div>
                    </div>
                  ))}
                </div>

                {/* Health + Updated */}
                <HealthBar value={p.health} />
                <div style={{ fontSize: 11, color: T.textSecondary, marginTop: 10 }}>Updated {p.updated}</div>
              </div>
            </Card>
          ))}
        </div>
      </div>
    </div>
  );
}

// ── PROJECT OVERVIEW ──────────────────────────────────────────────────────────
function ProjectScreen({ project, setScreen }) {
  const layers = [
    { key: "episodic", label: "Episodic Log", icon: "◎", color: T.episodic, bg: T.episodicLight, tech: "SQLite + FTS5", desc: "An append-only timestamped diary of every action the AI agent took — file reads, bug fixes, decisions, refactors.", stat1: `${project.obs} observations`, stat2: `${project.sessions} sessions recorded` },
    { key: "semantic", label: "Semantic Layer", icon: "◈", color: T.semantic, bg: T.semanticLight, tech: "ChromaDB + Embeddings", desc: "Find any past memory by meaning — not exact keywords. Every observation is compressed to ~200 tokens and embedded.", stat1: `${project.obs} embeddings`, stat2: "~90% token savings" },
    { key: "graph", label: "Knowledge Graph", icon: "◆", color: T.graph, bg: T.graphLight, tech: "NetworkX", desc: "Maps how every code entity relates to others — which functions call which, what locks what, what was deprecated.", stat1: `${project.entities} nodes`, stat2: `${Math.floor(project.entities * 1.6)} edges` },
  ];

  return (
    <div style={{ flex: 1, display: "flex", flexDirection: "column", overflow: "hidden" }}>
      <PageHeader title={project.name} subtitle={project.desc}
        breadcrumb={[{ label: "Projects", onClick: () => setScreen("home") }, { label: project.name }]}
        actions={[<Btn key="s" variant="secondary">Settings</Btn>, <Btn key="r">Run Session</Btn>]} />

      <div style={{ flex: 1, overflow: "auto", padding: 32 }}>
        {/* Project stats */}
        <Card style={{ marginBottom: 24 }}>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: 0, divideX: "1px solid #E5" }}>
            {[
              { label: "Sessions", value: project.sessions, icon: "▶" },
              { label: "Observations", value: project.obs, icon: "◎" },
              { label: "Graph Entities", value: project.entities, icon: "◆" },
              { label: "Memory Health", value: `${project.health}%`, icon: "♡" },
            ].map((s, i) => (
              <div key={s.label} style={{ textAlign: "center", padding: "16px 0", borderLeft: i > 0 ? `1px solid ${T.border}` : "none" }}>
                <div style={{ fontSize: 10, color: T.textSecondary, textTransform: "uppercase", letterSpacing: 1, marginBottom: 6 }}>{s.label}</div>
                <div style={{ fontSize: 26, fontWeight: 600, color: T.textPrimary }}>{s.value}</div>
              </div>
            ))}
          </div>
        </Card>

        {/* MCP snippet */}
        <Card style={{ marginBottom: 24, background: T.bg }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
            <div>
              <div style={{ fontSize: 13, fontWeight: 600, color: T.textPrimary, marginBottom: 4 }}>Connect to this project</div>
              <div style={{ fontSize: 12, color: T.textSecondary }}>Add this to your IDE's MCP config to activate memory for this project.</div>
            </div>
            <Btn variant="secondary" style={{ fontSize: 12, padding: "6px 12px" }}>Copy config</Btn>
          </div>
          <div style={{ marginTop: 12, background: T.textPrimary, borderRadius: 8, padding: "12px 16px", fontFamily: "monospace", fontSize: 12, color: "#e2e8f0", lineHeight: 1.6 }}>
            {`"mcpServers": {\n  "memory-layer": {\n    "serverUrl": "https://api.memorylayer.ai/mcp",\n    "headers": { "X-Api-Key": "skp_••••••••" }\n  }\n}`}
          </div>
        </Card>

        {/* Memory layers */}
        <div style={{ fontSize: 12, fontWeight: 500, color: T.textSecondary, textTransform: "uppercase", letterSpacing: 1, marginBottom: 14 }}>Memory Layers</div>
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          {layers.map(l => (
            <Card key={l.key} hover onClick={() => setScreen(l.key)} style={{ padding: 0, overflow: "hidden" }}>
              <div style={{ display: "flex" }}>
                {/* Color strip */}
                <div style={{ width: 4, background: l.color, borderRadius: "12px 0 0 12px", flexShrink: 0 }} />
                <div style={{ padding: "18px 20px", display: "flex", gap: 16, alignItems: "center", flex: 1 }}>
                  {/* Icon */}
                  <div style={{ width: 44, height: 44, borderRadius: 10, background: l.bg, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 20, flexShrink: 0, color: l.color }}>
                    {l.icon}
                  </div>
                  {/* Info */}
                  <div style={{ flex: 1 }}>
                    <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 5 }}>
                      <span style={{ fontSize: 15, fontWeight: 600, color: T.textPrimary }}>{l.label}</span>
                      <Badge label={l.tech} color={l.color} bg={l.bg} />
                    </div>
                    <div style={{ fontSize: 13, color: T.textSecondary, lineHeight: 1.55 }}>{l.desc}</div>
                    <div style={{ display: "flex", gap: 16, marginTop: 8 }}>
                      <span style={{ fontSize: 12, color: l.color, fontWeight: 500 }}>{l.stat1}</span>
                      <span style={{ fontSize: 12, color: T.textSecondary }}>·</span>
                      <span style={{ fontSize: 12, color: T.textSecondary }}>{l.stat2}</span>
                    </div>
                  </div>
                  <div style={{ color: T.textSecondary, fontSize: 18 }}>›</div>
                </div>
              </div>
            </Card>
          ))}
        </div>
      </div>
    </div>
  );
}

// ── EPISODIC LOG ──────────────────────────────────────────────────────────────
function EpisodicScreen({ project, setScreen }) {
  const [expanded, setExpanded] = useState({ o2: true });
  const [q, setQ] = useState("");

  return (
    <div style={{ flex: 1, display: "flex", flexDirection: "column", overflow: "hidden" }}>
      <PageHeader title="Episodic Log" subtitle="Append-only session timeline. Every action the AI agent took, compressed and searchable."
        breadcrumb={[{ label: "Projects", onClick: () => setScreen("home") }, { label: project.name, onClick: () => setScreen("project") }, { label: "Episodic Log" }]} />

      <div style={{ flex: 1, overflow: "auto", padding: 32 }}>
        {/* Controls */}
        <div style={{ display: "flex", gap: 10, marginBottom: 24 }}>
          <Input placeholder="Search log entries…" value={q} onChange={e => setQ(e.target.value)} icon="⌕" style={{ flex: 1 }} />
          <select style={{ background: T.white, border: `1px solid ${T.border}`, borderRadius: 8, padding: "8px 12px", fontSize: 13, color: T.textPrimary, outline: "none" }}>
            <option>All types</option><option>BUG_FIX</option><option>FILE_READ</option><option>FILE_WRITE</option><option>DECISION</option>
          </select>
          <select style={{ background: T.white, border: `1px solid ${T.border}`, borderRadius: 8, padding: "8px 12px", fontSize: 13, color: T.textPrimary, outline: "none" }}>
            <option>All sessions</option><option>Session 204</option><option>Session 203</option>
          </select>
        </div>

        {/* Session group */}
        <div style={{ marginBottom: 8 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 16 }}>
            <div style={{ background: T.episodicLight, border: `1px solid ${T.episodic}33`, borderRadius: 8, padding: "6px 14px" }}>
              <span style={{ fontSize: 12, fontWeight: 600, color: T.episodic }}>Session 204</span>
              <span style={{ fontSize: 12, color: T.textSecondary, marginLeft: 10 }}>Today, 2:32–3:15 PM · {OBS.length} observations</span>
            </div>
            <div style={{ flex: 1, height: 1, background: T.border }} />
          </div>

          {/* Timeline */}
          <div style={{ position: "relative", paddingLeft: 80 }}>
            <div style={{ position: "absolute", left: 56, top: 12, bottom: 12, width: 2, background: T.border }} />

            {OBS.map(obs => (
              <div key={obs.id} style={{ marginBottom: 10, position: "relative" }}>
                {/* Time */}
                <div style={{ position: "absolute", left: -80, top: 14, width: 48, textAlign: "right", fontSize: 11, color: T.textSecondary }}>{obs.time}</div>
                {/* Dot */}
                <div style={{ position: "absolute", left: -28, top: 14, width: 12, height: 12, borderRadius: "50%", background: obs.deprecated ? T.border : typeColors[obs.type], border: `2px solid ${T.white}`, zIndex: 1 }} />

                <Card style={{ padding: 0, opacity: obs.deprecated ? 0.6 : 1 }}>
                  <div onClick={() => setExpanded(p => ({ ...p, [obs.id]: !p[obs.id] }))}
                    style={{ padding: "14px 16px", cursor: "pointer", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                      <Badge label={obs.type} color={typeColors[obs.type]} bg={typeColors[obs.type] + "15"} />
                      {obs.deprecated && <Badge label="DEPRECATED" color={T.textSecondary} bg="#F3F4F6" />}
                      <span style={{ fontSize: 13, fontWeight: 500, color: T.textPrimary }}>{obs.title}</span>
                    </div>
                    <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                      <span style={{ fontSize: 11, color: T.textSecondary }}>{obs.tokens} tok</span>
                      <span style={{ color: T.textSecondary, transition: "transform 0.2s", transform: expanded[obs.id] ? "rotate(90deg)" : "none" }}>›</span>
                    </div>
                  </div>

                  {expanded[obs.id] && (
                    <div style={{ padding: "0 16px 16px", borderTop: `1px solid ${T.border}` }}>
                      <p style={{ fontSize: 13, color: T.textSecondary, lineHeight: 1.65, margin: "12px 0 10px" }}>{obs.summary}</p>
                      <div style={{ display: "flex", gap: 6, marginBottom: 14 }}>
                        {obs.entities.map(e => <Badge key={e} label={e} color={T.primary} bg={T.primaryLight} />)}
                      </div>
                      <div style={{ display: "flex", gap: 8 }}>
                        <Btn variant="secondary" style={{ fontSize: 12, padding: "5px 12px" }}>Edit summary</Btn>
                        <Btn variant="secondary" style={{ fontSize: 12, padding: "5px 12px", color: T.error, borderColor: T.error + "44" }}>Invalidate</Btn>
                        <Btn variant="secondary" style={{ fontSize: 12, padding: "5px 12px", color: T.primary }}>Show in graph</Btn>
                      </div>
                    </div>
                  )}
                </Card>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

// ── SEMANTIC LAYER ────────────────────────────────────────────────────────────
function SemanticScreen({ project, setScreen }) {
  const [q, setQ] = useState("mutex deadlock fix");
  const [searched, setSearched] = useState(true);

  return (
    <div style={{ flex: 1, display: "flex", flexDirection: "column", overflow: "hidden" }}>
      <PageHeader title="Semantic Layer" subtitle="Search your project's memory by meaning — not just keywords."
        breadcrumb={[{ label: "Projects", onClick: () => setScreen("home") }, { label: project.name, onClick: () => setScreen("project") }, { label: "Semantic Layer" }]} />

      <div style={{ flex: 1, overflow: "auto", padding: 32 }}>
        {/* Explainer */}
        <Card style={{ background: T.semanticLight, border: `1px solid ${T.semantic}33`, marginBottom: 24, padding: 16 }}>
          <div style={{ display: "flex", gap: 12, alignItems: "flex-start" }}>
            <span style={{ fontSize: 20 }}>💡</span>
            <div>
              <div style={{ fontSize: 13, fontWeight: 600, color: T.textPrimary, marginBottom: 3 }}>How semantic search works</div>
              <p style={{ fontSize: 12, color: T.textSecondary, margin: 0, lineHeight: 1.6 }}>Every observation is compressed to ~200 tokens then converted into a vector embedding — a mathematical fingerprint of its meaning. When you search, your query is embedded the same way, and we surface the closest matches even if the exact words don't appear.</p>
            </div>
          </div>
        </Card>

        {/* Search */}
        <div style={{ display: "flex", gap: 10, marginBottom: 24 }}>
          <Input placeholder='Try: "how did we fix the state bug?" or "auth refactor decisions"' value={q} onChange={e => setQ(e.target.value)} icon="◈" style={{ flex: 1, borderColor: T.semantic + "88" }} />
          <Btn onClick={() => setSearched(true)} style={{ background: T.semantic }}>Search Memory</Btn>
        </div>

        {searched && (
          <>
            <div style={{ fontSize: 13, color: T.textSecondary, marginBottom: 16 }}>
              {SEM_RESULTS.length} results for <strong style={{ color: T.textPrimary }}>"{q}"</strong> — sorted by semantic similarity
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
              {SEM_RESULTS.map((r, i) => (
                <Card key={r.id} style={{ padding: 0 }}>
                  <div style={{ display: "flex" }}>
                    {/* Match indicator */}
                    <div style={{ width: 72, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", borderRight: `1px solid ${T.border}`, padding: 16, flexShrink: 0 }}>
                      <div style={{ fontSize: 18, fontWeight: 700, color: r.score >= 0.9 ? T.semantic : r.score >= 0.75 ? T.warning : T.textSecondary }}>
                        {Math.round(r.score * 100)}%
                      </div>
                      <div style={{ fontSize: 9, color: T.textSecondary, letterSpacing: 1, textTransform: "uppercase" }}>match</div>
                      <div style={{ width: 32, height: 3, background: T.border, borderRadius: 2, marginTop: 6 }}>
                        <div style={{ width: `${r.score * 100}%`, height: "100%", background: T.semantic, borderRadius: 2 }} />
                      </div>
                    </div>
                    {/* Content */}
                    <div style={{ flex: 1, padding: 16 }}>
                      <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 6 }}>
                        <Badge label={`#${i + 1}`} color={T.textSecondary} bg="#F3F4F6" />
                        <Badge label={r.type} color={typeColors[r.type]} bg={typeColors[r.type] + "15"} />
                        <span style={{ fontSize: 13, fontWeight: 500, color: T.textPrimary }}>{r.title}</span>
                      </div>
                      <div style={{ fontSize: 12, color: T.textSecondary }}>Last accessed {r.accessed} · {r.tokens} tokens · Tier 3 retrieval</div>
                    </div>
                    {/* Actions */}
                    <div style={{ display: "flex", flexDirection: "column", gap: 6, padding: 16, justifyContent: "center", borderLeft: `1px solid ${T.border}` }}>
                      <Btn variant="secondary" style={{ fontSize: 11, padding: "5px 12px", whiteSpace: "nowrap" }}>View full</Btn>
                      <Btn variant="secondary" style={{ fontSize: 11, padding: "5px 12px", whiteSpace: "nowrap", color: T.primary }}>Show in graph</Btn>
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          </>
        )}

        {!searched && (
          <div style={{ textAlign: "center", padding: "60px 0", color: T.textSecondary }}>
            <div style={{ fontSize: 32, marginBottom: 12 }}>◈</div>
            <div style={{ fontSize: 15, fontWeight: 500, color: T.textPrimary, marginBottom: 6 }}>Search your project's memory</div>
            <div style={{ fontSize: 13 }}>Type a question or concept above and press Search Memory</div>
          </div>
        )}
      </div>
    </div>
  );
}

// ── KNOWLEDGE GRAPH ───────────────────────────────────────────────────────────
function GraphScreen({ project, setScreen }) {
  const [selected, setSelected] = useState(null);
  const [filter, setFilter] = useState("all");
  const selNode = selected ? NODES.find(n => n.id === selected) : null;

  return (
    <div style={{ flex: 1, display: "flex", flexDirection: "column", overflow: "hidden" }}>
      <PageHeader title="Knowledge Graph" subtitle="Visual map of how your code entities relate — with full temporal history."
        breadcrumb={[{ label: "Projects", onClick: () => setScreen("home") }, { label: project.name, onClick: () => setScreen("project") }, { label: "Knowledge Graph" }]}
        actions={[
          <select key="f" value={filter} onChange={e => setFilter(e.target.value)} style={{ background: T.white, border: `1px solid ${T.border}`, borderRadius: 8, padding: "7px 12px", fontSize: 12, color: T.textPrimary, outline: "none" }}>
            <option value="all">All nodes</option><option value="component">Components</option><option value="function">Functions</option><option value="file">Files</option><option value="state">State</option>
          </select>
        ]} />

      <div style={{ flex: 1, display: "flex", overflow: "hidden" }}>
        {/* Canvas area */}
        <div style={{ flex: 1, position: "relative", overflow: "hidden", background: T.bg }}>
          {/* Legend */}
          <div style={{ position: "absolute", bottom: 20, left: 20, background: T.white, border: `1px solid ${T.border}`, borderRadius: 10, padding: "12px 16px", boxShadow: "0 1px 2px rgba(0,0,0,0.05)", zIndex: 2 }}>
            <div style={{ fontSize: 10, color: T.textSecondary, textTransform: "uppercase", letterSpacing: 1, marginBottom: 8 }}>Node Types</div>
            {Object.entries(nodeColors).map(([type, color]) => (
              <div key={type} style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 5 }}>
                <div style={{ width: 10, height: 10, borderRadius: "50%", background: color }} />
                <span style={{ fontSize: 11, color: T.textSecondary, textTransform: "capitalize" }}>{type}</span>
              </div>
            ))}
          </div>

          {/* Click hint */}
          <div style={{ position: "absolute", top: 16, right: 16, background: T.white, border: `1px solid ${T.border}`, borderRadius: 8, padding: "8px 12px", fontSize: 11, color: T.textSecondary, zIndex: 2 }}>
            Click any node to inspect →
          </div>

          {/* SVG graph */}
          <svg width="100%" height="100%">
            <defs>
              <marker id="arrow" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto">
                <path d="M0,0 L0,6 L8,3 z" fill={T.border} />
              </marker>
            </defs>
            {/* Edges */}
            {EDGES.map((e, i) => {
              const f = NODES.find(n => n.id === e.f), t = NODES.find(n => n.id === e.t);
              const mx = (f.x + t.x) / 2, my = (f.y + t.y) / 2;
              return (
                <g key={i}>
                  <line x1={`${f.x}%`} y1={`${f.y}%`} x2={`${t.x}%`} y2={`${t.y}%`}
                    stroke={T.border} strokeWidth={1.5} markerEnd="url(#arrow)" />
                  <rect x={`calc(${mx}% - 24px)`} y={`calc(${my}% - 8px)`} width={48} height={14} rx={3} fill={T.white} stroke={T.border} strokeWidth={0.5} />
                  <text x={`${mx}%`} y={`${my}%`} textAnchor="middle" fontSize="8" fill={T.textSecondary} dy={5}>{e.l}</text>
                </g>
              );
            })}
            {/* Nodes */}
            {NODES.filter(n => filter === "all" || n.type === filter).map(n => {
              const color = nodeColors[n.type];
              const isSel = selected === n.id;
              return (
                <g key={n.id} onClick={() => setSelected(isSel ? null : n.id)} style={{ cursor: "pointer" }}>
                  <circle cx={`${n.x}%`} cy={`${n.y}%`} r={isSel ? 26 : 22}
                    fill={T.white} stroke={isSel ? color : T.border} strokeWidth={isSel ? 2.5 : 1.5}
                    filter={isSel ? "drop-shadow(0 2px 8px rgba(0,0,0,0.12))" : "none"} />
                  <circle cx={`${n.x}%`} cy={`${n.y - 2.5}%`} r={6} fill={color + "33"} />
                  <text x={`${n.x}%`} y={`${n.y + 2}%`} textAnchor="middle" fontSize="9" fill={T.textPrimary} fontWeight="600" dy={8}>
                    {n.name.length > 14 ? n.name.slice(0, 13) + "…" : n.name}
                  </text>
                  <text x={`${n.x}%`} y={`${n.y + 2}%`} textAnchor="middle" fontSize="8" fill={T.textSecondary} dy={20}>
                    {n.type}
                  </text>
                </g>
              );
            })}
          </svg>
        </div>

        {/* Inspector panel */}
        <div style={{ width: selNode ? 280 : 0, overflow: "hidden", transition: "width 0.25s ease", flexShrink: 0, borderLeft: selNode ? `1px solid ${T.border}` : "none", background: T.white }}>
          {selNode && (
            <div style={{ width: 280, height: "100%", overflow: "auto" }}>
              {/* Panel header */}
              <div style={{ padding: "16px 20px", borderBottom: `1px solid ${T.border}`, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <div style={{ fontSize: 13, fontWeight: 600, color: T.textPrimary }}>Entity Inspector</div>
                <button onClick={() => setSelected(null)} style={{ background: "none", border: "none", cursor: "pointer", color: T.textSecondary, fontSize: 18, lineHeight: 1 }}>×</button>
              </div>
              <div style={{ padding: 20 }}>
                <div style={{ marginBottom: 16 }}>
                  <div style={{ fontSize: 16, fontWeight: 600, color: T.textPrimary, marginBottom: 6 }}>{selNode.name}</div>
                  <Badge label={selNode.type} color={nodeColors[selNode.type]} bg={nodeColors[selNode.type] + "15"} />
                </div>

                <div style={{ fontSize: 11, color: T.textSecondary, textTransform: "uppercase", letterSpacing: 1, marginBottom: 10 }}>Connections</div>
                {EDGES.filter(e => e.f === selNode.id || e.t === selNode.id).map((e, i) => {
                  const other = NODES.find(n => n.id === (e.f === selNode.id ? e.t : e.f));
                  const isOut = e.f === selNode.id;
                  return (
                    <div key={i} style={{ background: T.bg, borderRadius: 8, padding: "10px 12px", marginBottom: 8 }}>
                      <div style={{ fontSize: 10, color: T.textSecondary, marginBottom: 3 }}>
                        <span style={{ color: isOut ? T.primary : T.warning }}>{isOut ? "→ outgoing" : "← incoming"}</span>
                        {" · "}{e.l}
                      </div>
                      <div style={{ fontSize: 13, fontWeight: 500, color: T.textPrimary }}>{other?.name}</div>
                      <Badge label={other?.type || ""} color={nodeColors[other?.type]} bg={nodeColors[other?.type] + "15"} />
                    </div>
                  );
                })}

                <div style={{ marginTop: 16, display: "flex", flexDirection: "column", gap: 8 }}>
                  <Btn variant="secondary" style={{ fontSize: 12, width: "100%" }}>View in Episodic Log</Btn>
                  <Btn variant="secondary" style={{ fontSize: 12, width: "100%", color: T.error, borderColor: T.error + "44" }}>Invalidate entity</Btn>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// ── APP ROOT ──────────────────────────────────────────────────────────────────
export default function App() {
  const [screen, setScreen] = useState("home");
  const [project, setProject] = useState(PROJECTS[0]);

  const renderScreen = () => {
    if (screen === "home") return <HomeScreen setScreen={setScreen} setProject={setProject} />;
    if (screen === "project") return <ProjectScreen project={project} setScreen={setScreen} />;
    if (screen === "episodic") return <EpisodicScreen project={project} setScreen={setScreen} />;
    if (screen === "semantic") return <SemanticScreen project={project} setScreen={setScreen} />;
    if (screen === "graph") return <GraphScreen project={project} setScreen={setScreen} />;
    return null;
  };

  return (
    <div style={{ height: "100vh", display: "flex", fontFamily: "'Inter', system-ui, sans-serif", fontSize: 14, background: T.bg, color: T.textPrimary, overflow: "hidden" }}>
      <Sidebar active={screen} setScreen={setScreen} />
      <div style={{ flex: 1, display: "flex", flexDirection: "column", overflow: "hidden" }}>
        {renderScreen()}
      </div>
    </div>
  );
}