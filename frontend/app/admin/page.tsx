"use client";
import { useEffect, useState } from "react";
import { getMaterials, getLabor, updateMaterialPrice, updateLaborPrice } from "@/lib/api";

type Material = { id: number; name: string; category: string; unit: string; price_gel: number };
type Labor    = { id: number; trade: string; unit: string; price_gel: number };

export default function AdminPage() {
  const [materials, setMaterials] = useState<Material[]>([]);
  const [labor, setLabor]         = useState<Labor[]>([]);
  const [editing, setEditing]     = useState<Record<string, string>>({});
  const [saved, setSaved]         = useState<Record<string, boolean>>({});
  const [tab, setTab]             = useState<"materials" | "labor">("materials");

  useEffect(() => {
    getMaterials().then(setMaterials);
    getLabor().then(setLabor);
  }, []);

  const handleSaveMaterial = async (id: number) => {
    const key = `m_${id}`;
    const val = parseFloat(editing[key]);
    if (isNaN(val) || val <= 0) return;
    await updateMaterialPrice(id, val);
    setMaterials((prev) => prev.map((m) => m.id === id ? { ...m, price_gel: val } : m));
    setSaved({ ...saved, [key]: true });
    setTimeout(() => setSaved((s) => ({ ...s, [key]: false })), 1500);
  };

  const handleSaveLabor = async (id: number) => {
    const key = `l_${id}`;
    const val = parseFloat(editing[key]);
    if (isNaN(val) || val <= 0) return;
    await updateLaborPrice(id, val);
    setLabor((prev) => prev.map((l) => l.id === id ? { ...l, price_gel: val } : l));
    setSaved({ ...saved, [key]: true });
    setTimeout(() => setSaved((s) => ({ ...s, [key]: false })), 1500);
  };

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold text-white mb-2">Price Manager</h1>
      <p className="text-slate-400 text-sm mb-6">Update material and labor prices to reflect current Georgian market rates.</p>

      <div className="flex gap-1 mb-6 bg-slate-900 p-1 rounded-xl w-fit">
        {(["materials", "labor"] as const).map((t) => (
          <button key={t} onClick={() => setTab(t)}
            className={`px-5 py-2 rounded-lg text-sm font-medium capitalize transition-colors
              ${tab === t ? "bg-sky-600 text-white" : "text-slate-400 hover:text-white"}`}>
            {t}
          </button>
        ))}
      </div>

      {tab === "materials" && (
        <div className="space-y-2">
          {materials.map((m) => {
            const key = `m_${m.id}`;
            return (
              <div key={m.id} className="flex items-center gap-3 bg-slate-900 border border-slate-800 rounded-xl px-4 py-3">
                <div className="flex-1 min-w-0">
                  <p className="text-white text-sm font-medium truncate">{m.name}</p>
                  <p className="text-slate-500 text-xs capitalize">{m.category} · per {m.unit}</p>
                </div>
                <div className="flex items-center gap-2">
                  <input
                    type="number"
                    step="0.01"
                    defaultValue={m.price_gel}
                    onChange={(e) => setEditing({ ...editing, [key]: e.target.value })}
                    className="w-28 bg-slate-800 border border-slate-700 rounded-lg px-3 py-1.5 text-white text-sm text-right focus:outline-none focus:border-sky-500"
                  />
                  <span className="text-slate-500 text-sm">GEL</span>
                  <button onClick={() => handleSaveMaterial(m.id)}
                    className="px-3 py-1.5 rounded-lg text-xs bg-sky-700 hover:bg-sky-600 text-white transition-colors">
                    {saved[key] ? "✓" : "Save"}
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {tab === "labor" && (
        <div className="space-y-2">
          {labor.map((l) => {
            const key = `l_${l.id}`;
            return (
              <div key={l.id} className="flex items-center gap-3 bg-slate-900 border border-slate-800 rounded-xl px-4 py-3">
                <div className="flex-1 min-w-0">
                  <p className="text-white text-sm font-medium">{l.trade}</p>
                  <p className="text-slate-500 text-xs">per {l.unit}</p>
                </div>
                <div className="flex items-center gap-2">
                  <input
                    type="number"
                    step="0.01"
                    defaultValue={l.price_gel}
                    onChange={(e) => setEditing({ ...editing, [key]: e.target.value })}
                    className="w-28 bg-slate-800 border border-slate-700 rounded-lg px-3 py-1.5 text-white text-sm text-right focus:outline-none focus:border-sky-500"
                  />
                  <span className="text-slate-500 text-sm">GEL</span>
                  <button onClick={() => handleSaveLabor(l.id)}
                    className="px-3 py-1.5 rounded-lg text-xs bg-sky-700 hover:bg-sky-600 text-white transition-colors">
                    {saved[key] ? "✓" : "Save"}
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
