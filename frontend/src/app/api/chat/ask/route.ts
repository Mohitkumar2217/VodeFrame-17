import { NextRequest, NextResponse } from 'next/server';

const FALLBACK_ANSWER =
  'I can help with DPR workflow, status checks, and risk review steps. If you need specific guidance, ask about upload, review, approval, or rejection flow.';

export async function POST(request: NextRequest) {
  try {
    const { query } = await request.json();
    if (!query || typeof query !== 'string') {
      return NextResponse.json({ message: 'Query is required' }, { status: 400 });
    }

    const aiBaseUrl = process.env.AI_API_BASE_URL?.trim().replace(/\/$/, '');

    if (aiBaseUrl) {
      try {
        const upstream = await fetch(`${aiBaseUrl}/ask`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ query }),
        });

        if (upstream.ok) {
          const data = await upstream.json(); 
          return NextResponse.json({ answer: data.answer || FALLBACK_ANSWER });
        }
      } catch {
        // fall through to local fallback response
      }
    }

    return NextResponse.json({ answer: FALLBACK_ANSWER });
  } catch (error) {
    console.error('Chat route error:', error);
    return NextResponse.json({ message: 'Internal server error' }, { status: 500 });
  }
}
