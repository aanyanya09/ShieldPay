export default function StatCard({ icon: Icon, label, value, note, tone = "blue" }) {
  return <div className="stat-card"><div className={`stat-icon ${tone}`}><Icon size={19}/></div><div className="stat-copy"><span>{label}</span><strong>{value}</strong><small>{note}</small></div></div>;
}
