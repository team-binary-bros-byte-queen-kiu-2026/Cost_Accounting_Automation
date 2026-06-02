"use client";
import { useState, useRef } from "react";
import { useRouter } from "next/navigation";
import { analyzeImage } from "@/lib/api";

export default function HomePage() {
  const router = useRouter();
  const fileRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);
  const [preview, setPreview] = useState<string | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFile = (f: File) => {
    if (!f.type.startsWith("image/")) {
      setError("Please upload a JPEG, PNG, or WebP image.");
      return;
    }
    setFile(f);
    setError(null);
    const reader = new FileReader();
    reader.onload = (e) => setPreview(e.target?.result as string);
    reader.readAsDataURL(f);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    const f = e.dataTransfer.files[0];
    if (f) handleFile(f);
  };

  const handleSubmit = async () => {
    if (!file) return;
    setLoading(true);
    setError(null);
    try {
      const result = await analyzeImage(file);
      router.push(`/estimate/${result.session_id}`);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Analysis failed. Please try again.");
      setLoading(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto px-4 py-16">
      {/* Hero */}
      <div className="text-center mb-12">
        <h1 className="text-4xl font-bold text-white mb-4">
          Construction Cost Estimator
        </h1>
        <p className="text-slate-400 text-lg max-w-xl mx-auto">
          Upload a photo of your building project. Our AI identifies the components
          and computes a detailed cost estimate using Georgian market prices.
        </p>
      </div>

      {/* Upload zone */}
      <div
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={handleDrop}
        onClick={() => fileRef.current?.click()}
        className={`relative border-2 border-dashed rounded-2xl p-8 text-center cursor-pointer transition-all
          ${dragging ? "border-sky-400 bg-sky-950/30" : "border-slate-700 hover:border-slate-500 bg-slate-900/50"}`}
      >
        <input
          ref={fileRef}
          type="file"
          accept="image/jpeg,image/png,image/webp"
          className="hidden"
          onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])}
        />

        {preview ? (
          <div className="space-y-4">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={preview}
              alt="Building preview"
              className="max-h-64 mx-auto rounded-xl object-contain"
            />
            <p className="text-slate-400 text-sm">{file?.name} · Click to change</p>
          </div>
        ) : (
          <div className="space-y-3">
            <div className="text-5xl">📷</div>
            <p className="text-white font-medium">Drag & drop your building photo here</p>
            <p className="text-slate-500 text-sm">or click to browse · JPEG, PNG, WebP · max 10MB</p>
          </div>
        )}
      </div>

      {error && (
        <div className="mt-4 p-3 bg-red-900/40 border border-red-700 rounded-lg text-red-300 text-sm">
          {error}
        </div>
      )}

      <button
        onClick={handleSubmit}
        disabled={!file || loading}
        className="mt-6 w-full py-4 rounded-xl font-semibold text-white text-lg
          bg-sky-600 hover:bg-sky-500 disabled:bg-slate-700 disabled:text-slate-500
          transition-colors flex items-center justify-center gap-2"
      >
        {loading ? (
          <>
            <span className="animate-spin">⟳</span>
            Analyzing with AI…
          </>
        ) : (
          "Estimate Cost →"
        )}
      </button>

      {/* Feature pills */}
      <div className="mt-12 grid grid-cols-3 gap-4 text-center text-sm">
        {[
          { icon: "🔍", title: "Vision AI", desc: "Identifies components from photo" },
          { icon: "💰", title: "Market Prices", desc: "Georgian construction rates 2025" },
          { icon: "💬", title: "AI Chat", desc: "Ask follow-up questions" },
        ].map((f) => (
          <div key={f.title} className="bg-slate-900 rounded-xl p-4 border border-slate-800">
            <div className="text-2xl mb-2">{f.icon}</div>
            <div className="font-medium text-white">{f.title}</div>
            <div className="text-slate-400 text-xs mt-1">{f.desc}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
