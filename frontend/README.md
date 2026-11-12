# ShieldPay Frontend

React + Vite browser interface for ShieldPay. The frontend talks only to the ShieldPay FastAPI backend; it never stores Gemini or PayPal secrets and never calls PayPal capture directly.

## Local setup (Windows PowerShell)

```powershell
Copy-Item .env.example .env
npm install
npm run dev
```

Set `VITE_API_BASE_URL=http://127.0.0.1:8000` in `.env`, then open the Vite URL printed in the terminal (normally http://localhost:5173).

## Backend connection

The frontend consumes `/api/health`, `/api/products`, `/api/orders`, `/api/assess`, `/api/capture`, `/api/reports`, `/api/feedback`, and the admin report endpoints. Risk outcomes and tokens are backend-owned.

## Privacy

The buyer message is capped at 2,000 characters. The backend redacts detected emails, phone-like numbers, card-like digit sequences, and short codes before sending it to Google Gemini. Redaction is pattern-based and imperfect. Google's free-tier data-use terms may permit submitted content to be used to improve Google products. Do not paste secrets or real payment credentials.
