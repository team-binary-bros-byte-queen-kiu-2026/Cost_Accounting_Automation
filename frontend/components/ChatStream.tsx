"use client";
import { useState, useRef, useEffect } from "react";
import { streamChat } from "@/lib/api";
import VoiceInput from "./VoiceInput";

type Message = { role: "user" | "assistant"; content: string };

export default function ChatStream({ sessionId }: { sessionId: string }) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const send = async (text: string) => {
    if (!text.trim() || streaming) return;
    const userMsg: Message = { role: "user", content: text };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setStreaming(true);

    const assistantMsg: Message = { role: "assistant", content: "" };
    setMessages((prev) => [...prev, assistantMsg]);

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
      });
    } finally {
      setStreaming(false);
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
        {messages.map((m, i) => (
          <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
            <div className={`max-w-[80%] rounded-2xl px-4 py-3 text-sm leading-relaxed
              ${m.role === "user"
                ? "bg-sky-700 text-white"
                : "bg-slate-800 text-slate-100 border border-slate-700"}`}
            >
              {m.content || (streaming && m.role === "assistant" ? <span className="animate-pulse">▌</span> : "")}
            </div>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>

      {/* Input row */}
      <div className="flex gap-2 items-center">
        <VoiceInput onTranscript={(t) => setInput(t)} disabled={streaming} />
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && send(input)}
          placeholder="Ask about your estimate…"
          disabled={streaming}
          className="flex-1 bg-slate-800 border border-slate-700 rounded-xl px-4 py-3 text-white text-sm placeholder:text-slate-500 focus:outline-none focus:border-sky-500 disabled:opacity-50"
        />
        <button
          onClick={() => send(input)}
          disabled={!input.trim() || streaming}
          className="px-4 py-3 bg-sky-600 hover:bg-sky-500 disabled:bg-slate-700 disabled:text-slate-500 text-white rounded-xl transition-colors text-sm font-medium"
        >
          Send
        </button>
      </div>
    </div>
  );
}
