"use client";
import { useState } from "react";

type LineItem = {
  name: string; category: string; quantity: number; unit: string;
  unit_price_gel: number | null; subtotal_gel: number; confidence: string;
  notes: string; matched_item: string | null;
};

export default function CostBreakdown({
  estimate,
  sessionId,
}: {
  estimate: Record<string, unknown>;
  sessionId: string;
}) {
  const [speaking, setSpeaking] = useState(false);
  const items = (estimate.line_items as LineItem[]) || [];
  const byCategory = items.reduce<Record<string, LineItem[]>>((acc, item) => {
    const cat = item.category || "other";
    (acc[cat] ??= []).push(item);
    return acc;
  }, {});

  const confidenceColor = (c: string) => ({
    high: "text-emerald-400", medium: "text-amber-400", low: "text-red-400",
  }[c] ?? "text-slate-400");

  const handleSpeak = () => {
    if (speaking) {
      window.speechSynthesis.cancel();
      setSpeaking(false);
      return;
    }
    const total = (estimate.grand_total_gel as number).toLocaleString();
    const materials = (estimate.materials_total_gel as number).toLocaleString();
    const labor = (estimate.labor_estimate_gel as number).toLocaleString();
    const text =
      `Construction cost estimate. Total: ${total} Georgian Lari. ` +
      `Materials: ${materials} GEL. Labor: ${labor} GEL. ` +
      `${items.length} components identified. ` +
      `Confidence: ${estimate.confidence}. ` +
      `${estimate.notes ?? ""}`;

    const utt = new SpeechSynthesisUtterance(text);
    utt.lang = "en-US";
    utt.rate = 1.0;
    utt.onend = () => setSpeaking(false);
    utt.onerror = () => setSpeaking(false);
    setSpeaking(true);
    window.speechSynthesis.speak(utt);
  };

  return (
    <div>
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-white font-semibold">Cost Breakdown by Category</h2>
        <button
          onClick={handleSpeak}
          disabled={speaking}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors disabled:opacity-50"
        >
          {speaking ? "⏹ Stop" : "🔊 Read Aloud"}
        </button>
      </div>

      {Object.entries(byCategory).map(([category, catItems]) => {
        const catTotal = catItems.reduce((s, i) => s + i.subtotal_gel, 0);
        return (
          <div key={category} className="mb-4">
            <div className="flex items-center justify-between py-2 px-3 bg-slate-800/50 rounded-t-lg border border-slate-700 border-b-0">
              <span className="text-slate-300 text-sm font-medium capitalize">{category}</span>
              <span className="text-white text-sm font-semibold">{catTotal.toLocaleString()} GEL</span>
            </div>
            <div className="border border-slate-700 rounded-b-lg overflow-hidden">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-slate-500 text-xs border-b border-slate-800 bg-slate-900">
                    <th className="text-left py-2 px-3">Item</th>
                    <th className="text-right py-2 px-3">Qty</th>
                    <th className="text-right py-2 px-3">Unit price</th>
                    <th className="text-right py-2 px-3">Subtotal</th>
                    <th className="text-center py-2 px-3">Conf.</th>
                  </tr>
                </thead>
                <tbody>
                  {catItems.map((item, i) => (
                    <tr key={i} className="border-b border-slate-800/50 last:border-0 bg-slate-900/30 hover:bg-slate-800/30">
                      <td className="py-2.5 px-3 text-slate-200">
                        {item.name}
                        {item.notes && (
                          <span className="block text-xs text-slate-500">{item.notes}</span>
                        )}
                      </td>
                      <td className="py-2.5 px-3 text-right text-slate-300">
                        {item.quantity} {item.unit}
                      </td>
                      <td className="py-2.5 px-3 text-right text-slate-300">
                        {item.unit_price_gel != null ? `${item.unit_price_gel} GEL` : "—"}
                      </td>
                      <td className="py-2.5 px-3 text-right font-medium text-white">
                        {item.subtotal_gel > 0 ? `${item.subtotal_gel.toLocaleString()} GEL` : "—"}
                      </td>
                      <td className={`py-2.5 px-3 text-center text-xs capitalize ${confidenceColor(item.confidence)}`}>
                        {item.confidence}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        );
      })}

      <div className="mt-2 bg-slate-900 border border-slate-700 rounded-xl p-4 text-sm text-slate-400">
        💡 {(estimate.notes as string) || "Prices are estimates based on 2025 Georgian market rates. Get contractor quotes before committing to a budget."}
      </div>
    </div>
  );
}
