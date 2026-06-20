import mongoose, { Document, Schema } from "mongoose";

interface IEvaluations {
    evaluation?: string;
    issues?: string[];
    highlighted_pdf?: string;
    raw?: Record<string, any>;
}
export interface IDPR extends Document {
    title: string;
    description: string;
    fileUrl: string;
    publicId: string;
    uploadedBy: string;
    risk?: number;
    completeness?: number;
    evaluationData?: IEvaluations;
    createdAt: Date;
    updatedAt: Date;
}

const dprSchema = new Schema<IDPR>(
    {
        title: {
            type: String,
            required: true,
        },
        description: {
            type: String,
        },
        fileUrl: {
            type: String,
            required: true,
        },
        publicId: {
            type: String,
            required: true,
        },
        uploadedBy: {
            type: String,
            default: "client",   // STATIC — always client
        },
        risk: {
            type: Number,
        },
        completeness: {
            type: Number,
        },
        evaluationData: {
            evaluation: {
                type: String,        // AI final report
            },     
            issues: [
                {
                    type: String,    // list of issues
                },
            ],        
            highlighted_pdf: {
                type: String,        // annotated PDF download link
            },  
            raw: {
                type: Schema.Types.Mixed,   // raw full FastAPI result
            },              
        },
    },
    { 
        timestamps: true,
    }
);

const DPR = mongoose.model<IDPR>("DPR", dprSchema);
export default DPR;
