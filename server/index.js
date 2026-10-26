import "dotenv/config";
import express from "express";
import cors from "cors";
import multer from "multer";

const PORT = process.env.PORT || 5000;
const RAG_URL = process.env.RAG_SERVICE_URL || "http://localhost:8000";
const CLIENT_ORIGIN = process.env.CLIENT_ORIGIN || "http://localhost:5173";

const ALLOWED_EXT = [".pdf", ".txt", ".md", ".docx"];
const MAX_MB = 25;

const app = express();
app.use(cors({ origin: CLIENT_ORIGIN }));
app.use(express.json({ limit: "1mb" }));

// Keep the upload in memory and forward it straight to the Python service
const upload = multer({
  storage: multer.memoryStorage(),
  limits: { fileSize: MAX_MB * 1024 * 1024 },
  fileFilter: (_req, file, cb) => {
    const name = file.originalname.toLowerCase();
    if (ALLOWED_EXT.some((ext) => name.endsWith(ext))) return cb(null, true);
    cb(new Error(`Unsupported file type. Allowed: ${ALLOWED_EXT.join(", ")}`));
  },
});

// Pass the FastAPI error message through to the client
async function relay(res, upstream) {
  const data = await upstream.json().catch(() => ({}));
  if (!upstream.ok) {
    return res
      .status(upstream.status)
      .json({ error: data.detail || "RAG service error" });
  }
  return res.json(data);
}

app.get("/api/health", async (_req, res) => {
  try {
    const r = await fetch(`${RAG_URL}/health`);
    res.json({ gateway: "ok", rag: await r.json() });
  } catch {
    res.status(502).json({ gateway: "ok", rag: "unreachable" });
  }
});

app.post("/api/upload", upload.single("file"), async (req, res) => {
  if (!req.file) return res.status(400).json({ error: "No file uploaded." });

  try {
    const form = new FormData();
    form.append(
      "file",
      new Blob([req.file.buffer], { type: req.file.mimetype }),
      req.file.originalname
    );
    const upstream = await fetch(`${RAG_URL}/upload`, {
      method: "POST",
      body: form,
    });
    await relay(res, upstream);
  } catch (err) {
    console.error("Upload failed:", err.message);
    res.status(502).json({ error: "Could not reach the RAG service." });
  }
});

app.post("/api/ask", async (req, res) => {
  const { docId, question } = req.body || {};
  if (!docId || !question?.trim()) {
    return res.status(400).json({ error: "docId and question are required." });
  }

  try {
    const upstream = await fetch(`${RAG_URL}/ask`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ doc_id: docId, question: question.trim() }),
    });
    await relay(res, upstream);
  } catch (err) {
    console.error("Ask failed:", err.message);
    res.status(502).json({ error: "Could not reach the RAG service." });
  }
});

app.delete("/api/document/:docId", async (req, res) => {
  try {
    const upstream = await fetch(`${RAG_URL}/document/${req.params.docId}`, {
      method: "DELETE",
    });
    await relay(res, upstream);
  } catch {
    res.status(502).json({ error: "Could not reach the RAG service." });
  }
});

// Multer / generic error handler
app.use((err, _req, res, _next) => {
  const status = err.code === "LIMIT_FILE_SIZE" ? 413 : 400;
  res.status(status).json({
    error:
      err.code === "LIMIT_FILE_SIZE"
        ? `File larger than ${MAX_MB} MB.`
        : err.message,
  });
});

app.listen(PORT, () => console.log(`Gateway running on http://localhost:${PORT}`));
