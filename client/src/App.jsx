import { useRef, useState } from "react";
import { askQuestion, uploadDocument } from "./api";

export default function App() {
  const fileInput = useRef(null);
  const [file, setFile] = useState(null);
  const [doc, setDoc] = useState(null); // { doc_id, filename, chunks }
  const [question, setQuestion] = useState("");
  const [result, setResult] = useState(null); // { answer, sources }
  const [uploading, setUploading] = useState(false);
  const [asking, setAsking] = useState(false);
  const [error, setError] = useState("");

  const pickFile = (e) => {
    setFile(e.target.files[0] || null);
    setDoc(null);
    setResult(null);
    setError("");
  };

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    setError("");
    try {
      setDoc(await uploadDocument(file));
    } catch (e) {
      setError(e.message);
    } finally {
      setUploading(false);
    }
  };

  const handleAsk = async (e) => {
    e.preventDefault();
    if (!doc || !question.trim()) return;
    setAsking(true);
    setError("");
    setResult(null);
    try {
      setResult(await askQuestion(doc.doc_id, question));
    } catch (e) {
      setError(e.message);
    } finally {
      setAsking(false);
    }
  };

  const reset = () => {
    setFile(null);
    setDoc(null);
    setResult(null);
    setQuestion("");
    setError("");
    if (fileInput.current) fileInput.current.value = "";
  };

  return (
    <div className="page">
      <header>
        <h1>📚 AI Student Assistant</h1>
        <p>Upload your notes or textbook, then ask questions. Answers come only from your document.</p>
      </header>

      <section className="card">
        <h2>1. Upload a document</h2>
        <div className="row">
          <input
            ref={fileInput}
            type="file"
            accept=".pdf,.txt,.md,.docx"
            onChange={pickFile}
          />
          <button onClick={handleUpload} disabled={!file || uploading || !!doc}>
            {uploading ? "Processing…" : "Upload"}
          </button>
          {doc && (
            <button className="ghost" onClick={reset}>
              New document
            </button>
          )}
        </div>
        {uploading && <p className="hint">Reading, chunking and embedding your document. This can take a little while for large files.</p>}
        {doc && (
          <p className="ok">
            ✅ <strong>{doc.filename}</strong> is ready ({doc.chunks} chunks indexed)
          </p>
        )}
      </section>

      <section className={`card ${!doc ? "disabled" : ""}`}>
        <h2>2. Ask a question</h2>
        <form onSubmit={handleAsk}>
          <textarea
            rows={3}
            placeholder="e.g. What is the difference between TCP and UDP?"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            disabled={!doc || asking}
          />
          <button type="submit" disabled={!doc || asking || !question.trim()}>
            {asking ? "Thinking…" : "Submit"}
          </button>
        </form>
      </section>

      {error && <div className="error">⚠️ {error}</div>}

      {result && (
        <section className="card">
          <h2>Answer</h2>
          <div className="answer">{result.answer}</div>

          {result.sources.length > 0 && (
            <details>
              <summary>Sources from your document ({result.sources.length})</summary>
              {result.sources.map((s, i) => (
                <div className="source" key={i}>
                  <div className="meta">
                    {s.page} · relevance {Math.round(s.score * 100)}%
                  </div>
                  <p>{s.snippet}…</p>
                </div>
              ))}
            </details>
          )}
        </section>
      )}
    </div>
  );
}
