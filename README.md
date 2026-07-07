# 🚀 VodeFrame 17 – DPR Quality Assessment System

A modern AI-powered **Document Processing and Review (DPR) Quality Assessment System** designed to automate document evaluation, streamline quality assurance workflows, and provide intelligent insights through machine learning and secure role-based authentication.

**🌐 Live Demo:** https://vode-frame-17.vercel.app/

---

## 📖 Overview

VodeFrame 17 is a full-stack web application that enables organizations to upload, analyze, and assess DPR documents using AI-powered evaluation pipelines. The platform combines modern web technologies with secure authentication and scalable serverless architecture to simplify document quality management.

---

## ✨ Features

### 🔐 Authentication & Authorization

* Secure JWT Authentication
* Role-Based Access Control (Admin, Manager, Staff)
* Password Hashing using bcrypt
* HTTP-only Cookie Authentication
* Forgot Password
* Password Reset via Email
* Session Management

---

### 📄 Document Management

* Upload DPR Documents
* AI-based Document Assessment
* Quality Score Generation
* Document Status Tracking
* Search & Filter Documents
* Real-time Processing Status

---

### 🤖 AI Features

* Automated DPR Quality Evaluation
* Intelligent Document Analysis
* AI-powered Scoring Pipeline
* Python-based Processing Engine
* Rule-based Validation
* Machine Learning Assisted Review

---

### 📊 Dashboard

* Interactive Dashboard
* Document Statistics
* User Activity
* Quality Metrics
* Processing Overview
* Performance Insights

---

### 👥 User Management

* User Registration
* User Login
* Profile Management
* Role Management
* Access Permissions

---

## 🛠 Tech Stack

### Frontend

* Next.js
* React.js
* TypeScript
* Tailwind CSS
* Axios

### Backend

* Next.js API Routes
* Node.js
* JWT Authentication
* bcrypt
* Serverless Functions

### AI & Processing

* Python
* Machine Learning Pipeline

### Database

* MongoDB

### Deployment

* Vercel

---

## 📁 Project Structure

```text
.
├── app/
├── components/
├── context/
├── hooks/
├── lib/
├── public/
├── styles/
├── middleware/
├── api/
├── python/
├── utils/
├── package.json
└── README.md
```

---

## 🚀 Getting Started

### Clone Repository

```bash
git clone https://github.com/Mohitkumar2217/VodeFrame-17.git
```

```bash
cd VodeFrame-17
```

---

### Install Dependencies

```bash
npm install
```

---

### Configure Environment Variables

Create a `.env.local` file.

```env
MONGODB_URI=

JWT_SECRET=

EMAIL_USER=

EMAIL_PASS=

NEXT_PUBLIC_API_URL=

PYTHON_API_URL=
```

---

### Run Development Server

```bash
npm run dev
```

Open

```
http://localhost:3000
```

---

## 🔒 Authentication Flow

```text
User Login
      │
      ▼
Credential Verification
      │
      ▼
JWT Generation
      │
      ▼
HTTP-only Cookie
      │
      ▼
Protected Routes
      │
      ▼
Role Verification
      │
      ▼
Dashboard Access
```

---

## 📌 Core Modules

* Authentication
* Authorization
* Dashboard
* DPR Upload
* AI Processing
* Quality Assessment
* User Management
* Reports
* Profile Management

---

## 📈 Highlights

* Secure Authentication
* AI-assisted Document Evaluation
* Responsive UI
* Serverless Deployment
* Modern React Architecture
* RESTful APIs
* Scalable Codebase
* Clean Component Structure

---

## 📦 Installation

```bash
npm install
```

Development

```bash
npm run dev
```

Production

```bash
npm run build

npm start
```

---

## 🌍 Live Demo

https://vode-frame-17.vercel.app/

---

## 📂 Repository

https://github.com/Mohitkumar2217/VodeFrame-17

---

## 🔮 Future Enhancements

* OCR Integration
* PDF Annotation
* Team Collaboration
* Audit Logs
* Analytics Dashboard
* Notification System
* Cloud Storage Integration
* AI Model Improvements

---

## 👨‍💻 Author

**Mohit Kumawat**

* GitHub: https://github.com/Mohitkumar2217
* LinkedIn: https://www.linkedin.com/in/mohit-kumawat-889202374/

---

## 📄 License

This project is licensed under the MIT License.
