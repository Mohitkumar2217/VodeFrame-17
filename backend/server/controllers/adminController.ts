import { Request, Response } from "express";
import Admin from "../models/Admin";
import bcrypt from "bcryptjs";
import jwt from "jsonwebtoken";

interface AdminLoginBody {
    email: string;
    password: string;
}

export const adminLogin = async (
    req: Request<{}, {}, AdminLoginBody>,
    res: Response
): Promise<Response | void> => {
    try {
        const { email, password } = req.body;

        if (!email || !password) {
            return res.status(400).json({
                message: "Email and password are required.",
            });
        }

        const admin = await Admin.findOne({ email });

        if (!admin) {
            return res.status(404).json({
                message: "Admin not found",
            });
        }

        const valid = await bcrypt.compare(
            password,
            admin.password
        );

        if (!valid) {
            return res.status(400).json({
                message: "Invalid password",
            });
        }

        const token = jwt.sign(
            {
                id: admin._id,
                role: "admin",
            },
            process.env.JWT_SECRET as string,
            {
                expiresIn: "7d",
            }
        );

        return res.json({
            status: true,
            data: {
                token,
                user: admin,
            },
        });
    } catch (error) {
        console.error("Admin login error:", error);

        return res.status(500).json({
            message: "Server error",
        });
    }
};