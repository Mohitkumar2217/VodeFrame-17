'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { auth, User } from '../lib/auth';
import Navigation from '../components/Navigation';
import { useDocuments, UploadedDocument } from '../contexts/DocumentContext';
  
const PortalContent: React.FC = () => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    if (!auth.isAuthenticated()) {
      router.push('/login');
      return;
    }
    setUser(auth.getUser());
    setLoading(false);
  }, [router]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-black">
        <div className="text-white text-xl animate-pulse">Loading...</div>
      </div>
    );
  }

  if (!user) return null;

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 to-black text-white">
      <Navigation />
      <div className="max-w-6xl mx-auto py-24 px-6">
        {user.role === 'mdoner' ? <MDoNERDashboard /> : <ClientDashboard />}
      </div>
    </div>
  );
};
 
  //  ADMIN (MDoNER) DASHBOARD 
const MDoNERDashboard: React.FC = () => {
  const { getAllDocuments, updateDocumentStatus } = useDocuments();
  const [selectedFilter, setSelectedFilter] = useState<'all' | UploadedDocument['status']>('all');

  const all = getAllDocuments();

  const filtered =
    selectedFilter === 'all' ? all : all.filter(doc => doc.status === selectedFilter);

  const counts = {
    pending: all.filter(d => d.status === 'pending').length,
    'under-review': all.filter(d => d.status === 'under-review').length,
    approved: all.filter(d => d.status === 'approved').length,
    rejected: all.filter(d => d.status === 'rejected').length,
    viewed: all.filter(d => d.status === 'viewed').length,
  };

  const handleStatusUpdate = (id: string, status: UploadedDocument['status']) => {
    const msg = {
      pending: 'Pending review.',
      viewed: 'Document viewed.',
      'under-review': 'Review started.',
      approved: 'Approved successfully.',
      rejected: 'Rejected due to issues.',
    };
    updateDocumentStatus(id, status, msg[status], {
      name: "MDoNER Admin",
      email: "admin@mdoner.gov.in",
    });
  };

  return (
    <div className="w-full">
      {/* Title */}
      <h2 className="text-3xl font-bold text-white mb-10">📊 Admin Dashboard</h2>

      {/* Status Cards */}
      <div className="grid md:grid-cols-5 gap-6 mb-12">
        {Object.entries(counts).map(([key, val]) => (
          <div
            key={key}
            className="p-6 rounded-2xl bg-white/5 border border-white/10 backdrop-blur-lg shadow-xl"
          >
            <p className="text-gray-300 text-sm capitalize">{key.replace('-', ' ')}</p>
            <p className="text-4xl font-bold text-blue-400 mt-1">{val}</p>
          </div>
        ))}
      </div>

      {/* Filter Buttons */}
      <div className="flex gap-3 mb-8">
        {(['all', ...Object.keys(counts)] as Array<'all' | UploadedDocument['status']>).map(f => (
          <button
            key={f}
            onClick={() => setSelectedFilter(f)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-all
              ${
                selectedFilter === f
                  ? 'bg-blue-600 text-white'
                  : 'bg-white/10 text-gray-300 hover:bg-white/20'
              }`}
          >
            {f.toString().replace('-', ' ').toUpperCase()}
          </button>
        ))}
      </div>

      {/* Document List */}
      <div className="space-y-4">
        {filtered.map(doc => (
          <div
            key={doc.id}
            className="bg-white/5 border border-white/10 p-6 rounded-2xl hover:bg-white/10 transition"
          >
            <div className="flex justify-between items-start">
              <div>
                <p className="text-white text-lg font-semibold">{doc.name}</p>
                <p className="text-gray-400 text-sm mt-1">{doc.uploadDate}</p>
                <p className="text-gray-500 text-xs">
                  Uploaded by: {doc.uploadedBy?.name || 'Client'}
                </p>
              </div>
            </div>

            <div className="flex gap-2 mt-4">
              <button
                onClick={() => handleStatusUpdate(doc.id, 'viewed')}
                className="px-4 py-2 text-xs bg-blue-600/20 text-blue-400 rounded-lg hover:bg-blue-600/30"
              >
                Viewed
              </button>
              <button
                onClick={() => handleStatusUpdate(doc.id, 'under-review')}
                className="px-4 py-2 text-xs bg-purple-600/20 text-purple-300 rounded-lg hover:bg-purple-600/30"
              >
                Review
              </button>
              <button
                onClick={() => handleStatusUpdate(doc.id, 'approved')}
                className="px-4 py-2 text-xs bg-green-600/20 text-green-300 rounded-lg hover:bg-green-600/30"
              >
                Approve
              </button>
              <button
                onClick={() => handleStatusUpdate(doc.id, 'rejected')}
                className="px-4 py-2 text-xs bg-red-600/20 text-red-300 rounded-lg hover:bg-red-600/40"
              >
                Reject
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
 
  //  CLIENT DASHBOARD (UPLOAD + AI ANALYSIS) 
const ClientDashboard: React.FC = () => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadStatus, setUploadStatus] =
    useState<'idle' | 'uploading' | 'success' | 'error'>('idle');
  const [uploadMessage, setUploadMessage] = useState<string>('');
  const [evaluation, setEvaluation] = useState<string | null>(null);
  const [reviewedPdfUrl, setReviewedPdfUrl] = useState<string | null>(null);

  const { addDocument } = useDocuments();
  const user = auth.getUser();

  const handleUpload = async () => {
    if (!selectedFile) return
    setUploadStatus("uploading");
    setUploadMessage('');

    try {
      const form = new FormData();
      form.append("file", selectedFile);

      const res = await fetch("/api/dpr/upload", {
        method: "POST",
        body: form,
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.message || "Upload failed");

      setEvaluation(data.evaluation);
      setReviewedPdfUrl(data.highlightedPdfUrl || null);

      // Local UI state
      addDocument({
        name: selectedFile.name,
        size: selectedFile.size,
        status: "pending",
        uploadDate: new Date().toISOString(),
        reviewerComments: "AI Reviewed",
        evaluationData: data,
        uploadedBy: {
          name: user?.name || "Client",
          email: user?.email || "",
        },
      });

      setUploadStatus("success");
      setUploadMessage(data.message || 'Document uploaded and analyzed.');
    } catch (err) {
      console.error(err);
      setUploadStatus("error");
      setUploadMessage('Upload failed. Please try again.');
    }
  };

  return (
    <div className="w-full">
      <h2 className="text-white text-3xl font-bold mb-8">📄 Analysis Dashboard</h2>

      {/* Upload Card */}
      <div className="bg-white/5 border border-white/10 p-8 rounded-2xl backdrop-blur-lg shadow-lg">
        <p className="text-gray-300 mb-3">Upload your DPR PDF file</p>

        <label className="block w-full p-6 border border-white/20 rounded-xl bg-white/5 text-center text-gray-300 cursor-pointer hover:bg-white/10">
          {selectedFile ? selectedFile.name : "Click to select a PDF"}
          <input
            type="file"
            accept=".pdf"
            className="hidden"
            onChange={e => setSelectedFile(e.target.files?.[0] || null)}
          />
        </label>

        {selectedFile && (
          <button
            onClick={handleUpload}
            className="mt-6 w-full py-3 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-xl hover:opacity-90"
          >
            {uploadStatus === "uploading" ? "Analyzing..." : "Upload & Analyze"}
          </button>
        )}
        {uploadMessage && (
          <p className={`mt-4 text-sm ${uploadStatus === 'error' ? 'text-red-300' : 'text-green-300'}`}>
            {uploadMessage}
          </p>
        )}
      </div>

      {/* AI Report */}
      {evaluation && (
        <div className="mt-10 bg-white/5 border border-white/10 p-8 rounded-2xl">
          <h3 className="text-2xl text-white font-semibold mb-4">AI Evaluation Report</h3>
          <pre className="whitespace-pre-wrap text-gray-200 bg-black/20 p-6 rounded-xl">
            {evaluation}
          </pre>
        </div>
      )}

     

      {/* PDF Preview */}
      {reviewedPdfUrl && (
        <div className="mt-10">
          <h3 className="text-xl text-white font-semibold mb-3">Highlighted PDF</h3>

          <iframe
            src={reviewedPdfUrl}
            className="w-full h-[600px] rounded-xl border border-white/20"
          />

          <a
            target="_blank"
            href={reviewedPdfUrl}
            className="mt-4 inline-block bg-green-600 px-6 py-3 rounded-xl text-white hover:bg-green-700"
          >
            Download Reviewed PDF
          </a>
        </div>
      )}
    </div>
  );
};

export default PortalContent;
