import { NextResponse } from 'next/server';
import { getComputationStatus } from '@/utils/gcs';

export const dynamic = 'force-dynamic';

export async function GET() {
    try {
        const status = await getComputationStatus();
        return NextResponse.json(status);
    } catch (error) {
        console.error('Error fetching status:', error);
        return NextResponse.json({ error: 'Failed to fetch status' }, { status: 500 });
    }
}
