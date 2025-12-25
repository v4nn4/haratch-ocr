import { Storage } from '@google-cloud/storage';

const storage = new Storage({
    projectId: 'haratch-ocr',
});

const BUCKET_NAME = 'haratch-ocr';

export async function getComputationStatus() {
    const [blobs] = await storage.bucket(BUCKET_NAME).getFiles();

    const status: Record<string, { pages: number[], isComplete: boolean, totalPages: number }> = {};
    const metadataBlobs: any[] = [];

    blobs.forEach((blob) => {
        const name = blob.name;

        // ocr/YYYY-MM/page_i.json
        if (name.startsWith('ocr/')) {
            const parts = name.split('/');
            if (parts.length === 3) {
                const issueId = parts[1]; // YYYY-MM
                const pageFile = parts[2]; // page_i.json

                if (pageFile === 'metadata.json') {
                    metadataBlobs.push(blob);
                    return;
                }

                const match = pageFile.match(/\d+/);
                if (match) {
                    const pageNum = parseInt(match[0]);

                    if (!status[issueId]) {
                        status[issueId] = { pages: [], isComplete: false, totalPages: 0 };
                    }
                    if (!status[issueId].pages.includes(pageNum)) {
                        status[issueId].pages.push(pageNum);
                    }
                }
            }
        }
    });

    // Fetch metadata for total page counts (in parallel)
    await Promise.all(metadataBlobs.map(async (blob) => {
        try {
            const [content] = await blob.download();
            const meta = JSON.parse(content.toString());
            const issueId = meta.issue;
            if (status[issueId]) {
                status[issueId].totalPages = meta.total_pages || 0;
            } else {
                // Issue might have metadata but no pages yet
                status[issueId] = { pages: [], isComplete: false, totalPages: meta.total_pages || 0 };
            }
        } catch (e) {
            console.error('Error parsing metadata:', e);
        }
    }));

    // Sort pages for each issue and derive isComplete
    for (const issueId in status) {
        status[issueId].pages.sort((a, b) => a - b);

        // Coherence Check: strictly complete only if all pages are accounted for
        if (status[issueId].totalPages > 0 &&
            status[issueId].pages.length >= status[issueId].totalPages) {
            status[issueId].isComplete = true;
        } else {
            status[issueId].isComplete = false;
        }
    }

    return status;
}

export async function getRunnerStatus() {
    try {
        const [content] = await storage.bucket(BUCKET_NAME).file('status/runner.json').download();
        return JSON.parse(content.toString());
    } catch (error) {
        console.warn('Runner status not found or invalid format, checking legacy runner.txt');
        try {
            const [content] = await storage.bucket(BUCKET_NAME).file('status/runner.txt').download();
            return {
                status: content.toString().trim(),
                ram_mb: 0,
                disk_mb: 0,
                last_updated: new Date().toISOString()
            };
        } catch (e) {
            return {
                status: 'idle',
                ram_mb: 0,
                disk_mb: 0,
                last_updated: null
            };
        }
    }
}
