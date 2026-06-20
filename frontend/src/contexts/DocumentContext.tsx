"use client";

import React, { createContext, useContext, useState, ReactNode } from "react";

//  DOCUMENT TYPE (Updated with evaluationData) 
export interface UploadedDocument {
  id: string;
  name: string;
  size: number;
  uploadDate: string;
  status: "viewed" | "under-review" | "approved" | "rejected" | "pending";
  reviewerComments?: string;

  uploadedBy: {
    name: string;
    email: string;
    department?: string; // optional
  };

  reviewedBy?: {
    name: string;
    email: string;
  };

  reviewDate?: string;

  evaluationData?: Record<string, unknown>; // NEW FIELD for AI results
}

//  CONTEXT TYPE 
interface DocumentContextType {
  documents: UploadedDocument[];
  addDocument: (document: Omit<UploadedDocument, "id">) => void;
  updateDocumentStatus: (
    id: string,
    status: UploadedDocument["status"],
    comments?: string,
    reviewedBy?: { name: string; email: string }
  ) => void;
  getClientDocuments: (clientEmail: string) => UploadedDocument[];
  getAllDocuments: () => UploadedDocument[];
}

//  INIT CONTEXT 
const DocumentContext = createContext<DocumentContextType | undefined>(
  undefined
);

export const useDocuments = () => {
  const context = useContext(DocumentContext);
  if (!context) {
    throw new Error("useDocuments must be used within a DocumentProvider");
  }
  return context;
};

//  PROVIDER 
export const DocumentProvider: React.FC<{ children: ReactNode }> = ({
  children,
}) => {
  const [documents, setDocuments] = useState<UploadedDocument[]>([]);

  //  ADD A DOCUMENT 
  const addDocument = (document: Omit<UploadedDocument, "id">) => {
    const newDocument: UploadedDocument = {
      ...document,
      id: Date.now().toString(),

      // If user forgot to include "uploadedBy", set default
      uploadedBy: document.uploadedBy || {
        name: "Client",
        email: "client@system",
        department: "Client",
      },
    };

    setDocuments((prev) => [newDocument, ...prev]);
  };

  //  UPDATE STATUS (Admin Only) 
  const updateDocumentStatus = (
    id: string,
    status: UploadedDocument["status"],
    comments?: string,
    reviewedBy?: { name: string; email: string }
  ) => {
    setDocuments((prev) =>
      prev.map((doc) =>
        doc.id === id
          ? {
            ...doc,
            status,
            reviewerComments: comments ?? doc.reviewerComments,
            reviewedBy: reviewedBy ?? doc.reviewedBy,
            reviewDate: new Date().toISOString(),
          }
          : doc
      )
    );
  };

  // FILTER BY CLIENT 
  const getClientDocuments = (clientEmail: string) => {
    return documents.filter((doc) => doc.uploadedBy.email === clientEmail);
  };

  // RETURN ALL 
  const getAllDocuments = () => documents;

  return (
    <DocumentContext.Provider
      value={{
        documents,
        addDocument,
        updateDocumentStatus,
        getClientDocuments,
        getAllDocuments,
      }}
    >
      {children}
    </DocumentContext.Provider>
  );
};
