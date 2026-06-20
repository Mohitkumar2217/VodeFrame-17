import dotenv from "dotenv";
// import path from "path";
// import { fileURLToPath } from "url";

// const __filename = fileURLToPath(import.meta.url);
// const __dirname = path.dirname(__filename);

dotenv.config();

import express, {
    Application,
} from "express";

import cors from "cors";
import connectDB from "./config/db";
import authRoutes from "./routes/authRoutes";
import adminRoutes from "./routes/adminRoutes";
import dprRoutes from "./routes/dprRoutes";

const PORT: number = Number(
    process.env.PORT
) || 4000;
connectDB();

const app: Application = express();

app.use(
  cors({
    origin: true,
    credentials: true,
  })
);

// app.use(
//     cors({
//         origin: [
//             "http://localhost:3000",
//             "http://192.168.137.248:3000",
//         ],
//         credentials: true,
//     })
// );

app.use(express.json());

app.use("/api/auth", authRoutes);
app.use("/api/admin", adminRoutes);
app.use("/api/dpr", dprRoutes);

app.listen(PORT, () => {
    console.log(
        `Server running on http://localhost:${PORT}`
    );
});