# Frontend (Next.js)

## Local Development

1. Copy `.env.example` to `.env` and set values.
2. Install dependencies:
   - `npm install`
3. Start dev server:
   - `npm run dev`

## Environment Variables

Required for deployment:

- `JWT_SECRET`: secret used by auth API routes to sign and verify tokens.
- `AI_API_BASE_URL`: base URL of AI backend used by upload/chat routes.
- `NEXT_PUBLIC_NOTIFICATION_SOCKET_URL`: socket server URL for notifications.

## Production Build

- `npm run build`
- `npm run start`

## Deploy (Vercel)

1. Import this `frontend` folder as a Vercel project.
2. Add the variables from `.env.example` in Vercel project settings.
3. Deploy.
