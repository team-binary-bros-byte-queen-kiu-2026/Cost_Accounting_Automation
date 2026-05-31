const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// ── Store estimate in sessionStorage so the results page can read it ─────────
export function storeEstimate(sessionId: string, estimate: Record<string, unknown>) {
  if (typeof window !== "undefined") {
    sessionStorage.setItem(`estimate_${sessionId}`, JSON.stringify(estimate));
  }
}
export function getStoredEstimate(sessionId: string): Record<string, unknown> | null {
  if (typeof window === "undefined") return null;
  const raw = sessionStorage.getItem(`estimate_${sessionId}`);
  return raw ? JSON.parse(raw) : null;
}

// ── Analyze image → cost estimate ────────────────────────────────────────────
export async function analyzeImage(file: File): Promise<{ session_id: string; estimate: Record<string, unknown> }> {
  const form = new FormData();
  form.append("file", file);
  const resp = await fetch(`${API}/analyze`, { method: "POST", body: form });
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({}));
    throw new Error(err.detail || `Analysis failed (${resp.status})`);
  }
  const data = await resp.json();
  storeEstimate(data.session_id, data.estimate);
  return data;
}

// ── Streaming chat ────────────────────────────────────────────────────────────
export async function streamChat(
  sessionId: string,
  message: string,
  onToken: (token: string) => void
): Promise<void> {
  const resp = await fetch(`${API}/chat/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, message }),
  });
  if (!resp.ok || !resp.body) throw new Error(`Chat failed (${resp.status})`);

  const reader = resp.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() ?? "";
    for (const line of lines) {
      if (line.startsWith("data: ")) {
        const chunk = line.slice(6);
        if (chunk === "[DONE]") return;
        try {
          const data = JSON.parse(chunk);
          if (data.token) onToken(data.token);
        } catch { /* ignore malformed */ }
      }
    }
  }
}

// ── TTS: text → audio blob ────────────────────────────────────────────────────
export async function speakText(text: string, voice = "nova"): Promise<Blob> {
  const resp = await fetch(`${API}/speak`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, voice }),
  });
  if (!resp.ok) throw new Error(`TTS failed (${resp.status})`);
  return resp.blob();
}

// ── STT: audio blob → transcript ──────────────────────────────────────────────
export async function transcribeAudio(blob: Blob): Promise<string> {
  const form = new FormData();
  form.append("file", blob, "recording.webm");
  const resp = await fetch(`${API}/transcribe`, { method: "POST", body: form });
  if (!resp.ok) throw new Error(`Transcription failed (${resp.status})`);
  const data = await resp.json();
  return data.transcript || "";
}

// ── Admin: prices ─────────────────────────────────────────────────────────────
export async function getMaterials() {
  const resp = await fetch(`${API}/admin/materials`);
  return resp.json();
}
export async function getLabor() {
  const resp = await fetch(`${API}/admin/labor`);
  return resp.json();
}
export async function updateMaterialPrice(id: number, price: number) {
  return fetch(`${API}/admin/materials/${id}/price`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ price_gel: price }),
  });
}
export async function updateLaborPrice(id: number, price: number) {
  return fetch(`${API}/admin/labor/${id}/price`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ price_gel: price }),
  });
}
