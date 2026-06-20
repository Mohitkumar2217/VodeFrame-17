import Navigation from '../../components/Navigation'
export default function DPRAnalysisFlow() {
  return (
    <>
      <Navigation />
      <div className='min-h-screen bg-gradient-to-br from-gray-900 to-black text-white'>
        <div className="pt-30 px-50">
          <h1 className="text-4xl font-bold mb-6">
            DPR Analysis Workflow
          </h1>

          <p className="text-gray-600 mb-8">
            This module evaluates a Detailed Project Report (DPR) and generates
            a quality score, improvement suggestions, and clarification questions.
          </p>

          <div className="space-y-6">

            <div className="rounded-lg p-6">
              <h2 className="text-xl font-semibold">
                Step 1: DPR Upload
              </h2>
              <p>
                User uploads the DPR document in PDF or DOCX format.
                The system validates file size, format, and readability.
              </p>
            </div>

            <div className="rounded-lg p-6">
              <h2 className="text-xl font-semibold">
                Step 2: Content Extraction
              </h2>
              <p>
                The document is processed to extract structured content such as:
              </p>

              <ul className="list-disc ml-6 mt-2">
                <li>Project Overview</li>
                <li>Objectives</li>
                <li>Financial Projections</li>
                <li>Market Analysis</li>
                <li>Implementation Plan</li>
                <li>Risk Assessment</li>
              </ul>
            </div>

            <div className="rounded-lg p-6">
              <h2 className="text-xl font-semibold">
                Step 3: AI Evaluation
              </h2>
              <p>
                AI reviews the extracted information against predefined
                evaluation criteria and identifies strengths, weaknesses,
                missing information, and inconsistencies.
              </p>
            </div>

            <div className="rounded-lg p-6">
              <h2 className="text-xl font-semibold">
                Step 4: Scoring Engine
              </h2>

              <p>
                A weighted scoring model generates ratings across key categories:
              </p>

              <ul className="list-disc ml-6 mt-2">
                <li>Technical Feasibility (20%)</li>
                <li>Financial Viability (25%)</li>
                <li>Market Potential (20%)</li>
                <li>Risk Management (15%)</li>
                <li>Operational Readiness (10%)</li>
                <li>Sustainability (10%)</li>
              </ul>
            </div>

            <div className="rounded-lg p-6">
              <h2 className="text-xl font-semibold">
                Step 5: Clarification Questions
              </h2>

              <p>
                If important information is missing or unclear, the system
                generates targeted questions for the user.
              </p>

              <div className="p-4 rounded mt-3">
                <p>Example Questions:</p>
                <ul className="list-disc ml-6">
                  <li>What is the projected ROI period?</li>
                  <li>How are operational risks mitigated?</li>
                  <li>What assumptions support revenue forecasts?</li>
                </ul>
              </div>
            </div>

            <div className="rounded-lg p-6">
              <h2 className="text-xl font-semibold">
                Step 6: Final Report Generation
              </h2>

              <p>
                The platform generates a final DPR assessment including:
              </p>

              <ul className="list-disc ml-6 mt-2">
                <li>Overall Rating</li>
                <li>Category-wise Scores</li>
                <li>Strengths</li>
                <li>Weaknesses</li>
                <li>Recommended Improvements</li>
                <li>Clarification Questions</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
