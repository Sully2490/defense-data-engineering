# Ferrum Frontend

AI-powered defense supply chain intelligence platform frontend built with Next.js 14.

## Tech Stack

- Next.js 14 (App Router)
- React 18
- TypeScript
- Tailwind CSS
- Lucide React (icons)

## Getting Started

1. Install dependencies:
```bash
npm install
```

2. Set environment variables:
```bash
cp .env.local.example .env.local
# Edit .env.local with your API URL
```

3. Run development server:
```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

## Project Structure

```
src/
├── app/                    # Next.js App Router pages
│   ├── (auth)/            # Authentication pages
│   ├── (dashboard)/       # Dashboard pages
│   └── layout.tsx         # Root layout
├── components/            # React components
│   ├── layout/           # Layout components
│   ├── search/           # Search components
│   ├── suppliers/        # Supplier components
│   └── ui/              # UI primitives
├── hooks/                # Custom React hooks
└── lib/                  # Utilities and API client
    ├── api.ts           # API client
    ├── auth.tsx         # Auth context
    ├── types.ts         # TypeScript types
    └── utils.ts         # Utility functions
```

## Features

- User authentication (login/register)
- Supplier management and detail views
- Material catalog browsing
- AI-powered natural language search
- Organization settings
- Responsive design with Tailwind CSS

## Build

```bash
npm run build
npm start
```

## Environment Variables

- `NEXT_PUBLIC_API_URL` - Backend API URL (default: http://localhost:8000/api/v1)
