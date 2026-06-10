"use client";
import { useState, useRef } from "react";
import { transcribeAudio } from "@/lib/api";

function SoundWave() {
  return (
    <span className="flex items-end gap-[3px] h-5 w-6">
      {[0, 1, 2].map((i) => (
        <span
          key={i}
          className="w-[4px] rounded-full bg-white animate-bounce"
          style={{
            animationDelay: `${i * 0.12}s`,
            animationDuration: "0.7s",
            height: i === 1 ? "100%" : "55%",
          }}
        />
      ))}
    </span>
  );
}

export default function VoiceInput({
  onTranscript,
  onProcessingChange,
  disabled = false,
}: {
  onTranscript: (text: string) => void;
  onProcessingChange?: (processing: boolean) => void;
  disabled?: boolean;
}) {
  const [listening, setListening] = useState(false);
  const [processing, setProcessing] = useState(false);
  const mediaRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const streamRef = useRef<MediaStream | null>(null);

  const setProc = (val: boolean) => {
    setProcessing(val);
    onProcessingChange?.(val);
  };

  const stopStream = () => {
    streamRef.current?.getTracks().forEach((track) => track.stop());
    streamRef.current = null;
  };

  const toggle = async () => {
    if (processing) return;

    if (listening) {
      mediaRef.current?.stop();
      return;
    }

    if (!navigator.mediaDevices?.getUserMedia) {
      alert("Voice input is not supported in this browser.");
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      chunksRef.current = [];

      const mimeType = MediaRecorder.isTypeSupported("audio/webm;codecs=opus")
        ? "audio/webm;codecs=opus"
        : MediaRecorder.isTypeSupported("audio/webm")
          ? "audio/webm"
          : "audio/mp4";

      const recorder = new MediaRecorder(stream, { mimeType });
      mediaRef.current = recorder;

      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) chunksRef.current.push(event.data);
      };

      recorder.onstop = async () => {
        setListening(false);
        stopStream();

        const blob = new Blob(chunksRef.current, { type: mimeType });
        if (blob.size < 500) {
          alert("Recording too short. Click the mic, speak, then click again to stop.");
          return;
        }

        setProc(true);
        try {
          const text = await transcribeAudio(blob);
          if (text.trim()) {
            onTranscript(text.trim());
          } else {
            alert("No speech detected. Please try again.");
          }
        } catch (err) {
          const msg = err instanceof Error ? err.message : "Transcription failed.";
          alert(msg);
        } finally {
          setProc(false);
        }
      };

      recorder.onerror = () => {
        setListening(false);
        setProc(false);
        stopStream();
        alert("Recording failed. Please try again.");
      };

      recorder.start();
      setListening(true);
    } catch {
      alert("Microphone access denied. Allow microphone permission for this site in browser settings.");
    }
  };

  const active = listening || processing;

  return (
    <button
      type="button"
      onClick={toggle}
      disabled={disabled && !active}
      title={
        processing
          ? "Transcribing…"
          : listening
            ? "Click to stop recording"
            : "Click to record a question"
      }
      className={`p-3 rounded-xl transition-all select-none min-w-[46px] flex items-center justify-center
        ${active
          ? "bg-red-600 text-white scale-105 ring-2 ring-red-400 ring-offset-1 ring-offset-slate-900"
          : "bg-slate-800 hover:bg-slate-700 text-slate-400 border border-slate-700"}
        ${disabled && !active ? "opacity-50 cursor-not-allowed" : ""}`}
    >
      {processing ? (
        <span className="flex items-center gap-[3px] h-5">
          {[0, 1, 2].map((i) => (
            <span
              key={i}
              className="w-1.5 h-1.5 rounded-full bg-white animate-bounce"
              style={{ animationDelay: `${i * 0.15}s`, animationDuration: "0.8s" }}
            />
          ))}
        </span>
      ) : listening ? (
        <SoundWave />
      ) : (
        <span className="text-lg">🎤</span>
      )}
    </button>
  );
}
