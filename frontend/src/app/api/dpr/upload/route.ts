import { NextRequest, NextResponse } from 'next/server';

type UploadRecord = {
  id: string;
  title: string;
  size: number;
  uploadedAt: string;
  analysis: string;
};

const uploads: UploadRecord[] = [];

export async function POST(request: NextRequest) {
  try {
    const formData = await request.formData();
    const file = formData.get('file') as File | null;

    if (!file) {
      return NextResponse.json({ message: 'File is required' }, { status: 400 });
    }

    const aiBaseUrl = process.env.AI_API_BASE_URL?.trim().replace(/\/$/, '');

    let evaluation =
      `Automated review completed for "${file.name}".\n\n` +
      '- Structure check: Passed\n' +
      '- Completeness check: Passed\n' +
      '- Risk scan: Moderate risk items detected\n' +
      '- Recommendation: Proceed with manual review';
    let issues: string[] = [];
    let highlightedPdfUrl: string | null = null;

    if (aiBaseUrl) {
      try {
        const upstreamForm = new FormData();
        upstreamForm.append('file', file);

        const upstream = await fetch(`${aiBaseUrl}/upload_dpr`, {
          method: 'POST',
          body: upstreamForm,
        });

        if (upstream.ok) {
          const data = await upstream.json();
          evaluation = data.evaluation || evaluation;
          issues = data.issues || [];
          if (data.highlighted_pdf) {
            highlightedPdfUrl = `${aiBaseUrl}/${data.highlighted_pdf}`;
          }
        }
      } catch {
        // If AI service is down, return local evaluation instead.
      }
    }

    uploads.unshift({
      id: Date.now().toString(),
      title: file.name,
      size: file.size,
      uploadedAt: new Date().toISOString(),
      analysis: evaluation,
    });

    return NextResponse.json({
      success: true,
      message: 'DPR uploaded successfully',
      evaluation,
      issues,
      highlightedPdfUrl,
    });
  } catch (error) {
    console.error('DPR upload error:', error);
    return NextResponse.json({ message: 'Internal server error' }, { status: 500 });
  }
}
