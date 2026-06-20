import { Request, Response } from "express";
import User from "../models/User";
import Admin from "../models/Admin";
import bcrypt from "bcryptjs";
import jwt from "jsonwebtoken";

interface LoginBody {
    email: string;
    password: string;
}

export const login = async (
    req: Request<{}, {}, LoginBody>,
    res: Response
): Promise<Response | void> => {
    const { email, password } = req.body;

    if (!email || !password) {
        return res.status(400).json({
            message: "Email and password required.",
        });
    }

    try {
        // Try User
        let account = await User.findOne({ email });

        // Try Admin
        if (!account) {
            account = await Admin.findOne({ username: email });
        }

        if (!account) {
            return res.status(404).json({
                message: "Account not found.",
            });
        }

        const valid = await bcrypt.compare(
            password,
            account.password
        );

        if (!valid) {
            return res.status(400).json({
                message: "Invalid password.",
            });
        }

        const token = jwt.sign(
            {
                id: account._id,
                role: account.role,
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
                user: account,
            },
        });
    } catch (err) {
        console.error("Login error:", err);

        return res.status(500).json({
            message: "Server error.",
        });
    }
};