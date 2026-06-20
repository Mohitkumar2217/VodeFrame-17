import mongoose from "mongoose";

export interface IAdmin {
    username: string;
    password: string;
    role: string;
}
const adminSchema = new mongoose.Schema({
    username: {
        type: String,
        unique: true
    },
    password: {
        type: String,
        required: true,
    },
    role: {
        type: String,
        default: "admin"
    }
}, {
    timestamps: true
});

const Admin = mongoose.model<IAdmin>("Admin", adminSchema);
export default Admin;
