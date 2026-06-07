"use client";
import { useState, useRef } from "react";

// Animated sound-wave bars shown while listening / processing
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

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type Any = any;

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
  const recRef = useRef<Any>(null);
  const resultReceivedRef = useRef(false);

  const setProc = (val: boolean) => {
    setProcessing(val);
    onProcessingChange?.(val);
  };

  const toggle = () => {
    if (listening || processing) {
      recRef.current?.stop();
      setListening(false);
      setProc(false);
      return;
    }

    const W = window as Any;
    const SpeechRec = W.SpeechRecognition || W.webkitSpeechRecognition;
    if (!SpeechRec) {
      alert("Voice input requires Chrome or Edge.");
      return;
    }

    const rec = new SpeechRec();
    rec.lang = "en-US";
    rec.continuous = false;
    rec.interimResults = false;
    rec.maxAlternatives = 1;

    resultReceivedRef.current = false;

    // Result arrives → clear processing, pass text up
    rec.onresult = (e: Any) => {
      resultReceivedRef.current = true;
      setProc(false);
      const text: string = e.results[0]?.[0]?.transcript ?? "";
      if (text) onTranscript(text);
    };

    // Speech ended — switch from wave to processing dots
    rec.onspeechend = () => {
      setListening(false);
      if (!resultReceivedRef.current) setProc(true);
    };

    rec.onend = () => {
      setListening(false);
      if (resultReceivedRef.current) setProc(false);
    };

    rec.onerror = () => {
      setListening(false);
      setProc(false);
    };

    recRef.current = rec;
    rec.start();
    setListening(true);
  };

  const active = listening || processing;

  return (
    <button
      type="button"
      onClick={toggle}
      disabled={disabled && !active}
      title={
        processing ? "Processing…"
        : listening ? "Click to stop"
        : "Click to speak"
      }
      className={`p-3 rounded-xl transition-all select-none min-w-[46px] flex items-center justify-center
        ${active
          ? "bg-red-600 text-white scale-105 ring-2 ring-red-400 ring-offset-1 ring-offset-slate-900"
          : "bg-slate-800 hover:bg-slate-700 text-slate-400 border border-slate-700"}
        ${disabled && !active ? "opacity-50 cursor-not-allowed" : ""}`}
    >
      {processing ? (
        // 3 bouncing dots while waiting for transcript
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
