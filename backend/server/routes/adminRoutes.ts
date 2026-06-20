import express, { Request, Response } from "express";
import { auth, adminOnly } from "../middleware/authMiddleware";

interface AuthRequest extends Request {
    user?: any;
}

const router = express.Router();

router.get(
    "/dashboard",
    auth,
    adminOnly,
    (req: AuthRequest, res: Response) => {
        res.json({
            message: "Welcome Admin",
            user: req.user,
        });
    }
);

export default router;