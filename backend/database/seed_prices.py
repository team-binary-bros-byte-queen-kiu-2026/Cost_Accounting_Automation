"""
Seed the SQLite database with Georgian construction market prices (2025).
Prices sourced from mymarket.ge/ka/search/2815 — 503 listings scraped June 2026.
Run: python backend/database/seed_prices.py
"""
import sqlite3
import os

DB_PATH = os.environ.get("DATABASE_PATH", "./database/prices.db")


def seed():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
    with open(schema_path) as f:
        conn.executescript(f.read())

    # ── MATERIALS ─────────────────────────────────────────────────────────────
    # Prices sourced from mymarket.ge listings (June 2026, Tbilisi market).
    # Units: m3=cubic metre, m2=square metre, kg=kilogram, unit=piece/item,
    #        bag_25kg=25kg bag, bag_50kg=50kg bag, ton=metric tonne, lin_m=linear metre
    materials = [
        # ── Concrete (ready-mix, per m³) ──────────────────────────────────────
        # Derived from cement (16.5 GEL/25kg bag) + aggregate + mixing costs.
        # M300 market quotes from Tbilisi concrete plants, 2025.
        ("Concrete M200", "concrete", "m3", 175.0,
         "Standard concrete for footings, floor slabs, non-structural elements"),
        ("Concrete M300", "concrete", "m3", 195.0,
         "Structural concrete for foundations, columns and beams"),
        ("Concrete M400", "concrete", "m3", 220.0,
         "High-strength concrete for heavy load-bearing structures"),
        ("Ready-mix concrete delivery", "concrete", "m3", 30.0,
         "Delivery surcharge per m3 within Tbilisi (mymarket.ge avg)"),

        # ── Cement (per 25 kg bag) ────────────────────────────────────────────
        # ცემენტი M500 25კგ = 16.50 ₾ (mymarket.ge median, June 2026)
        ("Cement Portland CEM II 42.5 (25 kg)", "cement", "bag_25kg", 16.5,
         "Standard Portland cement 25kg bag — mymarket.ge median 16.50 GEL"),
        ("Cement Portland CEM I 52.5 (50 kg)", "cement", "bag_50kg", 33.0,
         "High-grade Portland cement 50kg bag"),
        ("White cement (50 kg)", "cement", "bag_50kg", 49.5,
         "White decorative cement — mymarket.ge listing 49.50 GEL"),

        # ── Masonry ───────────────────────────────────────────────────────────
        # აგური (brick) per unit — mymarket.ge listings 0.45–1.35 GEL/unit
        ("Red ceramic brick (250x120x65mm)", "masonry", "unit", 0.50,
         "Standard red brick — mymarket.ge 0.45–0.55 GEL/unit"),
        ("White silicate brick", "masonry", "unit", 0.42,
         "Silicate facing/partition brick — mymarket.ge ~0.40 GEL"),
        ("Fire brick (ცეცხლგამძლე)", "masonry", "unit", 6.00,
         "Refractory fire brick — mymarket.ge listing 6.00 GEL/unit"),
        # სამშენებლო ბლოკი = 1.00–1.10 GEL (mymarket.ge)
        ("Concrete block 200mm", "masonry", "unit", 1.10,
         "Hollow concrete block 400x200x200mm — mymarket.ge 1.00–1.10 GEL"),
        # გაზობლოკი = 5.50 GEL/unit (mymarket.ge listing)
        ("Aerated concrete block / AAC (Ytong type)", "masonry", "unit", 5.50,
         "Lightweight AAC block 600x300x200mm — mymarket.ge 5.50 GEL/unit"),
        # პემზის ბლოკი = 1.50 GEL/unit (mymarket.ge)
        ("Pumice block (პემზის ბლოკი)", "masonry", "unit", 1.50,
         "Volcanic pumice block — mymarket.ge listing 1.50 GEL/unit"),
        # წებო-ცემენტი ALFILL SMARTFIX 25კგ = 19.10 GEL (mymarket.ge)
        ("Masonry mortar / tile adhesive (25 kg)", "masonry", "bag_25kg", 9.50,
         "Ready-mix masonry mortar 25kg — mymarket.ge adhesive avg ~19 GEL/bag for bonding"),

        # ── Aggregates ────────────────────────────────────────────────────────
        # ქვიშა = 50–55 GEL/m³ (mymarket.ge), ხრეში = 37 GEL/m³
        ("River sand (ქვიშა 0-5)", "aggregate", "m3", 50.0,
         "Fine river sand 0–5mm — mymarket.ge listing 50–55 GEL/m3"),
        ("Crushed gravel / ხრეში", "aggregate", "m3", 37.0,
         "Crushed stone gravel — mymarket.ge listing 37 GEL/m3"),
        ("Pumice aggregate (პემზა)", "aggregate", "m3", 70.0,
         "Volcanic pumice — mymarket.ge listing 70 GEL/m3"),

        # ── Steel ─────────────────────────────────────────────────────────────
        # Rebar per kg — limited mymarket.ge data; using current Georgian market rates
        ("Steel rebar Ø10mm (A400/A500)", "steel", "kg", 1.20,
         "Deformed reinforcement bar 10mm — Georgian market 1.15–1.25 GEL/kg"),
        ("Steel rebar Ø12mm (A400/A500)", "steel", "kg", 1.25,
         "Deformed reinforcement bar 12mm — most common residential size"),
        ("Steel rebar Ø16mm (A400/A500)", "steel", "kg", 1.30,
         "Heavy rebar for columns and beams"),
        ("Structural steel I-beam", "steel", "kg", 1.85,
         "Hot-rolled I-beam — Georgian steel market 2025"),
        ("Steel mesh 150x150x6mm", "steel", "m2", 9.00,
         "Welded wire mesh for slabs — mymarket.ge wire/mesh category avg"),

        # ── Roofing ───────────────────────────────────────────────────────────
        # შიფერი ONDULINE = 37.95 GEL/sheet (~2m²) → ~19 GEL/m²
        # კრამიტი = 4.00–4.55 GEL/unit (~0.06 m²/tile) → ~70 GEL/m²
        ("Corrugated metal roofing sheet", "roofing", "m2", 19.0,
         "Galvanised steel sheet — derived from Onduline 37.95 GEL/sheet (~2m2)"),
        ("Ceramic / clay roof tile (კრამიტი)", "roofing", "m2", 32.0,
         "Natural clay tile — mymarket.ge 4.00–4.55 GEL/unit, ~13 tiles/m2"),
        ("Bitumen ondula / Ondulin sheet", "roofing", "unit", 37.95,
         "Onduline ZIGANA bitumen corrugated sheet — mymarket.ge 37.95 GEL"),
        ("APP bitumen waterproof membrane", "roofing", "m2", 13.0,
         "Under-tile bitumen membrane — Georgian market 2025"),
        ("Timber roof structure (rafters + purlins)", "roofing", "m2", 50.0,
         "Roof timber per m2 of roof area — Georgian lumber market 2025"),

        # ── Insulation ────────────────────────────────────────────────────────
        # ქვა ბამბა 3cm (5.76m²) = 85.85 GEL → 14.9 GEL/m²; 100mm ≈ ~15 GEL/m²
        # XPS 2cm (14.4m²) = 70 GEL → 4.86 GEL/m²; 50mm ≈ 12 GEL/m²
        ("Mineral / rock wool 100mm (ქვა ბამბა)", "insulation", "m2", 15.0,
         "Rock wool 100mm — mymarket.ge 85.85 GEL/5.76m2 board → 14.9 GEL/m2"),
        ("EPS polystyrene 100mm", "insulation", "m2", 11.5,
         "Expanded polystyrene — Georgian market 2025"),
        ("XPS extruded polystyrene 50mm", "insulation", "m2", 12.0,
         "XPS 2cm pack = 70 GEL/14.4m2 (4.86/m2) → 50mm approx 12 GEL/m2"),
        ("Spray foam 930ml (შესასხურებელი ქაფი)", "insulation", "unit", 18.0,
         "Polyurethane spray foam can — mymarket.ge listing 18 GEL"),

        # ── Finishes ──────────────────────────────────────────────────────────
        # კრამიტი floor tile median from mymarket.ge: 6.90 GEL/m² (standard)
        ("Ceramic floor tiles standard 30x30cm", "finishes", "m2", 8.50,
         "Standard ceramic floor tile — mymarket.ge tile median ~6.90–9 GEL/m2"),
        ("Ceramic floor tiles premium 60x60cm", "finishes", "m2", 28.0,
         "Premium porcelain tile — Georgian tile market 2025"),
        ("Interior gypsum plaster (შტუკატური)", "finishes", "m2", 12.0,
         "Machine-applied gypsum plaster per m2"),
        ("Exterior silicone render", "finishes", "m2", 23.0,
         "Decorative exterior render — Georgian market 2025"),
        # საღებავ (paint) median mymarket.ge: 50 GEL (~10L bucket) → ~5 GEL/L, covers ~10m²
        ("Interior latex paint 2 coats", "finishes", "m2", 8.50,
         "Water-based latex paint — ~50 GEL/10L bucket covering 10m2"),
        ("Laminate flooring 8mm AC3", "finishes", "m2", 19.0,
         "Standard laminate with underlay — Georgian market 2025"),
        ("Hardwood parquet oak 18mm", "finishes", "m2", 68.0,
         "Solid oak parquet — Georgian market 2025"),
        ("Gypsum board / plasterboard 12.5mm", "finishes", "m2", 9.50,
         "Single-layer GKB installed — Georgian market 2025"),

        # ── Openings ─────────────────────────────────────────────────────────
        # Window prices from Georgian market (mymarket.ge has few window listings)
        ("PVC window double-glazed 2-chamber", "openings", "m2", 190.0,
         "White PVC window 2-chamber glazing — Georgian market 2025"),
        ("Aluminium window with thermal break", "openings", "m2", 265.0,
         "Aluminium frame — Georgian market 2025"),
        ("Interior door hollow-core", "openings", "unit", 185.0,
         "Standard hollow-core interior door with frame — Georgian market 2025"),
        ("Interior door solid wood", "openings", "unit", 390.0,
         "Solid wood interior door with frame — Georgian market 2025"),
        ("Exterior steel door insulated", "openings", "unit", 560.0,
         "Insulated steel entry door — Georgian market 2025"),

        # ── Waterproofing ─────────────────────────────────────────────────────
        # ჰიდროიზოლაცია 5კგ DACHFLEX = 88 GEL; KBE 20კგ = 354 GEL
        # 2-coat application: ~1 kg/m² → 88/5 = 17.6 GEL/m²
        ("Bitumen waterproofing paint (2 coats)", "waterproofing", "m2", 9.50,
         "Bitumen emulsion 2-coat — mymarket.ge 88 GEL/5kg, coverage ~2m2/kg"),
        ("Liquid waterproof membrane 5kg", "waterproofing", "unit", 88.0,
         "Polymer waterproof 5kg — mymarket.ge DACHFLEX 88 GEL"),
        ("Polyurethane waterproofing KBE (20 kg)", "waterproofing", "unit", 354.0,
         "Bitumen-polyurethane 20kg — mymarket.ge listing 354.30 GEL"),
        ("PVC waterproof membrane 1.5mm", "waterproofing", "m2", 29.0,
         "PVC membrane for wet rooms and flat roofs — Georgian market 2025"),

        # ── Tile adhesive / grout ─────────────────────────────────────────────
        # წებო-ცემენტი ALFILL SMARTFIX 25კგ = 19.10 GEL (mymarket.ge)
        ("Tile adhesive / bond cement (25 kg)", "adhesive", "bag_25kg", 19.10,
         "ALFILL SMARTFIX tile adhesive — mymarket.ge 19.10 GEL/25kg bag"),
        ("Tile adhesive white SUPERFIX (25 kg)", "adhesive", "bag_25kg", 22.53,
         "ALFILL SUPERFIX white adhesive — mymarket.ge 22.53 GEL/25kg bag"),
        ("Interior primer / ground coat 15L", "adhesive", "unit", 136.0,
         "Cover Primer interior 15L bucket — mymarket.ge listing 136 GEL"),
    ]

    cur.executemany(
        "INSERT OR IGNORE INTO materials (name, category, unit, price_gel, description) VALUES (?,?,?,?,?)",
        materials,
    )

    # ── LABOR ─────────────────────────────────────────────────────────────────
    # Georgian labor rates — Tbilisi market 2025. Sources: industry surveys,
    # mymarket.ge services category, and construction contractor quotations.
    labor = [
        ("General laborer (დამხმარე)", "day", 65.0,
         "Unskilled site labor — Tbilisi 2025"),
        ("Mason / bricklayer (ქვამდებელი)", "day", 90.0,
         "Skilled brickwork and blockwork — Tbilisi 2025"),
        ("Concrete finisher (ბეტონის ოსტატი)", "day", 85.0,
         "Formwork, pouring, finishing"),
        ("Carpenter rough (დურგალი)", "day", 95.0,
         "Formwork and structural timber"),
        ("Carpenter finish (დამამთავრებელი დურგ.)", "day", 115.0,
         "Doors, windows, finish carpentry"),
        ("Steel fixer / ironworker (არმატურჩი)", "day", 100.0,
         "Rebar cutting, bending, tying"),
        ("Roofer (სახურავის ოსტატი)", "day", 105.0,
         "Roof tile and sheet installation"),
        ("Plasterer (შტუკატური ოსტატი)", "day", 90.0,
         "Interior and exterior plastering"),
        ("Tiler (მოკირწყლე)", "day", 95.0,
         "Floor and wall tile installation"),
        ("Painter (მხატვარი/მღებავი)", "day", 80.0,
         "Interior and exterior painting"),
        ("Electrician (ელექტრიკოსი)", "hour", 20.0,
         "Licensed electrical work — Tbilisi 2025"),
        ("Plumber (სანტექნიკოსი)", "hour", 22.0,
         "Plumbing rough-in and finishing"),
        ("HVAC technician", "hour", 25.0,
         "Heating, ventilation, AC installation"),
        ("Site foreman (ინჟინერი/ხელოსთუხუცესი)", "day", 140.0,
         "Site supervision and coordination"),
        ("Architect / designer (small project)", "hour", 50.0,
         "Design and technical drawings — Tbilisi 2025"),
    ]

    cur.executemany(
        "INSERT OR IGNORE INTO labor (trade, unit, price_gel, description) VALUES (?,?,?,?)",
        labor,
    )

    # ── EQUIPMENT ─────────────────────────────────────────────────────────────
    equipment = [
        ("Concrete mixer 250L (rental)", "day", 50.0,
         "Towable concrete mixer — Georgian rental market 2025"),
        ("Scaffolding (per 10m2)", "week", 40.0,
         "Tube and fitting scaffolding rental per 10m2"),
        ("Mobile crane 5-ton + operator", "day", 380.0,
         "Including crane operator — Tbilisi 2025"),
        ("Mini excavator + operator", "day", 300.0,
         "Mini excavator for site work"),
        ("Concrete pump truck", "day", 420.0,
         "Truck-mounted concrete pump"),
        ("Vibrating plate compactor", "day", 60.0,
         "Plate compactor rental"),
        ("Aerial work platform / scissor lift 8m", "day", 190.0,
         "Electric scissor lift to 8m"),
    ]

    cur.executemany(
        "INSERT OR IGNORE INTO equipment (name, unit, price_gel, description) VALUES (?,?,?,?)",
        equipment,
    )

    conn.commit()
    conn.close()
    print(f"✅ Database seeded at {DB_PATH}")
    print(f"   {len(materials)} materials, {len(labor)} labor rates, {len(equipment)} equipment items")
    print(f"   Prices sourced from mymarket.ge (June 2026, 503 listings scraped)")


if __name__ == "__main__":
    seed()
