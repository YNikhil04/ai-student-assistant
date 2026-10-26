async function parse(res) {
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || `Request failed (${res.status})`);
  return data;
}

export async function uploadDocument(file) {
  const form = new FormData();
  form.append("file", file);
  return parse(await fetch("/api/upload", { method: "POST", body: form }));
}

export async function askQuestion(docId, question) {
  return parse(
    await fetch("/api/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ docId, question }),
    })
  );
}
