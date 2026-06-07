"use client";
import { useState, useRef, useEffect } from "react";
import { streamChat } from "@/lib/api";
import VoiceInput from "./VoiceInput";

type Message = { role: "user" | "assistant"; content: string };

// Animated 3-dot thinking indicator
function ThinkingDots() {
  return (
    <span className="inline-flex items-center gap-1 px-1">
      {[0, 1, 2].map((i) => (
        <span
          key={i}
          className="w-1.5 h-1.5 rounded-full bg-sky-400 animate-bounce"
          style={{ animationDelay: `${i * 0.15}s`, animationDuration: "0.8s" }}
        />
      ))}
    </span>
  );
}

export default function ChatStream({ sessionId }: { sessionId: string }) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);
  const [voiceProcessing, setVoiceProcessing] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const stop = () => {
    abortRef.current?.abort();
    setStreaming(false);
  };

  const send = async (text: string) => {
    if (!text.trim() || streaming) return;
    setMessages((prev) => [...prev, { role: "user", content: text }]);
    setInput("");
    setStreaming(true);

    // Empty assistant bubble — shows ThinkingDots until first token arrives
    setMessages((prev) => [...prev, { role: "assistant", content: "" }]);

    const ctrl = new AbortController();
    abortRef.current = ctrl;

    try {
      await streamChat(sessionId, text, (token) => {
        setMessages((prev) => {
          const updated = [...prev];
          updated[updated.length - 1] = {
            ...updated[updated.length - 1],
            content: updated[updated.length - 1].content + token,
          };
          return updated;
        });
      }, ctrl.signal);
    } catch (err: unknown) {
      if (err instanceof Error && err.name !== "AbortError") {
        setMessages((prev) => {
          const updated = [...prev];
          updated[updated.length - 1] = {
            ...updated[updated.length - 1],
            content: "Sorry, something went wrong. Please try again.",
          };
          return updated;
        });
      }
    } finally {
      setStreaming(false);
      abortRef.current = null;
    }
  };

  const suggestions = [
    "What is the most expensive item?",
    "How can I reduce the total cost?",
    "What if I used cheaper tiles?",
    "How does this compare to typical Georgian houses?",
  ];

  return (
    <div className="flex flex-col h-[600px]">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto space-y-4 mb-4 scrollbar-thin pr-1">
        {messages.length === 0 && (
          <div className="text-center py-8">
            <p className="text-slate-400 mb-4">Ask me anything about your cost estimate</p>
            <div className="flex flex-wrap gap-2 justify-center">
              {suggestions.map((s) => (
                <button
                  key={s}
                  onClick={() => send(s)}
                  className="text-xs bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-300 rounded-full px-3 py-1.5 transition-colors"
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((m, i) => {
          const isThinking =
            m.role === "assistant" && m.content === "" && streaming && i === messages.length - 1;
          return (
            <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
              <div
                className={`max-w-[80%] rounded-2xl px-4 py-3 text-sm leading-relaxed
                  ${m.role === "user"
                    ? "bg-sky-700 text-white"
                    : "bg-slate-800 text-slate-100 border border-slate-700"}`}
              >
                {isThinking ? <ThinkingDots /> : m.content}
              </div>
            </div>
          );
        })}
        <div ref={bottomRef} />
      </div>

      {/* Input row */}
      <div className="flex gap-2 items-center">
        <VoiceInput
          onTranscript={(t) => { setVoiceProcessing(false); setInput(t); }}
          onProcessingChange={setVoiceProcessing}
          disabled={streaming}
        />

        <div className="relative flex-1">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && send(input)}
            placeholder={voiceProcessing ? "" : "Ask about your estimate…"}
            disabled={streaming || voiceProcessing}
            className="w-full bg-slate-800 border border-slate-700 rounded-xl px-4 py-3 text-white text-sm placeholder:text-slate-500 focus:outline-none focus:border-sky-500 disabled:opacity-100"
          />
          {/* Blinking typing cursor shown while voice is being processed */}
          {voiceProcessing && (
            <span className="absolute left-4 top-1/2 -translate-y-1/2 text-sky-400 text-sm font-mono animate-pulse select-none pointer-events-none">
              |
            </span>
          )}
        </div>

        {streaming ? (
          <button
            onClick={stop}
            className="px-4 py-3 bg-red-600 hover:bg-red-500 text-white rounded-xl transition-colors text-sm font-medium flex items-center gap-1.5"
          >
            <span className="w-2.5 h-2.5 bg-white rounded-sm inline-block" />
            Stop
          </button>
        ) : (
          <button
            onClick={() => send(input)}
            disabled={!input.trim()}
            className="px-4 py-3 bg-sky-600 hover:bg-sky-500 disabled:bg-slate-700 disabled:text-slate-500 text-white rounded-xl transition-colors text-sm font-medium"
          >
            Send
          </button>
        )}
      </div>
    </div>
  );
}
