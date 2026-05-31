"use client";
import { useState, useRef } from "react";
import { transcribeAudio } from "@/lib/api";

export default function VoiceInput({
  onTranscript,
  disabled = false,
}: {
  onTranscript: (text: string) => void;
  disabled?: boolean;
}) {
  const [recording, setRecording] = useState(false);
  const [processing, setProcessing] = useState(false);
  const mediaRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      chunksRef.current = [];
      recorder.ondataavailable = (e) => chunksRef.current.push(e.data);
      recorder.onstop = async () => {
        stream.getTracks().forEach((t) => t.stop());
        const blob = new Blob(chunksRef.current, { type: "audio/webm" });
        setProcessing(true);
        try {
          const text = await transcribeAudio(blob);
          onTranscript(text);
        } finally {
          setProcessing(false);
        }
      };
      mediaRef.current = recorder;
      recorder.start();
      setRecording(true);
    } catch {
      alert("Microphone access denied. Please allow microphone access to use voice input.");
    }
  };

  const stopRecording = () => {
    mediaRef.current?.stop();
    setRecording(false);
  };

  if (processing) {
    return (
      <button disabled className="p-3 rounded-xl bg-slate-700 text-slate-400 text-lg">
        <span className="animate-spin inline-block">⟳</span>
      </button>
    );
  }

  return (
    <button
      onMouseDown={startRecording}
      onMouseUp={stopRecording}
      onTouchStart={startRecording}
      onTouchEnd={stopRecording}
      disabled={disabled}
      title="Hold to speak"
      className={`p-3 rounded-xl text-lg transition-colors
        ${recording ? "bg-red-600 text-white animate-pulse" : "bg-slate-800 hover:bg-slate-700 text-slate-400 border border-slate-700"}
        disabled:opacity-50`}
    >
      🎤
    </button>
  );
}
