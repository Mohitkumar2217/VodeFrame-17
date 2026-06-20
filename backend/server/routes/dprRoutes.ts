import express from "express";
import { auth } from "../middleware/authMiddleware";
import upload from "../middleware/upload";
import {
    uploadDPR,
    getAllDPRs,
    getMyDPRs
} from "../controllers/dprController";

const router = express.Router();


// Upload DPR
router.post("/upload", auth, upload.single("file"), uploadDPR);

// Admin → Get all DPRs
router.get("/all", auth, getAllDPRs);

// Client → Get only client DPRs


export default router;