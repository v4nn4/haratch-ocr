import { NextResponse } from 'next/server';
import { getRunnerStatus } from '@/utils/gcs';

export const dynamic = 'force-dynamic';

export async function GET() {
    try {
        const runnerStatus = await getRunnerStatus();
        return NextResponse.json(runnerStatus);
    } catch (error) {
        console.error('Error fetching runner status:', error);
        return NextResponse.json({ error: 'Failed' }, { status: 500 });
    }
}
