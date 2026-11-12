# ShieldPay
### AI-Powered Payment Protection System

ShieldPay is an AI-powered payment protection platform designed to make online transactions safer by identifying potential scams before payments are completed.

It combines AI-based risk analysis with PayPal payment processing to help users identify suspicious recipients, detect potential fraud, and make more informed payment decisions.

---

## Live Application

**Deployed Application URL:**https://shieldpay-frontend-42oz.onrender.com/

**GitHub Repository:** https://github.com/aanyanya09/protect-pay

---

## Problem Statement

Online payment scams are becoming increasingly common. Users may unknowingly transfer money to fraudulent recipients because they lack sufficient information to evaluate payment requests.

Traditional payment systems primarily focus on processing transactions rather than helping users understand potential risks before paying.

ShieldPay addresses this problem by introducing an additional risk-assessment layer before payment processing.

## Our Solution

ShieldPay analyses payment information using risk-detection logic and AI-assisted message analysis.

Based on the assessment, transactions are classified into three risk levels:

- **Low Risk:** The transaction can proceed through the payment workflow.
- **Suspicious:** Additional verification and buyer confirmation are required.
- **High Risk:** The transaction is blocked to help prevent potential financial loss.

The goal is to provide users with an additional layer of protection before completing online payments.

## Key Features

- **AI-Assisted Fraud Detection:** Analyses payment-related messages for suspicious patterns.
- **Risk Classification:** Categorises transactions into Low, Suspicious, and High risk.
- **Recipient Verification:** Evaluates recipient information against configured risk rules.
- **Payment Protection:** Applies risk-based checks before allowing payment capture.
- **Secure Payment Workflow:** Supports PayPal order creation and payment capture.
- **Buyer Confirmation:** Introduces additional verification for suspicious transactions.
- **Interactive Dashboard:** Provides a simple interface to understand transaction status and risk results.
- **Demo Mode:** Allows the payment workflow to be demonstrated without transferring real money.

## Technology Stack

| Component | Technology |
|---|---|
| Frontend | React.js |
| Build Tool | Vite |
| Styling | CSS |
| Backend | Python |
| Backend Framework | FastAPI |
| Payment Platform | PayPal Developer Platform |
| Payment API | PayPal REST Orders API |
| AI Service | Google Gemini API |
| Database | SQLite |
| Testing | Pytest |

## AI Integration

ShieldPay is designed to use Google Gemini AI for analysing payment-related messages and identifying potential scam indicators.

The AI component helps:

- Identify suspicious language and payment requests.
- Analyse possible scam patterns.
- Provide risk-related explanations.
- Support transaction risk assessment.

The project also uses rule-based checks to complement AI analysis.

## PayPal Integration

ShieldPay is designed around the PayPal Developer Platform.

The payment workflow uses:

- **PayPal OAuth 2.0:** Backend authentication.
- **PayPal REST API:** Payment order creation.
- **PayPal Orders API:** Payment capture.
- **PayPal Sandbox:** Testing transactions without using real money.

**Current implementation status:** The tested project configuration uses mock payment mode. Actual PayPal Sandbox transactions require valid Sandbox credentials and configuration.

## Project Architecture

```text
                 USER
                   |
                   v
            REACT FRONTEND
                   |
                   v
             FASTAPI BACKEND
                   |
          +--------+--------+
          |                 |
          v                 v
     RISK ANALYSIS      AI ANALYSIS
          |             GEMINI API
          |                 |
          +--------+--------+
                   |
                   v
            RISK CLASSIFICATION
                   |
          +--------+--------+
          |        |        |
          v        v        v
         LOW   SUSPICIOUS  HIGH
          |        |        |
          v        v        v
       PAYMENT  ADDITIONAL  BLOCK
       FLOW     VERIFICATION
          |
          v
      PAYPAL PAYMENT
```

## Project Structure

```text
protect-pay/
│
├── backend/
│   ├── main.py
│   ├── ai_message_checker.py
│   ├── database.py
│   ├── paypal_client.py
│   ├── routes_extra.py
│   ├── rules.py
│   ├── security.py
│   ├── token_service.py
│   ├── requirements.txt
│   └── tests/
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── data/
│   │   ├── services/
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   └── styles.css
│   ├── index.html
│   ├── package.json
│   ├── package-lock.json
│   └── vite.config.js
│
├── docs/
├── scripts/
├── .env.example
├── .gitignore
└── README.md
```

## Running the Project Locally

### Prerequisites

- Python 3.10 or higher
- Node.js and npm
- Git

### 1. Clone the Repository

```bash
git clone https://github.com/aanyanya09/protect-pay.git
cd protect-pay
```

### 2. Backend Setup

```bash
cd backend
python -m venv .venv
```

Activate the environment on Windows:

```powershell
.venv\Scripts\activate
```

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

Configure the backend environment variables using the provided `.env.example` file.

Start the backend:

```bash
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

Backend URL:

```text
http://127.0.0.1:8000
```

### 3. Frontend Setup

Open another terminal:

```bash
cd frontend
npm install
```

Configure the frontend API URL in your local environment file:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

Start the frontend:

```bash
npm run dev
```

Open the application:

```text
http://localhost:5173
```

## Environment Configuration

Configure the required environment variables using the provided example files.

Typical configuration includes:

- `PAYPAL_MODE` – Selects mock or Sandbox payment mode.
- PayPal Client ID and Secret – Sandbox authentication credentials.
- `GEMINI_API_KEY` – Google Gemini API access.
- `TOKEN_SECRET` – Secret used for payment-token security.
- `ADMIN_PASSWORD` – Administrative authentication.
- `WAIT_SECONDS` – Configures the additional verification waiting period.

**Security:** Never commit `.env` files, API keys, passwords, or private credentials to GitHub.

## Testing

The backend includes automated tests using Pytest.

Run the test suite:

```bash
pytest -q
```

The current backend test suite has passed 24 tests in the local development environment.

The project has also been tested in mock payment mode to verify risk classification, payment workflow behaviour, and duplicate-capture protection.

## Future Improvements

- Complete and validate PayPal Sandbox integration.
- Complete and test Gemini API integration.
- Improve recipient reputation verification.
- Add transaction history and analytics.
- Enhance fraud detection using additional data sources.
- Introduce more advanced AI-based fraud analysis.
- Improve deployment scalability and monitoring.

## Potential Applications

ShieldPay can be useful for:

- Individuals making online payments.
- Freelancers receiving payments from unfamiliar clients.
- Small businesses handling online transactions.
- Users evaluating suspicious payment requests.
- Digital payment platforms seeking additional fraud-prevention features.

## Project Vision

Our vision is to make digital payments safer and more transparent by combining intelligent fraud detection with trusted payment infrastructure.

**ShieldPay — Think Before You Pay. Stay Protected.**

---

## Disclaimer

ShieldPay is a prototype developed for demonstration and hackathon purposes. Its risk assessments are not guarantees that a transaction is safe or fraudulent. Always verify payment recipients independently. Mock payment mode does not transfer real money.