import { ShieldCheck, ShoppingBag, Bell, ChevronDown, Menu } from "lucide-react";

export default function Header({ cartCount, onCart, onMenu }) {
  return <header className="topbar">
    <button className="mobile-menu icon-button" onClick={onMenu} aria-label="Open menu"><Menu size={20}/></button>
    <div className="brand">
      <div className="brand-mark"><ShieldCheck size={22} strokeWidth={2.4}/></div>
      <span>Shield<span className="brand-light">Pay</span></span>
    </div>
    <div className="topbar-right">
      <span className="secure-indicator"><span className="live-dot"/> Secure environment</span>
      <button className="icon-button notification-button" aria-label="Notifications"><Bell size={19}/><i/></button>
      <button className="profile-button"><span className="avatar">N</span><span className="profile-name">Nitin</span><ChevronDown size={15}/></button>
      <button className="cart-button" onClick={onCart}><ShoppingBag size={18}/><span>Cart</span><b>{cartCount}</b></button>
    </div>
  </header>;
}
