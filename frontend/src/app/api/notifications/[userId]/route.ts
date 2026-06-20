import { NextResponse } from 'next/server';

type Params = { params: Promise<{ userId: string }> };

const notificationsByUser: Record<string, Array<{
  id: number;
  userId: number; 
  message: string;
  read: boolean;
  createdAt: string;
}>> = {
  '1': [
    {
      id: 1,
      userId: 1, 
      message: 'Welcome back, MDoNER Administrator.',
      read: false,
      createdAt: new Date().toISOString(),
    },
    {
      id: 2,
      userId: 1, 
      message: 'Welcome back, MDoNER Administrator.',
      read: false,
      createdAt: new Date().toISOString(),
    },
  ],
  '2': [
    {
      id: 3,
      userId: 2, 
      message: 'Welcome back. You can upload a DPR from the portal dashboard.',
      read: false,
      createdAt: new Date().toISOString(),
    },
    {
      id: 4,
      userId: 2, 
      message: 'Welcome back. You can upload a DPR from the portal dashboard.',
      read: false,
      createdAt: new Date().toISOString(),
    },
  ],
};

export async function GET(_: Request, { params }: Params) {
  const { userId } = await params;
  return NextResponse.json(notificationsByUser[userId] || []);
}
