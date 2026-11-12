import { useEffect, useMemo, useState } from "react";
import {
  Activity, AlertTriangle, ArrowLeft, ArrowRight, BadgeCheck, Check, CheckCircle2,
  ChevronDown, ChevronRight, CircleAlert, CircleHelp, Clock3, ExternalLink, FileText,
  Flag, Headphones, HeartHandshake, KeyRound, Keyboard, LayoutDashboard, LifeBuoy,
  LockKeyhole, LogOut, Menu, Package, Search, Shield, ShieldAlert, ShieldCheck,
  ShoppingBag, Store, Watch, X, LoaderCircle, Mail, Globe, RefreshCw, Ban, Sparkles,
  ClipboardCheck, Eye, EyeOff, Smartphone, CreditCard, CircleCheck, CircleX
} from "lucide-react";
import { api } from "./services/api";
import { money } from "./data/demo";

const QUESTIONS = [
  "Is someone on a call or chat with you right now telling you to make this payment?",
  "Has anyone claiming to be the police, a bank, PayPal or customs mentioned a fine, an account problem or an arrest?",
  "Were you promised a refund, prize, job, loan or investment return if you pay?"
];
const productIcon = (name = "") => {
  const s = name.toLowerCase();
  if (s.includes("headphone") || s.includes("audio")) return Headphones;
  if (s.includes("watch")) return Watch;
  if (s.includes("keyboard")) return Keyboard;
  return Package;
};
const formatDate = value => value ? new Date(value).toLocaleString() : "—";

function Brand({ compact = false }) {
  return <div className={`brand ${compact ? "brand-compact" : ""}`}>
    <span className="brand-mark"><ShieldCheck size={21} strokeWidth={2.2}/></span>
    {!compact && <span className="brand-name">Shield<span>Pay</span></span>}
  </div>;
}
function Button({ children, kind = "primary", className = "", ...props }) {
  return <button className={`btn btn-${kind} ${className}`} {...props}>{children}</button>;
}
function PageTitle({ eyebrow, title, description, action }) {
  return <div className="page-title"><div><div className="eyebrow">{eyebrow}</div><h1>{title}</h1>{description && <p>{description}</p>}</div>{action}</div>;
}
function Field({ label, hint, children }) { return <label className="field"><span className="field-label">{label}</span>{children}{hint && <small>{hint}</small>}</label>; }
function StatusPill({ level }) {
  const cls = level === "Low risk" ? "low" : level === "Suspicious" ? "medium" : level === "High risk" ? "high" : "unknown";
  return <span className={`status-pill ${cls}`}><i/>{level || "Unknown"}</span>;
}
function Shell({ page, navigate, cartCount, children, mobileOpen, setMobileOpen, onCart, backendStatus }) {
  const nav = [
    ["dashboard", LayoutDashboard, "Dashboard"], ["store", Store, "Demo store"],
    ["reports", Flag, "Seller reports"], ["privacy", LockKeyhole, "Privacy"]
  ];
  return <div className="app-shell">
    <header className="topbar"><div className="topbar-left"><button className="mobile-toggle icon-btn" onClick={() => setMobileOpen(v => !v)} aria-label="Open navigation"><Menu size={20}/></button><Brand/></div>
      <div className="topbar-right"><span className={`connection ${backendStatus === "online" ? "online" : backendStatus === "offline" ? "offline" : "checking"}`}><i/>{backendStatus === "online" ? "Backend connected" : backendStatus === "offline" ? "Backend unavailable" : "Connecting"}</span><button className="cart-top" onClick={onCart}><ShoppingBag size={17}/><span>Cart</span><b>{cartCount}</b></button></div>
    </header>
    <div className="layout"><aside className={`sidebar ${mobileOpen ? "sidebar-open" : ""}`}>
      <div className="sidebar-caption">WORKSPACE</div><nav>{nav.map(([id, Icon, label]) => <button key={id} className={`nav-link ${page === id ? "active" : ""}`} onClick={() => {navigate(id);setMobileOpen(false);}}><Icon size={18}/><span>{label}</span>{page === id && <span className="nav-active-dot"/>}</button>)}</nav>
      <div className="sidebar-bottom"><div className="sidebar-security"><span className="security-mark"><ShieldCheck size={18}/></span><strong>Protection before capture</strong><p>PayPal approval is not the same as payment capture. ShieldPay checks first.</p></div><div className="sidebar-version">SHIELDPAY <span>DEMO ENVIRONMENT</span></div></div>
    </aside>
    {mobileOpen && <button className="mobile-scrim" onClick={() => setMobileOpen(false)} aria-label="Close navigation"/>}
    <main className="main-area"><div className="content-wrap">{children}<footer className="footer"><span>© 2026 ShieldPay</span><span><LockKeyhole size={13}/> Payment capture is controlled by the backend</span></footer></div></main></div>
  </div>;
}

function Dashboard({ onShop, onReports, onPrivacy, backendStatus, aiConfigured, aiModel }) {
  return <>
    <PageTitle eyebrow="SHIELDPAY / DASHBOARD" title="Safer decisions. Before payment." description="A checkout security layer that checks risk after PayPal approval and before the backend captures funds." action={<Button onClick={onShop}><Store size={16}/> Open demo store</Button>}/>
    <section className="hero-panel"><div className="hero-copy"><div className="hero-kicker"><span/> PRE-CAPTURE PROTECTION</div><h2>Pause. Check.<br/><em>Then decide.</em></h2><p>ShieldPay looks for scam signals in seller identity, reported activity, buyer answers and pasted messages before a payment can be captured.</p><Button kind="light" onClick={onShop}>Explore the demo store <ArrowRight size={16}/></Button></div><div className="hero-visual"><div className="hero-ring ring-a"/><div className="hero-ring ring-b"/><div className="hero-shield"><ShieldCheck size={76} strokeWidth={1.3}/></div><div className="hero-chip chip-a"><LockKeyhole size={14}/> Server-side capture gate</div><div className="hero-chip chip-b"><CheckCircle2 size={14}/> Risk-aware checkout</div></div></section>
    <div className="metric-grid"><article className="metric-card"><span className="metric-icon blue"><ShieldCheck size={19}/></span><div><small>Protection workflow</small><strong>Pre-capture</strong><p>Checks before money moves</p></div></article><article className="metric-card"><span className="metric-icon green"><Activity size={19}/></span><div><small>Backend status</small><strong>{backendStatus === "online" ? "Connected" : backendStatus === "offline" ? "Unavailable" : "Checking"}</strong><p>Live API connection</p></div></article><article className="metric-card"><span className="metric-icon violet"><Sparkles size={19}/></span><div><small>Gemini message check</small><strong>{aiConfigured ? "Configured" : "Key missing"}</strong><p>{aiConfigured ? (aiModel || "Gemini Flash-Lite") : "Add GEMINI_API_KEY to backend .env"}</p></div></article><article className="metric-card"><span className="metric-icon amber"><Ban size={19}/></span><div><small>High-risk outcome</small><strong>Capture blocked</strong><p>No payment is collected</p></div></article></div>
    <div className="dashboard-grid"><section className="surface workflow-card"><div className="surface-heading"><div><span className="eyebrow">HOW IT WORKS</span><h3>One checkout. Three clear stages.</h3></div><span className="heading-icon"><ClipboardCheck size={19}/></span></div><div className="workflow-list"><div className="workflow-step"><span>01</span><div><strong>Approve with PayPal</strong><p>The browser redirects to PayPal Sandbox. It never captures the payment.</p></div><ChevronRight size={17}/></div><div className="workflow-step"><span>02</span><div><strong>Run the ShieldPay check</strong><p>Review the message, answer optional questions and inspect the risk result.</p></div><ChevronRight size={17}/></div><div className="workflow-step"><span>03</span><div><strong>Backend controls capture</strong><p>A signed, short-lived token and server-side rules gate the final capture request.</p></div><ChevronRight size={17}/></div></div></section>
      <section className="surface dashboard-side"><div className="side-icon"><Shield size={22}/></div><span className="eyebrow">BUILT AROUND ONE RULE</span><h3>Approval is not capture.</h3><p>PayPal approval authorizes the merchant to request capture. ShieldPay checks the transaction context first; only the backend can call PayPal's capture operation.</p><div className="side-links"><button onClick={onReports}>Report a seller <ArrowRight size={14}/></button><button onClick={onPrivacy}>Privacy information <ArrowRight size={14}/></button></div></section></div>
  </>;
}

function StorePage({ products, loading, error, cart, addToCart, onCheckout }) {
  const [query, setQuery] = useState("");
  const visible = products.filter(p => p.name.toLowerCase().includes(query.toLowerCase()));
  return <><PageTitle eyebrow="DEMO STORE" title="Choose an item" description="A sample merchant storefront used to demonstrate ShieldPay's pre-capture checks." action={<div className="secure-label"><ShieldCheck size={16}/> Protected checkout flow</div>}/>
    <div className="store-toolbar"><div><strong>Products</strong><span>{products.length} catalogue items</span></div><label className="search-field"><Search size={16}/><input value={query} onChange={e => setQuery(e.target.value)} placeholder="Search the catalogue"/></label></div>
    {loading && <div className="empty-state"><LoaderCircle className="spin"/><strong>Loading catalogue</strong><p>Fetching product details from the backend.</p></div>}
    {error && <div className="notice notice-error"><CircleAlert size={17}/><div><strong>Catalogue unavailable</strong><p>{error}</p></div></div>}
    {!loading && !error && <div className="catalog-grid">{visible.map(p => {const Icon = productIcon(p.name); const qty = cart[p.product_id] || 0;return <article className="product-card" key={p.product_id}><div className="product-image"><span className="product-category">{p.category || "SHIELDPAY SELECT"}</span><Icon size={64} strokeWidth={1.25}/><span className="product-image-label">DEMO CATALOGUE</span></div><div className="product-body"><div className="product-seller">Seller <span>{p.seller_email}</span></div><h3>{p.name}</h3><div className="product-price">{money(Number(p.price_cents)/100,p.currency)}</div><div className="product-bottom"><span className="stock-label"><CheckCircle2 size={14}/> Available</span><Button kind={qty ? "secondary" : "primary"} onClick={() => addToCart(p.product_id)}>{qty ? <><Check size={15}/> Added ({qty})</> : <>Add to cart <ArrowRight size={15}/></>}</Button></div></div></article>;})}</div>}
    {!loading && !error && visible.length === 0 && <div className="empty-state"><Search/><strong>No matching products</strong><p>Try another search term.</p></div>}
    <div className="store-footnote"><LockKeyhole size={15}/> Prices and product IDs come from the backend. The backend recalculates the order total from its own database.</div>
    {Object.values(cart).some(Boolean) && <div className="checkout-bar"><div><small>YOUR CART</small><strong>{Object.values(cart).reduce((a,b)=>a+b,0)} item(s) selected</strong></div><Button onClick={onCheckout}>Review checkout <ArrowRight size={16}/></Button></div>}
  </>;
}

function CheckoutPage({ products, cart, loading, onCreateOrder, onBack }) {
  const lines = products.filter(p => cart[p.product_id]).map(p => ({...p, quantity:cart[p.product_id]}));
  const subtotal = lines.reduce((sum,p) => sum + (Number(p.price_cents)*p.quantity),0);
  const currency = lines[0]?.currency || "USD";
  const totalLabel = money(subtotal/100,currency);
  const singleCurrency = lines.every(p => p.currency === currency);
  return <><PageTitle eyebrow="CHECKOUT / REVIEW" title="Review your order" description="Confirm the items before opening PayPal Sandbox." action={<button className="back-link" onClick={onBack}><ArrowLeft size={15}/> Back to store</button>}/>
    <div className="checkout-grid"><section className="surface order-surface"><div className="surface-heading"><div><h3>Order summary</h3><p>{lines.reduce((n,p)=>n+p.quantity,0)} item(s)</p></div><Package size={19}/></div>{lines.map(p => <div className="order-line" key={p.product_id}><div className="order-product-icon"><Package size={20}/></div><div className="order-product-name"><strong>{p.name}</strong><small>Quantity: {p.quantity}</small></div><strong>{money(Number(p.price_cents)*p.quantity/100,p.currency)}</strong></div>)}<div className="order-total"><span>Total</span><strong>{totalLabel}</strong></div><div className="notice notice-info"><LockKeyhole size={17}/><p>PayPal approval happens in the browser. Payment capture can only be requested by the backend after the ShieldPay check.</p></div></section>
      <section className="surface payment-surface"><div className="paypal-brand"><span>Pay</span><b>Pal</b><small>SANDBOX</small></div><h3>Continue to PayPal</h3><p>You'll approve this order in a PayPal Sandbox pop-up or redirect. ShieldPay does not collect or store your PayPal password or card details.</p><div className="paypal-points"><div><CheckCircle2 size={16}/> PayPal handles buyer approval</div><div><CheckCircle2 size={16}/> ShieldPay checks before capture</div><div><CheckCircle2 size={16}/> Backend validates the signed token</div></div><Button className="full-width" disabled={loading || !lines.length || lines.length !== 1 || !singleCurrency} onClick={() => onCreateOrder(lines)}>{loading ? <><LoaderCircle className="spin" size={17}/> Creating order…</> : <>Continue with PayPal <ArrowRight size={17}/></>}</Button>{lines.length !== 1 && <p className="field-error">This backend currently supports one product per order. Keep one product in the cart.</p>}<small className="legal-note">This is a demonstration checkout. Use PayPal Sandbox accounts during testing.</small></section></div>
  </>;
}

function SecurityPage({ order, loading, onAssess, initialMessage = "", initialAnswers = [null,null,null], reAnswer = false }) {
  const [message,setMessage] = useState(initialMessage);
  const [answers,setAnswers] = useState(initialAnswers);
  const [consent,setConsent] = useState(false);
  const allAnswered = answers.every(v => v !== null);
  const allSkipped = answers.every(v => v === null);
  const questionsValid = allAnswered || allSkipped;
  const skipped = allSkipped;
  const answer = (index,value) => setAnswers(old => old.map((v,i) => i === index ? value : v));
  return <><PageTitle eyebrow={reAnswer ? "CORRECT YOUR ANSWERS" : "SECURITY CHECK / BUYER REVIEW"} title={reAnswer ? "Review your answers" : "Before you decide, check the context."} description="The check is optional for pasted text and questions. You can skip the three questions if you prefer." action={<span className="step-label">STEP 2 OF 3</span>}/>
    <div className="security-grid"><div className="security-main">
      <section className="surface message-surface"><div className="surface-heading"><div><span className="section-index">01</span><div><h3>Paste the message (optional)</h3><p>Paste seller instructions, a chat message or payment request.</p></div></div><span className="optional-tag">OPTIONAL</span></div><textarea maxLength={2000} value={message} onChange={e => setMessage(e.target.value.slice(0,2000))} placeholder="Paste the message or payment instructions here…"/><div className="textarea-meta"><span>Do not paste passwords, OTPs or full payment-card details.</span><span>{message.length.toLocaleString()} / 2,000</span></div>
      </section>
      <section className="surface questions-surface"><div className="surface-heading"><div><span className="section-index">02</span><div><h3>Three scam-check questions</h3><p>Answer all three, or skip the question section entirely.</p></div></div><span className="optional-tag">OPTIONAL</span></div><div className="question-stack">{QUESTIONS.map((q,i)=><div className="question-item" key={i}><div className="question-number">0{i+1}</div><p>{q}</p><div className="choice-group"><button type="button" className={answers[i] === true ? "chosen yes" : ""} onClick={() => answer(i,true)}>Yes</button><button type="button" className={answers[i] === false ? "chosen no" : ""} onClick={() => answer(i,false)}>No</button></div></div>)}</div><button className="skip-link" type="button" onClick={() => setAnswers([null,null,null])}>Skip all three questions</button></section>
      <label className="consent-box"><input type="checkbox" checked={consent} onChange={e => setConsent(e.target.checked)}/><span><strong>I agree to the message check.</strong><small>ShieldPay redacts contact and payment-like numbers before sending the message to Google Gemini. Do not include passwords, one-time codes or full card details. Google’s free-tier data-use terms may allow submitted content to be used to improve its services.</small></span></label>
      <Button className="assessment-button" disabled={!consent || !questionsValid || loading} onClick={() => onAssess({message:message.trim(),answers:skipped ? null : answers,reAnswer})}>{loading ? <><LoaderCircle className="spin" size={17}/> Checking the payment context…</> : <><ShieldCheck size={18}/> {reAnswer ? "Submit corrected answers" : "Check payment risk"} <ArrowRight size={17}/></>}</Button>
      {!questionsValid && <p className="field-error">Answer all three questions or choose “Skip all three questions”.</p>}
    </div><aside className="security-aside"><div className="surface order-context"><span className="eyebrow">CURRENT ORDER</span><div className="order-context-total">{money(order?.amount_cents ? order.amount_cents/100 : order?.amount || 0,order?.currency || "USD")}</div><strong>{order?.productName || "Demo purchase"}</strong><small>Reference: {order?.id || "—"}</small><div className="context-divider"/><div className="context-state"><span><i/> PayPal approval</span><b>Received</b></div><div className="context-state"><span><i/> Payment capture</span><b className="pending-text">Not requested</b></div></div><div className="surface signal-card"><div className="signal-title"><ShieldCheck size={18}/><strong>What ShieldPay checks</strong></div>{["Urgency and threats","Fake support or authority claims","Requests for passwords or codes","Advance fees and refund traps","Requests to pay outside checkout","Seller reports and brand lookalikes"].map(t=><div className="signal-row" key={t}><CheckCircle2 size={15}/>{t}</div>)}<p>Messages are treated as untrusted data. They cannot change the rules used to assess the payment.</p></div></aside></div>
  </>;
}

function Countdown({ seconds, assessedAt, onReady }) {
  const [remaining,setRemaining] = useState(Math.max(0,seconds - Math.floor((Date.now()-assessedAt)/1000)));
  useEffect(() => { const timer = setInterval(() => setRemaining(Math.max(0,seconds - Math.floor((Date.now()-assessedAt)/1000))),250); return () => clearInterval(timer); },[seconds,assessedAt]);
  useEffect(() => { if (remaining === 0) onReady?.(); },[remaining,onReady]);
  return <div className="wait-panel"><div className="wait-icon"><Clock3 size={20}/></div><div><strong>{remaining > 0 ? `Take ${remaining} more second${remaining===1?"":"s"} to review` : "Review period complete"}</strong><p>The backend enforces this waiting period too. The timer here is only a visual guide.</p></div><strong className="wait-time">{remaining}s</strong></div>;
}

function ResultPage({ result, order, loading, onCapture, onReanswer, onShop, onScammed, onReports }) {
  const level = result?.riskLevel || "Unknown";
  const high = level === "High risk";
  const suspicious = level === "Suspicious";
  const unknown = level === "Unknown";
  const low = level === "Low risk";
  const wait = suspicious ? Number(result.waitSeconds || 0) : 0;
  const [waitDone,setWaitDone] = useState(wait === 0);
  const assessedAt = result?.assessedAt || Date.now();
  const captureAllowed = !high && Boolean(result?.token) && (!suspicious || waitDone);
  const title = high ? "Do not continue with this payment." : suspicious ? "Pause. Review the warning signs." : low ? "No major warning signs were found." : "We could not verify enough information.";
  const description = high ? "ShieldPay has blocked the capture request. No money was collected by this checkout." : suspicious ? "The assessment found signals that deserve a closer look. Review the reasons and wait before deciding." : low ? "The available checks did not identify major warning signs. This is not a guarantee that the seller or payment is safe." : "Some checks were unavailable or there was not enough information. Unknown does not mean safe.";
  return <><PageTitle eyebrow="ASSESSMENT RESULT" title="Your payment review" description="The result is based on the backend assessment response." action={<StatusPill level={level}/>}/>
    <div className="result-grid"><section className="surface result-surface"><div className={`result-banner ${high?"danger":suspicious?"warning":low?"success":"neutral"}`}><span className="result-emblem">{high?<ShieldAlert size={29}/>:suspicious?<AlertTriangle size={29}/>:low?<ShieldCheck size={29}/>:<CircleHelp size={29}/>}</span><div><StatusPill level={level}/><h2>{title}</h2><p>{description}</p></div></div>
      <div className="result-facts"><div><small>ASSESSMENT REFERENCE</small><strong>{result.assessmentId || "Not supplied"}</strong></div><div><small>ORDER REFERENCE</small><strong>{order?.id || "—"}</strong></div><div><small>CONFIDENCE</small><strong>{result.confidence || "Unknown"}</strong></div></div>
      <div className="result-section"><h3>Why you received this result</h3>{result.reasons?.length ? result.reasons.map((r,i)=><div className="reason-line" key={i}><span><AlertTriangle size={15}/></span><p>{r}</p></div>) : <div className="quiet-line"><CheckCircle2 size={16}/><p>No specific warning reason was returned by the backend.</p></div>}</div>
      {result.notChecked?.length > 0 && <div className="result-section"><h3>What could not be checked</h3>{result.notChecked.map((r,i)=><div className="reason-line muted" key={i}><span><CircleHelp size={15}/></span><p>{r}</p></div>)}</div>}
      {result.messageCheckFailed && <div className="notice notice-warning"><CircleAlert size={17}/><div><strong>Message could not be checked</strong><p>The AI service timed out, was unavailable, or returned invalid data. This result cannot be treated as safe, and no capture token was issued.</p></div></div>}
      {result.messageAnalysis && <div className="result-section"><h3>AI message signals</h3><div className="signal-row"><CheckCircle2 size={15}/>Model: {result.messageAnalysis.model || "Gemini"}</div><div className="signal-row"><CheckCircle2 size={15}/>Language: {result.messageAnalysis.language || "Unknown"}</div>{result.messageAnalysis.categories?.length ? <div className="analysis-tags">{result.messageAnalysis.categories.map(c=><span className="status-pill unknown" key={c}>{c.replaceAll("_"," ")}</span>)}</div> : <p>No supported scam category was identified in the supplied message.</p>}{result.messageAnalysis.evidence_quotes?.length > 0 && <div className="evidence-quotes"><strong>Evidence from the redacted message</strong>{result.messageAnalysis.evidence_quotes.map((q,i)=><blockquote key={i}>{q}</blockquote>)}</div>}</div>}
      {suspicious && wait > 0 && <Countdown seconds={wait} assessedAt={assessedAt} onReady={() => setWaitDone(true)}/>}
      {high && <div className="blocked-note"><Ban size={18}/><div><strong>No money was collected.</strong><p>The frontend will not request capture for a high-risk result. The backend also refuses capture.</p></div></div>}
      <div className="result-actions">{!high && result.token && <Button disabled={!captureAllowed || loading} onClick={onCapture}>{loading?<LoaderCircle className="spin" size={17}/>:<LockKeyhole size={17}/>} {loading?"Waiting for backend…":low?"Continue to payment":"I understand — continue"}</Button>}{result.canReanswer && <Button kind="secondary" onClick={onReanswer} disabled={loading}><RefreshCw size={16}/> Re-answer questions</Button>}{(high || !result.token) && <Button kind="secondary" onClick={onShop}>Return to store</Button>}<Button kind="ghost" onClick={onScammed}><HeartHandshake size={16}/> I was scammed</Button><Button kind="ghost" onClick={onReports}><Flag size={16}/> Report a seller</Button></div>
      <p className="result-disclaimer">ShieldPay is a prototype decision-support layer. A Low risk result is not a guarantee. The backend is the only component authorised to capture payment.</p>
    </section><aside className="result-aside"><div className="surface next-steps"><span className="eyebrow">BEFORE YOU CONTINUE</span><h3>Three sensible checks</h3><div><b>01</b><p><strong>Verify independently</strong><small>Use the seller's official website or a trusted contact method.</small></p></div><div><b>02</b><p><strong>Keep credentials private</strong><small>Never share passwords, PINs or one-time codes.</small></p></div><div><b>03</b><p><strong>Stay on checkout</strong><small>Do not send money through gift cards, crypto or personal transfers.</small></p></div></div><div className="surface report-callout"><Flag size={20}/><h3>Help protect other buyers</h3><p>Share a concern about this seller. Reports remain unverified until reviewed.</p><button className="inline-action" onClick={onReports}>Submit a seller report <ArrowRight size={14}/></button></div></aside></div>
  </>;
}

function ReportsPage({ onSubmit, loading }) {
  const [email,setEmail] = useState("");
  const [reason,setReason] = useState("Brand impersonation");
  const [notice,setNotice] = useState(null);
  const submit = async e => {e.preventDefault();setNotice(null);try {const data=await onSubmit({seller_email:email.trim(),reason});setNotice({ok:true,text:data.note || "Your report was received and is unverified until reviewed."});setEmail("");}catch(err){setNotice({ok:false,text:err.message});}};
  return <><PageTitle eyebrow="COMMUNITY REPORTING" title="Report a suspicious seller" description="A report is a signal for review, not proof that a seller is fraudulent."/>
    <div className="reports-layout"><section className="surface report-form"><div className="surface-heading"><div><h3>Submit a report</h3><p>Do not include passwords, OTPs or card details.</p></div><Flag size={20}/></div>{notice && <div className={`notice ${notice.ok?"notice-success":"notice-error"}`}>{notice.ok?<CheckCircle2 size={17}/>:<CircleAlert size={17}/>}<p>{notice.text}</p></div>}<form onSubmit={submit}><Field label="Seller email address"><input type="email" required maxLength={254} value={email} onChange={e=>setEmail(e.target.value)} placeholder="seller@example.com"/></Field><Field label="Reason"><select value={reason} onChange={e=>setReason(e.target.value)}><option>Brand impersonation</option><option>Suspicious refund request</option><option>Requested payment outside checkout</option><option>Credential or OTP request</option><option>Threats or pressure tactics</option><option>Other suspicious behaviour</option></select></Field><div className="notice notice-info"><LockKeyhole size={16}/><p>Reports are rate-limited, duplicate-checked and stored as Unverified until an administrator reviews them.</p></div><Button type="submit" disabled={loading || !email.trim()}>{loading?<LoaderCircle className="spin" size={16}/>:<Flag size={16}/>} Submit report</Button></form></section>
      <aside className="surface report-policy"><span className="eyebrow">REPORTING GUIDANCE</span><h3>What happens next?</h3><div className="policy-step"><span>1</span><p><strong>Report received</strong><small>The backend checks the seller identifier and duplicate-report limits.</small></p></div><div className="policy-step"><span>2</span><p><strong>Unverified by default</strong><small>A report is not treated as confirmed fraud automatically.</small></p></div><div className="policy-step"><span>3</span><p><strong>Admin review</strong><small>Authorised reviewers can confirm, dispute or remove a report under review rules.</small></p></div><p className="policy-footnote">If money has already been lost, use the official reporting routes on the “I was scammed” page.</p></aside></div>
  </>;
}

function ScammedPage({ order, onFeedback }) {
  const [sent,setSent] = useState(false);
  const [error,setError] = useState("");
  const submit = async value => {setError("");try {await onFeedback(value);setSent(true);}catch(e){setError(e.message);}};
  return <><PageTitle eyebrow="URGENT SUPPORT" title="If you think you've been scammed" description="Act quickly. Contact your bank or payment provider and report the incident through an official channel."/>
    <div className="urgent-banner"><span><LifeBuoy size={22}/></span><div><strong>If money has left your account, contact your bank immediately.</strong><p>In India, call the national cyber financial fraud helpline 1930 as soon as possible.</p></div><a href="tel:1930">Call 1930 <ArrowRight size={15}/></a></div>
    <div className="official-grid"><a className="official-card" href="https://cybercrime.gov.in/" target="_blank" rel="noreferrer"><span className="official-icon"><ShieldCheck size={20}/></span><small>INDIA · OFFICIAL PORTAL</small><strong>National Cyber Crime Reporting Portal</strong><p>Report cybercrime and financial fraud to the Government of India.</p><span className="official-link">Open cybercrime.gov.in <ExternalLink size={14}/></span></a><a className="official-card" href="https://reportfraud.ftc.gov/" target="_blank" rel="noreferrer"><span className="official-icon"><Globe size={20}/></span><small>UNITED STATES · FTC</small><strong>Federal Trade Commission</strong><p>Report fraud and scams to the US consumer protection agency.</p><span className="official-link">Open reportfraud.ftc.gov <ExternalLink size={14}/></span></a><a className="official-card" href="tel:1930"><span className="official-icon"><Smartphone size={20}/></span><small>INDIA · HELPLINE</small><strong>1930 Cyber Fraud Helpline</strong><p>Call promptly if you have experienced financial cyber fraud in India.</p><span className="official-link">Call 1930 <ArrowRight size={14}/></span></a></div>
    <section className="surface feedback-card"><div><span className="eyebrow">HELP IMPROVE SHIELDPAY</span><h3>Did you experience a scam?</h3><p>This feedback is linked to the current demo order when one is available. It does not replace an official police or bank report.</p></div>{sent?<div className="notice notice-success"><CheckCircle2 size={17}/> Feedback received. Thank you.</div>:<div className="feedback-actions"><Button onClick={() => submit(true)}>Yes, I was scammed</Button><Button kind="secondary" onClick={() => submit(false)}>No</Button></div>}{error && <p className="field-error">{error}</p>}</section>
  </>;
}

function PrivacyPage() {
  const support = import.meta.env.VITE_SUPPORT_EMAIL || "Add your monitored support email before launch";
  return <><PageTitle eyebrow="SHIELDPAY / PRIVACY" title="Privacy and data handling" description="A plain-language summary of what the ShieldPay demonstration collects and why."/>
    <div className="privacy-layout"><section className="surface privacy-main"><div className="privacy-row"><span><ClipboardCheck size={19}/></span><div><h3>Information used for a check</h3><p>The order reference, product and seller details, buyer answers, and optional pasted message may be processed to assess checkout risk.</p></div></div><div className="privacy-row"><span><EyeOff size={19}/></span><div><h3>Message redaction and AI processing</h3><p>Before message analysis, ShieldPay masks detected email addresses, phone-like numbers, card-like number sequences and short numeric codes. The redacted message is sent to Google Gemini 3.1 Flash-Lite. This pattern-based redaction is not perfect: never submit passwords, OTPs, full card numbers, bank login details or identity documents. Google's free-tier data-use terms may allow submitted content to be used to improve its services.</p></div></div><div className="privacy-row"><span><DatabaseIcon/></span><div><h3>Data storage</h3><p>Assessment metadata and audit events are stored by the backend. The backend design should avoid retaining raw message content. Review the deployed backend configuration and database policy before public launch.</p></div></div><div className="privacy-row"><span><KeyRound size={19}/></span><div><h3>Payment credentials</h3><p>PayPal handles buyer approval. ShieldPay does not ask for or store PayPal passwords or card details. PayPal secrets must remain on the backend.</p></div></div></section>
      <aside className="surface privacy-contact"><span className="eyebrow">CONTACT</span><Mail size={24}/><h3>Questions about privacy?</h3><p>Contact the ShieldPay team using the monitored address configured for this deployment.</p><strong>{support}</strong><small>Set VITE_SUPPORT_EMAIL before publishing the site. Do not launch with the placeholder value.</small></aside></div>
  </>;
}
function DatabaseIcon(){return <Package size={19}/>;}

function AdminPage() {
  const [password,setPassword] = useState("");
  const [visible,setVisible] = useState(false);
  const [authenticated,setAuthenticated] = useState(false);
  const [reports,setReports] = useState([]);
  const [loading,setLoading] = useState(false);
  const [error,setError] = useState("");
  const [reference,setReference] = useState({});
  const [busyId,setBusyId] = useState("");
  const load = async pass => {setLoading(true);setError("");try {const rows=await api.adminReports(pass);setReports(Array.isArray(rows)?rows:rows.reports||[]);setAuthenticated(true);}catch(e){setAuthenticated(false);setError(e.message);}finally{setLoading(false);}};
  const update = async (report,status) => {setBusyId(report.report_id);setError("");try {await api.adminUpdateReport(password,{report_id:report.report_id,status,reference:reference[report.report_id]||null});await load(password);}catch(e){setError(e.message);}finally{setBusyId("");}};
  if (!authenticated) return <><PageTitle eyebrow="RESTRICTED AREA" title="Administrator access" description="This page uses the backend's admin password check. The password is sent only in the request header."/><section className="surface admin-login"><span className="admin-lock"><KeyRound size={22}/></span><h3>Sign in to report review</h3><p>Enter the admin password configured on the backend.</p><form onSubmit={e=>{e.preventDefault();load(password);}}><Field label="Admin password"><div className="password-wrap"><input type={visible?"text":"password"} value={password} onChange={e=>setPassword(e.target.value)} required autoComplete="current-password"/><button type="button" onClick={()=>setVisible(v=>!v)} aria-label="Toggle password visibility">{visible?<EyeOff size={17}/>:<Eye size={17}/>}</button></div></Field><Button type="submit" disabled={loading || !password}>{loading?<LoaderCircle className="spin" size={16}/>:<KeyRound size={16}/>} Unlock admin</Button></form>{error&&<p className="field-error">{error}</p>}</section></>;
  return <><PageTitle eyebrow="ADMINISTRATION" title="Seller report review" description="Review submitted reports and apply the backend's confirmation requirements." action={<Button kind="secondary" onClick={()=>{setAuthenticated(false);setPassword("");}}><LogOut size={15}/> Sign out</Button>}/>{error&&<div className="notice notice-error"><CircleAlert size={16}/>{error}</div>}<section className="surface admin-reports"><div className="surface-heading"><div><h3>Recent reports</h3><p>Latest reports returned by the backend (up to 200).</p></div><Button kind="secondary" onClick={()=>load(password)} disabled={loading}><RefreshCw size={15}/> Refresh</Button></div>{loading?<div className="empty-state"><LoaderCircle className="spin"/>Loading reports…</div>:reports.length===0?<div className="empty-state"><CheckCircle2/><strong>No reports to review</strong></div>:reports.map(r=><div className="admin-report-row" key={r.report_id}><div className="admin-report-main"><strong>{r.seller_key}</strong><p>{r.reason}</p><small>{r.report_id} · {formatDate(r.created_at)} · Expires {formatDate(r.expires_at)}</small></div><span className={`admin-status ${String(r.status).toLowerCase()}`}>{r.status}</span><div className="admin-controls"><input placeholder="Complaint reference (if needed)" value={reference[r.report_id]||""} onChange={e=>setReference(v=>({...v,[r.report_id]:e.target.value}))}/><div><Button kind="secondary" disabled={busyId===r.report_id || r.status==="Confirmed"} onClick={()=>update(r,"Confirmed")}>Confirm</Button><Button kind="ghost" disabled={busyId===r.report_id} onClick={()=>update(r,"Disputed")}>Dispute</Button><Button kind="ghost" disabled={busyId===r.report_id} onClick={()=>update(r,"Removed")}>Remove</Button></div></div></div>)}</section></>;
}

function CartDrawer({ open, close, products, cart, addToCart, removeFromCart, onCheckout }) {
  if (!open) return null;
  const lines = products.filter(p=>cart[p.product_id]);
  const total = lines.reduce((s,p)=>s+Number(p.price_cents)*cart[p.product_id],0);
  const currency = lines[0]?.currency || "USD";
  return <div className="drawer-overlay" onMouseDown={e=>{if(e.target===e.currentTarget)close();}}><aside className="cart-drawer"><div className="drawer-head"><div><span className="eyebrow">YOUR CART</span><h2>Selected items</h2></div><button className="icon-btn" onClick={close}><X size={19}/></button></div>{lines.length? <><div className="drawer-list">{lines.map(p=><div className="drawer-line" key={p.product_id}><span className="drawer-product-icon"><Package size={20}/></span><div className="drawer-product-copy"><strong>{p.name}</strong><small>{money(Number(p.price_cents)/100,p.currency)}</small><div className="quantity"><button onClick={()=>removeFromCart(p.product_id)}>−</button><span>{cart[p.product_id]}</span><button onClick={()=>addToCart(p.product_id)}>+</button></div></div><strong>{money(Number(p.price_cents)*cart[p.product_id]/100,p.currency)}</strong></div>)}</div><div className="drawer-total"><span>Subtotal</span><strong>{money(total/100,currency)}</strong><Button className="full-width" onClick={onCheckout}>Review checkout <ArrowRight size={16}/></Button></div></>:<div className="empty-state"><ShoppingBag size={26}/><strong>Your cart is empty</strong><p>Add an item from the demo store to begin.</p></div>}</aside></div>;
}

export default function App() {
  const [page,setPage] = useState("dashboard");
  const [mobileOpen,setMobileOpen] = useState(false);
  const [cartOpen,setCartOpen] = useState(false);
  const [cart,setCart] = useState({});
  const [products,setProducts] = useState([]);
  const [catalogLoading,setCatalogLoading] = useState(true);
  const [catalogError,setCatalogError] = useState("");
  const [backendStatus,setBackendStatus] = useState("checking");
  const [aiConfigured,setAiConfigured] = useState(false);
  const [aiModel,setAiModel] = useState("");
  const [order,setOrder] = useState(null);
  const [result,setResult] = useState(null);
  const [assessmentInput,setAssessmentInput] = useState({message:"",answers:[null,null,null]});
  const [reAnswer,setReAnswer] = useState(false);
  const [busy,setBusy] = useState(false);
  const [toast,setToast] = useState("");
  const cartCount = Object.values(cart).reduce((a,b)=>a+b,0);
  const showToast = message => {setToast(message);window.setTimeout(()=>setToast(""),5000);};
  const navigate = target => {setPage(target);setMobileOpen(false);setToast("");};

  const loadCatalog = async () => {setCatalogLoading(true);setCatalogError("");try {const [items,health] = await Promise.all([api.products(),api.health()]);setProducts(items);setBackendStatus("online");setAiConfigured(Boolean(health.ai_configured));setAiModel(health.ai_model || "");}catch(e){setCatalogError(e.message);setBackendStatus("offline");setAiConfigured(false);setAiModel("");}finally{setCatalogLoading(false);}};
  useEffect(()=>{loadCatalog();},[]);

  useEffect(()=>{
    const params=new URLSearchParams(window.location.search);
    const checkoutState=params.get("checkout");
    const pending=localStorage.getItem("shieldpay_pending_order");
    if(!checkoutState || !pending) return;
    try {
      const saved=JSON.parse(pending);
      const paypalOrderId=params.get("token");
      if(checkoutState==="return" && params.get("order_id")===saved.id && paypalOrderId && paypalOrderId===saved.paypalOrderId){
        setOrder(saved);setPage("security");showToast("PayPal approval returned successfully. Complete the ShieldPay check before capture.");
      } else if(checkoutState==="cancel") {showToast("PayPal checkout was cancelled. No payment was captured.");}
      else {showToast("We could not verify the PayPal return. Please restart checkout.");}
    } catch {showToast("The pending checkout could not be restored. Please restart.");}
    localStorage.removeItem("shieldpay_pending_order");
    window.history.replaceState({},document.title,window.location.pathname);
  },[]);

  const addToCart = id => {
    const hasOther=Object.entries(cart).some(([key,qty])=>qty>0 && key!==id);
    if(hasOther){showToast("This backend supports one catalogue product per order. Finish this checkout before selecting another product.");return;}
    if((cart[id]||0)>=10){showToast("The maximum quantity per product is 10.");return;}
    setCart(v=>({...v,[id]:(v[id]||0)+1}));
  };
  const removeFromCart = id => setCart(v=>{const next={...v};if(next[id]<=1)delete next[id];else next[id]-=1;return next;});
  const startCheckout = () => {setCartOpen(false);navigate("checkout");};

  const createOrder = async lines => {
    if(lines.length!==1) return;
    // Open the approval window synchronously from the buyer's click so popup blockers do not suppress it.
    const paypalWindow = window.open("about:blank", "shieldpay-paypal", "popup=yes,width=520,height=720");
    setBusy(true);
    try {
      const line=lines[0];
      const data=await api.createOrder({product_id:line.product_id,quantity:line.quantity});
      const next={id:data.order_id,paypalOrderId:data.paypal_order_id,amount_cents:data.amount_cents,currency:data.currency,productName:data.product_name||line.name,simulated:Boolean(data.simulated)};
      if(!next.id || !next.paypalOrderId) throw new Error("The backend did not return a valid order reference.");
      setOrder(next);localStorage.setItem("shieldpay_pending_order",JSON.stringify(next));
      if(data.approval_url){
        if(paypalWindow && !paypalWindow.closed) paypalWindow.location.href = data.approval_url;
        else window.location.assign(data.approval_url);
        return;
      }
      if(data.simulated){
        if(paypalWindow && !paypalWindow.closed) paypalWindow.close();
        localStorage.removeItem("shieldpay_pending_order");navigate("security");showToast("Mock PayPal mode is active. This is a simulated approval flow, not a real payment.");return;
      }
      throw new Error("Order created, but the PayPal approval URL was missing.");
    }catch(e){if(paypalWindow && !paypalWindow.closed) paypalWindow.close();showToast(e.message);}finally{setBusy(false);}
  };

  const assess = async ({message,answers,reAnswer:correcting=false}) => {
    if(!order?.id){showToast("No active order was found. Start checkout again.");return;}
    setBusy(true);setAssessmentInput({message,answers});setReAnswer(false);
    try {
      const data=await api.assess({order_id:order.id,message:message||null,answers,re_answer:Boolean(correcting)});
      const raw=String(data.outcome||"Unknown");
      const messageCheckFailed=Boolean(data.message_check_failed) || (message && (data.not_checked||[]).some(x=>/message/i.test(x) && /(could not|failed|unavailable|timeout|timed out|not checked)/i.test(x)));
      const level=raw.toLowerCase().includes("high")?"High risk":messageCheckFailed?"Unknown":raw.toLowerCase().includes("suspicious")?"Suspicious":raw.toLowerCase().includes("low")?"Low risk":"Unknown";
      const next={riskLevel:level,score:data.score??null,confidence:data.confidence||"Unknown",reasons:Array.isArray(data.reasons)?data.reasons:[],notChecked:Array.isArray(data.not_checked)?data.not_checked:[],assessmentId:data.assessment_id||null,token:data.token||null,waitSeconds:Number(data.wait_seconds)||0,canReanswer:Boolean(data.can_reanswer),assessedAt:Date.now(),messageCheckFailed,messageAnalysis:data.message_analysis||null};
      setResult(next);navigate("results");
    }catch(e){showToast(e.message);}finally{setBusy(false);}
  };

  const capture = async () => {
    if(!order?.id || !result?.token){showToast("A valid backend assessment token is required. Run the check again.");return;}
    setBusy(true);
    try {
      const data=await api.capture({order_id:order.id,token:result.token,confirm:true});
      if(data.status!=="captured") throw new Error("The backend did not confirm that the payment was captured.");
      setCart({});setOrder(null);setResult(null);setAssessmentInput({message:"",answers:[null,null,null]});localStorage.removeItem("shieldpay_pending_order");navigate("dashboard");showToast("The backend confirmed payment capture.");
    }catch(e){showToast(e.message);}finally{setBusy(false);}
  };
  const submitReport = payload => api.report(payload);
  const sendFeedback = value => {if(!order?.id) throw new Error("There is no current order to attach feedback to.");return api.feedback({order_id:order.id,was_scam:value});};

  const pageContent = useMemo(()=>{
    switch(page){
      case "store":return <StorePage products={products} loading={catalogLoading} error={catalogError} cart={cart} addToCart={addToCart} onCheckout={startCheckout}/>;
      case "checkout":return <CheckoutPage products={products} cart={cart} loading={busy} onCreateOrder={createOrder} onBack={()=>navigate("store")}/>;
      case "security":return <SecurityPage key={reAnswer?"reanswer":"initial"} order={order} loading={busy} onAssess={assess} initialMessage={assessmentInput.message} initialAnswers={assessmentInput.answers} reAnswer={reAnswer}/>;
      case "results":return <ResultPage result={result} order={order} loading={busy} onCapture={capture} onReanswer={()=>{setReAnswer(true);navigate("security");}} onShop={()=>navigate("store")} onScammed={()=>navigate("scammed")} onReports={()=>navigate("reports")}/>;
      case "reports":return <ReportsPage onSubmit={submitReport} loading={busy}/>;
      case "scammed":return <ScammedPage order={order} onFeedback={sendFeedback}/>;
      case "privacy":return <PrivacyPage/>;
      case "admin":return <AdminPage/>;
      default:return <Dashboard onShop={()=>navigate("store")} onReports={()=>navigate("reports")} onPrivacy={()=>navigate("privacy")} backendStatus={backendStatus} aiConfigured={aiConfigured} aiModel={aiModel}/>;
    }
  },[page,products,catalogLoading,catalogError,cart,busy,order,result,assessmentInput,reAnswer,backendStatus,aiConfigured,aiModel]);

  return <><Shell page={page} navigate={navigate} cartCount={cartCount} mobileOpen={mobileOpen} setMobileOpen={setMobileOpen} onCart={()=>setCartOpen(true)} backendStatus={backendStatus}>{pageContent}<div className="admin-entry"><button onClick={()=>navigate("admin")}>Administrator access <KeyRound size={13}/></button></div></Shell>
    <CartDrawer open={cartOpen} close={()=>setCartOpen(false)} products={products} cart={cart} addToCart={addToCart} removeFromCart={removeFromCart} onCheckout={startCheckout}/>
    {toast&&<div className="toast"><CircleAlert size={17}/><span>{toast}</span><button onClick={()=>setToast("")} aria-label="Dismiss"><X size={15}/></button></div>}
  </>;
}
