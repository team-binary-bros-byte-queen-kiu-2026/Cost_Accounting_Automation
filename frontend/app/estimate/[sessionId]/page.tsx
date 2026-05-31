"use client";
import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import CostBreakdown from "@/components/CostBreakdown";
import ChatStream from "@/components/ChatStream";
import { getStoredEstimate } from "@/lib/api";

export default function EstimatePage() {
  const params = useParams();
  const sessionId = params.sessionId as string;
  const [estimate, setEstimate] = useState<Record<string, unknown> | null>(null);
  const [activeTab, setActiveTab] = useState<"estimate" | "chat">("estimate");

  useEffect(() => {
    const stored = getStoredEstimate(sessionId);
    if (stored) setEstimate(stored);
  }, [sessionId]);

  if (!estimate) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-16 text-center text-slate-400">
        <p>Loading estimate… if this persists, <a href="/" className="text-sky-400 underline">start a new analysis</a>.</p>
      </div>
    );
  }

  const est = estimate as {
    grand_total_gel: number;
    materials_total_gel: number;
    labor_estimate_gel: number;
    building_type: string;
    floor_area_m2: number | null;
    cost_per_m2_gel: number | null;
    confidence: string;
    approval_required?: boolean;
    notes: string;
  };

  return (
    <div className="max-w-5xl mx-auto px-4 py-8">
      {/* Summary banner */}
      <div className="bg-gradient-to-r from-sky-900/60 to-slate-900 border border-sky-800/50 rounded-2xl p-6 mb-6">
        <div className="flex flex-wrap gap-6 items-center justify-between">
          <div>
            <p className="text-slate-400 text-sm mb-1">Estimated Total Cost</p>
            <p className="text-4xl font-bold text-white">
              {est.grand_total_gel.toLocaleString()} GEL
            </p>
            {est.cost_per_m2_gel && (
              <p className="text-slate-400 text-sm mt-1">{est.cost_per_m2_gel.toLocaleString()} GEL / m²</p>
            )}
          </div>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <Stat label="Materials" value={`${est.materials_total_gel.toLocaleString()} GEL`} />
            <Stat label="Labor (est.)" value={`${est.labor_estimate_gel.toLocaleString()} GEL`} />
            <Stat label="Building type" value={est.building_type || "—"} />
            <Stat label="Floor area" value={est.floor_area_m2 ? `${est.floor_area_m2} m²` : "—"} />
          </div>
        </div>
        {est.approval_required && (
          <div className="mt-4 p-3 bg-amber-900/40 border border-amber-700 rounded-lg text-amber-300 text-sm">
            ⚠️ Large estimate — professional quantity surveyor review recommended.
          </div>
        )}
        <div className="mt-3 flex gap-2 items-center text-xs text-slate-500">
          <span>Confidence: <span className="text-slate-300 capitalize">{est.confidence}</span></span>
          <span>·</span>
          <span>{est.notes}</span>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 mb-6 bg-slate-900 p-1 rounded-xl w-fit">
        {(["estimate", "chat"] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-5 py-2 rounded-lg text-sm font-medium transition-colors capitalize
              ${activeTab === tab ? "bg-sky-600 text-white" : "text-slate-400 hover:text-white"}`}
          >
            {tab === "estimate" ? "📊 Cost Breakdown" : "💬 Ask Questions"}
          </button>
        ))}
      </div>

      {activeTab === "estimate" ? (
        <CostBreakdown estimate={estimate} sessionId={sessionId} />
      ) : (
        <ChatStream sessionId={sessionId} />
      )}
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-slate-500">{label}</p>
      <p className="text-white font-medium capitalize">{value}</p>
    </div>
  );
}
