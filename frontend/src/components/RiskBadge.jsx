import { ShieldCheck, AlertTriangle, ShieldAlert, HelpCircle } from "lucide-react";

export default function RiskBadge({ level = "Unknown" }) {
  const config = {
    Low: [ShieldCheck, "risk-low", "Low risk"],
    Suspicious: [AlertTriangle, "risk-medium", "Suspicious"],
    High: [ShieldAlert, "risk-high", "High risk"],
    Unknown: [HelpCircle, "risk-unknown", "Unknown"]
  };
  const [Icon, cls, label] = config[level] || config.Unknown;
  return <span className={`risk-badge ${cls}`}><Icon size={15}/>{label}</span>;
}
