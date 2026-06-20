import { v2 as cloudinary } from "cloudinary";
import dotenv from "dotenv";
// import path from "path";
// import { fileURLToPath } from "url";
 
// const __filename = fileURLToPath(import.meta.url);

// const __dirname = path.dirname(__filename);
 
dotenv.config();
 
cloudinary.config({
    cloud_name: process.env.CLOUDINARY_CLOUD_NAME as string,

    api_key: process.env.CLOUDINARY_API_KEY as string,

    api_secret: process.env.CLOUDINARY_API_SECRET as string,

    secure: true,
});

export default cloudinary;