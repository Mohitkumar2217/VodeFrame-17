import { Request, Response } from "express"; 
import DPR from "../models/DPR";
import cloudinary from "../config/cloudinary";

interface CloudinaryUploadResult {
    secure_url: string;
    public_id: string;
}

interface DPRBody {
    title?: string;
    risk?: string;
    completeness?: string;
    analysis?: string;
}
 
const uploadToCloudinary = (
    buffer: Buffer
): Promise<CloudinaryUploadResult> => {
    return new Promise((resolve, reject) => {
        const stream = cloudinary.uploader.upload_stream(
            {
                folder: "dpr",
                resource_type: "raw",
            },
            (error, result) => {
                if (error) {
                    reject(error);
                } else if (result) {
                    resolve(result as CloudinaryUploadResult);
                }
            }
        );

        stream.end(buffer);
    });
};
 
export const uploadDPR = async (
    req: Request<{}, {}, DPRBody>,
    res: Response
): Promise<Response | void> => {
    try {
        if (!req.file) {
            return res.status(400).json({
                status: false,
                message: "No file uploaded",
            });
        }

        const {
            title,
            risk,
            completeness,
            analysis,
        } = req.body;
 
        const pdf = await uploadToCloudinary(
            req.file.buffer
        );
 
        let parsed: any = {};

        try {
            parsed =
                typeof analysis === "string"
                    ? JSON.parse(analysis)
                    : analysis;
        } catch (err) {
            console.log(
                "❌ ANALYSIS JSON PARSE ERROR:",
                err
            );

            parsed = {};
        }

        const evaluation =
            parsed?.evaluation || "";

        const issues =
            parsed?.issues || [];

        const highlighted_pdf =
            parsed?.highlighted_pdf || null;
 
        const dpr = await DPR.create({
            title:
                title || req.file.originalname,

            description:
                "AI evaluated DPR document",

            fileUrl: pdf.secure_url,

            publicId: pdf.public_id,

            risk: Number(risk || 0),

            completeness: Number(
                completeness || 0
            ),

            uploadedBy: "client",

            evaluationData: {
                evaluation,
                issues,
                highlighted_pdf,
                raw: parsed,
            },
        });

        return res.json({
            status: true,
            message:
                "DPR uploaded successfully",
            data: dpr,
        });
    } catch (err: any) {
        console.error(
            "❌ DPR UPLOAD ERROR:",
            err
        );

        return res.status(500).json({
            status: false,
            message: "Internal server error",
            error: err.message,
        });
    }
};
 
export const getAllDPRs = async (
    req: Request,
    res: Response
): Promise<Response | void> => {
    try {
        const dprs = await DPR.find().sort({
            createdAt: -1,
        });

        return res.json({
            status: true,
            data: dprs,
        });
    } catch {
        return res.status(500).json({
            status: false,
            message: "Server error",
        });
    }
};
 
export const getMyDPRs = async (
    req: Request,
    res: Response
): Promise<Response | void> => {
    try {
        const dprs = await DPR.find().sort({
            createdAt: -1,
        });

        return res.json({
            status: true,
            data: dprs,
        });
    } catch {
        return res.status(500).json({
            status: false,
            message: "Server error",
        });
    }
};