import { Request, Response, NextFunction } from "express";
import jwt, { JwtPayload } from "jsonwebtoken";

interface AuthRequest extends Request {
    user?: string | JwtPayload;
}

interface CustomJwtPayload extends JwtPayload {
    id: string;
    role: string;
}

export const auth = (
    req: AuthRequest,
    res: Response,
    next: NextFunction
): Response | void => {
    const token = req.headers.authorization?.split(" ")[1];

    if (!token) {
        return res.status(401).json({
            message: "No token",
        });
    }

    try {
        const decoded = jwt.verify(
            token,
            process.env.JWT_SECRET as string
        ) as CustomJwtPayload;

        req.user = decoded;

        next();
    } catch (err) {
        return res.status(401).json({
            message: "Invalid token",
        });
    }
};

export const adminOnly = (
    req: AuthRequest,
    res: Response,
    next: NextFunction
): Response | void => {
    const user = req.user as CustomJwtPayload;

    if (user.role !== "admin") {
        return res.status(403).json({
            message: "Admins only",
        });
    }

    next();
};