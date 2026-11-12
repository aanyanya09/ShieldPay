import { LayoutDashboard, Store, ShieldCheck, Flag, Settings, CircleHelp } from "lucide-react";

const items = [
  ["overview", LayoutDashboard, "Dashboard"],
  ["shop", Store, "Demo store"],
  ["security", ShieldCheck, "Security check"],
  ["reports", Flag, "Seller reports"]
];

export default function Sidebar({ page, setPage, open }) {
  return <aside className={`sidebar ${open ? "sidebar-open" : ""}`}>
    <div className="workspace-label">WORKSPACE</div>
    <nav>{items.map(([id, Icon, label]) => <button key={id} className={`nav-item ${page === id ? "active" : ""}`} onClick={() => setPage(id)}><Icon size={18}/><span>{label}</span>{id === "reports" && <span className="nav-count">3</span>}</button>)}</nav>
    <div className="sidebar-bottom">
      <div className="help-card"><div className="help-icon"><CircleHelp size={18}/></div><strong>Need a hand?</strong><p>Learn how ShieldPay protects your checkout.</p><button onClick={() => setPage("security")}>Explore security <span>→</span></button></div>
      <button className="nav-item muted-nav"><Settings size={18}/><span>Settings</span></button>
      <div className="sidebar-version">SHIELDPAY DEMO <span>v1.0.0</span></div>
    </div>
  </aside>;
}
