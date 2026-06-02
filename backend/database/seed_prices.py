"""
Seed the SQLite database with sample Georgian construction market prices (2025).
Run once: python backend/database/seed_prices.py
Replace prices with actual market values before production.
"""
import sqlite3
import os

DB_PATH = os.environ.get("DATABASE_PATH", "./database/prices.db")


def seed():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Apply schema
    schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
    with open(schema_path) as f:
        conn.executescript(f.read())

    # ── MATERIALS ─────────────────────────────────────────────────────────────
    materials = [
        # Concrete
        ("Concrete M200", "concrete", "m3", 165.0, "Standard concrete for footings and slabs"),
        ("Concrete M300", "concrete", "m3", 185.0, "Structural concrete for foundations and columns"),
        ("Concrete M400", "concrete", "m3", 210.0, "High-strength concrete for load-bearing structures"),
        ("Ready-mix concrete delivery", "concrete", "m3", 25.0, "Delivery surcharge per m3"),
        # Masonry
        ("Red ceramic brick (standard)", "masonry", "unit", 0.45, "250x120x65mm standard brick"),
        ("White silicate brick", "masonry", "unit", 0.38, "Silicate facing brick"),
        ("Concrete block (200mm)", "masonry", "unit", 1.80, "Hollow concrete block 400x200x200mm"),
        ("Aerated concrete block (Ytong)", "masonry", "unit", 2.50, "Lightweight AAC block 600x300x200mm"),
        ("Mortar (ready-mix)", "masonry", "bag_25kg", 8.50, "Masonry mortar 25kg bag"),
        # Steel
        ("Steel rebar Ø10mm", "steel", "kg", 1.15, "Deformed steel bar for reinforcement"),
        ("Steel rebar Ø12mm", "steel", "kg", 1.20, "Deformed steel bar for reinforcement"),
        ("Steel rebar Ø16mm", "steel", "kg", 1.25, "Heavy rebar for columns and beams"),
        ("Structural steel I-beam", "steel", "kg", 1.80, "Hot-rolled I-beam"),
        ("Steel mesh (road mesh)", "steel", "m2", 8.50, "150x150x6mm welded mesh"),
        # Roofing
        ("Corrugated metal sheet", "roofing", "m2", 18.0, "Galvanized steel roofing sheet"),
        ("Ceramic roof tile", "roofing", "m2", 32.0, "Clay roof tile including underlay"),
        ("Metal tile (Metrotile)", "roofing", "m2", 28.0, "Steel tile with stone coating"),
        ("Roofing membrane (waterproof)", "roofing", "m2", 12.0, "APP bitumen membrane"),
        ("Timber roof structure", "roofing", "m2", 45.0, "Timber rafters and purlins per m2 of roof"),
        # Insulation
        ("Mineral wool (100mm)", "insulation", "m2", 14.0, "Rock wool wall/ceiling insulation"),
        ("EPS polystyrene (100mm)", "insulation", "m2", 11.0, "Expanded polystyrene insulation board"),
        ("XPS extruded polystyrene (50mm)", "insulation", "m2", 16.0, "For foundation and floor insulation"),
        ("Spray foam insulation", "insulation", "m2", 22.0, "Polyurethane spray foam per m2"),
        # Finishes
        ("Ceramic floor tiles (standard)", "finishes", "m2", 28.0, "30x30cm standard ceramic floor tile"),
        ("Ceramic floor tiles (premium)", "finishes", "m2", 55.0, "60x60cm premium porcelain tile"),
        ("Interior plaster (machine)", "finishes", "m2", 12.0, "Gypsum machine plaster per m2"),
        ("Exterior render (silicone)", "finishes", "m2", 22.0, "Silicone decorative render"),
        ("Interior paint (2 coats)", "finishes", "m2", 8.0, "Water-based latex paint per m2"),
        ("Laminate flooring (standard)", "finishes", "m2", 18.0, "8mm AC3 laminate with underlay"),
        ("Hardwood parquet", "finishes", "m2", 65.0, "18mm solid oak parquet"),
        ("Gypsum board (plasterboard)", "finishes", "m2", 9.0, "12.5mm GKB single layer installed"),
        # Openings
        ("PVC window (double-glazed)", "openings", "m2", 185.0, "White PVC window with 2-chamber glazing"),
        ("Aluminium window", "openings", "m2", 260.0, "Aluminium frame with thermal break"),
        ("Interior door (hollow-core)", "openings", "unit", 180.0, "Standard hollow-core interior door with frame"),
        ("Interior door (solid wood)", "openings", "unit", 380.0, "Solid wood interior door with frame"),
        ("Exterior door (steel)", "openings", "unit", 550.0, "Insulated steel entry door"),
        ("Garage door (sectional)", "openings", "unit", 1200.0, "Automatic sectional garage door"),
        # Waterproofing
        ("Bitumen waterproofing paint", "waterproofing", "m2", 9.0, "Bitumen emulsion 2-coat application"),
        ("PVC waterproof membrane", "waterproofing", "m2", 28.0, "1.5mm PVC membrane for wet rooms"),
    ]

    cur.executemany(
        "INSERT OR IGNORE INTO materials (name, category, unit, price_gel, description) VALUES (?,?,?,?,?)",
        materials,
    )

    # ── LABOR ─────────────────────────────────────────────────────────────────
    labor = [
        ("General laborer", "day", 60.0, "Unskilled labor for site work"),
        ("Mason / bricklayer", "day", 85.0, "Skilled brickwork and blockwork"),
        ("Concrete finisher", "day", 80.0, "Formwork, pouring, finishing"),
        ("Carpenter (rough)", "day", 90.0, "Formwork and structural timber"),
        ("Carpenter (finish)", "day", 110.0, "Doors, windows, finish carpentry"),
        ("Steel fixer / ironworker", "day", 95.0, "Rebar cutting, bending, tying"),
        ("Roofer", "day", 100.0, "Roof tile and sheet installation"),
        ("Plasterer", "day", 85.0, "Interior and exterior plastering"),
        ("Tiler", "day", 90.0, "Floor and wall tile installation"),
        ("Painter", "day", 75.0, "Interior and exterior painting"),
        ("Electrician", "hour", 18.0, "Licensed electrical work"),
        ("Plumber", "hour", 20.0, "Plumbing rough-in and finishing"),
        ("HVAC technician", "hour", 22.0, "Heating, ventilation, AC installation"),
        ("Site foreman", "day", 130.0, "Site supervision and coordination"),
        ("Architect / designer (small project)", "hour", 45.0, "Design and drawings"),
    ]

    cur.executemany(
        "INSERT OR IGNORE INTO labor (trade, unit, price_gel, description) VALUES (?,?,?,?)",
        labor,
    )

    # ── EQUIPMENT ─────────────────────────────────────────────────────────────
    equipment = [
        ("Concrete mixer (250L)", "day", 45.0, "Towable concrete mixer rental"),
        ("Scaffolding (per 10m2)", "week", 35.0, "Standard tube and fitting scaffolding"),
        ("Mobile crane (5 ton)", "day", 350.0, "Including operator"),
        ("Excavator (mini)", "day", 280.0, "Mini excavator including operator"),
        ("Concrete pump", "day", 400.0, "Truck-mounted concrete pump"),
        ("Compactor plate", "day", 55.0, "Vibrating plate compactor"),
        ("Aerial work platform", "day", 180.0, "Electric scissor lift to 8m"),
    ]

    cur.executemany(
        "INSERT OR IGNORE INTO equipment (name, unit, price_gel, description) VALUES (?,?,?,?)",
        equipment,
    )

    conn.commit()
    conn.close()
    print(f"✅ Database seeded at {DB_PATH}")
    print(f"   {len(materials)} materials, {len(labor)} labor rates, {len(equipment)} equipment items")


if __name__ == "__main__":
    seed()
