
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS vehicles (
 id INTEGER PRIMARY KEY, type TEXT NOT NULL CHECK(type IN ('carro','moto')),
 brand TEXT NOT NULL, model TEXT NOT NULL, version TEXT, year INTEGER NOT NULL,
 plate TEXT NOT NULL UNIQUE, renavam TEXT, chassis TEXT, color TEXT, fuel TEXT,
 odometer_km REAL NOT NULL DEFAULT 0 CHECK(odometer_km >= 0), acquired_on TEXT,
 acquisition_value REAL CHECK(acquisition_value >= 0), photo_path TEXT, notes TEXT,
 status TEXT NOT NULL DEFAULT 'ativo' CHECK(status IN ('ativo','vendido','inativo')),
 is_demo INTEGER NOT NULL DEFAULT 0, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
 updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS records (
 id INTEGER PRIMARY KEY, vehicle_id INTEGER NOT NULL REFERENCES vehicles(id) ON DELETE CASCADE,
 kind TEXT NOT NULL CHECK(kind IN ('manutencao','pagamento','seguro','documento','abastecimento','despesa')),
 category TEXT NOT NULL, description TEXT NOT NULL, due_date TEXT, performed_on TEXT,
 amount REAL NOT NULL DEFAULT 0 CHECK(amount >= 0), status TEXT NOT NULL DEFAULT 'pendente'
   CHECK(status IN ('pendente','pago','atrasado','concluido','ativo')),
 odometer_km REAL, details TEXT, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_records_vehicle ON records(vehicle_id);
CREATE INDEX IF NOT EXISTS idx_records_due ON records(due_date);

CREATE TABLE IF NOT EXISTS app_meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
