"use client";
import { useState, useRef } from "react";

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type AnySpeechRecognition = any;

export default function VoiceInput({
  onTranscript,
  disabled = false,
}: {
  onTranscript: (text: string) => void;
  disabled?: boolean;
}) {
  const [listening, setListening] = useState(false);
  const recRef = useRef<AnySpeechRecognition>(null);

  const toggle = () => {
    if (listening) {
      recRef.current?.stop();
      setListening(false);
      return;
    }

    // Use browser Web Speech API — Chrome, Edge, Safari all support it on localhost
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const W = window as any;
    const SpeechRec = W.SpeechRecognition || W.webkitSpeechRecognition;

    if (!SpeechRec) {
      alert("Voice input requires Chrome or Edge. Firefox does not support Web Speech API.");
      return;
    }

    const rec = new SpeechRec();
    rec.lang = "en-US";          // single valid BCP-47 tag
    rec.continuous = false;
    rec.interimResults = false;
    rec.maxAlternatives = 1;

    rec.onresult = (e: { results: { [k: number]: { [k: number]: { transcript: string } } } }) => {
      const text = e.results[0]?.[0]?.transcript ?? "";
      if (text) onTranscript(text);
    };

    rec.onerror = () => {
      setListening(false);
    };

    rec.onend = () => {
      setListening(false);
    };

    recRef.current = rec;
    rec.start();
    setListening(true);
  };

  return (
    <button
      type="button"
      onClick={toggle}
      disabled={disabled}
      title={listening ? "Click to stop recording" : "Click to speak"}
      className={`p-3 rounded-xl text-lg transition-all select-none
        ${listening
          ? "bg-red-600 text-white scale-110 ring-2 ring-red-400 ring-offset-1 ring-offset-slate-900 animate-pulse"
          : "bg-slate-800 hover:bg-slate-700 text-slate-400 border border-slate-700"}
        disabled:opacity-50`}
    >
      {listening ? "🔴" : "🎤"}
    </button>
  );
}
