# PhishGuard Frontend

A modern, responsive Next.js frontend for the PhishGuard email and URL security scanner.

## Quick Start

### Prerequisites
- Node.js 18+
- Firebase project setup

### Installation

1. **Install dependencies**
```bash
npm install
```

2. **Set up environment variables**

Copy `.env.example` to `.env.local` and fill in your Firebase credentials:

```bash
cp .env.example .env.local
```

Edit `.env.local` with your Firebase project details:
```
NEXT_PUBLIC_FIREBASE_API_KEY=your_key
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=your_domain
NEXT_PUBLIC_FIREBASE_PROJECT_ID=your_project
NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET=your_bucket
NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID=your_id
NEXT_PUBLIC_FIREBASE_APP_ID=your_app_id
NEXT_PUBLIC_API_URL=http://localhost:8000
```

3. **Run development server**
```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

## Project Structure

```
app/
├── page.tsx              # Landing page
├── layout.tsx            # Root layout
├── globals.css           # Global styles
├── login/page.tsx        # Login page
├── signup/page.tsx       # Signup page
├── dashboard/
│   ├── layout.tsx
│   └── page.tsx          # Dashboard
├── scanner/
│   ├── layout.tsx
│   ├── email/page.tsx    # Email scanner
│   └── url/page.tsx      # URL scanner
├── history/page.tsx      # Scan history
└── profile/page.tsx      # User profile

components/
├── ui/                   # Reusable UI components
├── Sidebar.tsx
└── DashboardLayout.tsx

lib/
├── firebase.ts           # Firebase config
├── api.ts                # API client
├── store.ts              # Zustand stores
├── hooks.ts              # Custom React hooks
└── utils.ts              # Utility functions
```

## Features

- ✅ Firebase Authentication (Email & Google)
- ✅ Email Scanner with detailed analysis
- ✅ URL Scanner
- ✅ Scan History with Firestore
- ✅ User Profile management
- ✅ Responsive design
- ✅ Black & White theme
- ✅ Real-time results

## Build & Deploy

```bash
# Build for production
npm run build

# Start production server
npm start
```

## Connect Backend

Make sure the FastAPI backend is running on `http://localhost:8000`:

```bash
python -m uvicorn app:app --reload --port 8000
```

The frontend will automatically connect to the backend API for phishing detection analysis.

## Tech Stack

- **Next.js 14** - React framework
- **TypeScript** - Type safety
- **Tailwind CSS** - Styling
- **Firebase** - Authentication & Firestore
- **Zustand** - State management
- **React Hook Form** - Form handling
- **Axios** - HTTP client

## License

Private - All rights reserved
