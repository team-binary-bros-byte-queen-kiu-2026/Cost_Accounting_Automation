"use client";
import { useState, useRef } from "react";

export default function VoiceInput({
  onTranscript,
  disabled = false,
}: {
  onTranscript: (text: string) => void;
  disabled?: boolean;
}) {
  const [listening, setListening] = useState(false);
  const recognizerRef = useRef<SpeechRecognition | null>(null);

  const toggle = () => {
    if (listening) {
      recognizerRef.current?.stop();
      setListening(false);
      return;
    }

    // Browser Web Speech API — works in Chrome/Edge/Safari natively, no API key needed
    const SpeechRec =
      (window as unknown as { SpeechRecognition?: typeof SpeechRecognition; webkitSpeechRecognition?: typeof SpeechRecognition })
        .SpeechRecognition ||
      (window as unknown as { webkitSpeechRecognition?: typeof SpeechRecognition })
        .webkitSpeechRecognition;

    if (!SpeechRec) {
      alert("Speech recognition is not supported in this browser. Please use Chrome.");
      return;
    }

    const rec = new SpeechRec();
    rec.lang = "ka-GE,en-US"; // Georgian first, English fallback
    rec.interimResults = false;
    rec.maxAlternatives = 1;

    rec.onresult = (e: SpeechRecognitionEvent) => {
      const transcript = e.results[0]?.[0]?.transcript ?? "";
      if (transcript) onTranscript(transcript);
    };

    rec.onerror = () => setListening(false);
    rec.onend = () => setListening(false);

    recognizerRef.current = rec;
    rec.start();
    setListening(true);
  };

  return (
    <button
      type="button"
      onClick={toggle}
      disabled={disabled}
      title={listening ? "Click to stop" : "Click to speak"}
      className={`p-3 rounded-xl text-lg transition-all
        ${listening
          ? "bg-red-600 text-white scale-110 ring-2 ring-red-400 ring-offset-1 ring-offset-slate-900"
          : "bg-slate-800 hover:bg-slate-700 text-slate-400 border border-slate-700"}
        disabled:opacity-50`}
    >
      {listening ? "🔴" : "🎤"}
    </button>
  );
}
