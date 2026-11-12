export const products = [
  { id: "p1", name: "Studio Wireless Headphones", category: "Audio", price: 6499, oldPrice: 7999, rating: "4.8", reviews: 284, tag: "Bestseller", icon: "headphones", color: "violet", description: "Immersive sound, adaptive noise cancellation and all-day comfort." },
  { id: "p2", name: "Pulse Smart Watch", category: "Wearables", price: 8999, oldPrice: 10999, rating: "4.7", reviews: 196, tag: "Popular", icon: "watch", color: "blue", description: "A refined everyday smartwatch with health and activity insights." },
  { id: "p3", name: "Arc Mechanical Keyboard", category: "Accessories", price: 5299, oldPrice: null, rating: "4.9", reviews: 142, tag: "Editor's pick", icon: "keyboard", color: "orange", description: "A tactile low-profile keyboard built for focused work." },
  { id: "p4", name: "Orbit Portable Speaker", category: "Audio", price: 3799, oldPrice: 4499, rating: "4.6", reviews: 118, tag: "New arrival", icon: "speaker", color: "green", description: "Room-filling sound in a compact, travel-ready design." }
];

export const initialReports = [
  { id: "SP-1048", seller: "paypa1-support@gmail.com", reason: "Brand impersonation", status: "Under review", date: "Today, 10:42 AM" },
  { id: "SP-1041", seller: "quick-refund-help.co", reason: "Suspicious refund request", status: "Confirmed", date: "Yesterday" },
  { id: "SP-1036", seller: "market-deals.store", reason: "Requested payment outside checkout", status: "Under review", date: "2 days ago" }
];

export const money = (amount, currency = "USD") => new Intl.NumberFormat("en-US", {
  style: "currency", currency, maximumFractionDigits: 2
}).format(amount);
