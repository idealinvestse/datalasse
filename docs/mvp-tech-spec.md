# MVP Tech Spec — Bygglov B2C

> Skapad: 2026-06-19  
> Version: 0.1 (Pre-development)  
> Scope: MVP för Borlänge pilot — 1 åtgärdstyp (tillbyggnad) — 10-20 pilotanvändare  
> Förutsättningar: BBR 2026-övergång hanterad, PBL 1 dec 2025-regler, BankID, Lantmäteriet API

---

## 0. Sammanfattning

| Parameter | Värde |
|-----------|-------|
| **Namn (arbetstitel)** | Bygglansen / ByggNu / LovPilot — *att välja* |
| **Målgrupp** | Privatpersoner (B2C) som vill bygga till sin villa |
| **Första åtgärdstyp** | Tillbyggnad (15-30m² bruttoarea) |
| **Första kommun** | Borlänge |
| **Pilotanvändare** | 10-20 |
| **Pilotstart** | September 2026 (efter Öppet hus 23/9) |
| **Driftkostnad** | ~25 500 kr/månad |
| **Pris per ansökan** | 995 kr (medel) |
| **Break-even** | 385 ansökningar/år |

---

## 1. Arkitektur (Högnivå)

```
┌────────────────────────────────────────────────────────────┐
│                  Användare (privatperson)                  │
│                                                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │  Mobil web   │  │  Desktop web │  │  App (senare)│    │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘    │
└─────────┼─────────────────┼─────────────────┼──────────────┘
          │                 │                  │
          └─────────────────┼──────────────────┘
                            │
                  ┌─────────▼─────────┐
                  │   CDN + WAF       │  (Cloudflare/Vercel)
                  └─────────┬─────────┘
                            │
        ┌───────────────────┴───────────────────────┐
        │                                           │
        ▼                                           ▼
┌──────────────┐                          ┌──────────────┐
│  Frontend    │                          │  Backend API │
│  (Next.js)   │  ◄────REST/JSON────►     │  (Node.js)   │
│              │                          │              │
│  - Wizard    │                          │  - Auth      │
│  - Kartor    │                          │  - Validator │
│  - Formulär  │                          │  - Generator │
│  - Status    │                          │  - Submission│
└──────────────┘                          └──────┬───────┘
                                                 │
        ┌────────────────────────────────────────┼─────────────────────┐
        │                    │                   │                     │
        ▼                    ▼                   ▼                     ▼
  ┌──────────┐         ┌──────────┐         ┌──────────┐         ┌──────────┐
  │ Postgres │         │PostGIS   │         │  S3      │         │ Redis    │
  │ (Data)   │         │(Geodata) │         │ (Filer)  │         │ (Cache)  │
  └──────────┘         └──────────┘         └──────────┘         └──────────┘
        │                    │
        └─────────┬──────────┘
                  │
                  ▼
        ┌──────────────────┐
        │  Lantmäteriet API│  (externt)
        └──────────────────┘

         ▲                              ▲
         │                              │
   ┌─────┴──────┐                ┌──────┴──────┐
   │ BankID     │                │ Borlänge    │
   │ (externt)  │                │ API/e-post  │
   └────────────┘                └─────────────┘
```

---

## 2. Tech Stack

### 2.1 Frontend
| Komponent | Val | Motivering |
|-----------|-----|------------|
| **Framework** | Next.js 14+ (App Router) | SSR för SEO, bra DX, svensk community |
| **Språk** | TypeScript | Strikt typning, minskar buggar |
| **UI-bibliotek** | shadcn/ui + Tailwind | Snyggt default, anpassningsbart, WCAG-friendly |
| **Kartor** | MapLibre GL + Lantmäteriets tiles | Open source, fri hosting |
| **Formulär** | React Hook Form + Zod | Validering, minimal re-renders |
| **State** | Zustand | Lättviktigt, bra för wizard-state |
| **I18n** | next-intl | Svenska primärt, ev. engelska |
| **Tester** | Vitest + Playwright | E2E för kritiska flöden |

### 2.2 Backend
| Komponent | Val | Motivering |
|-----------|-----|------------|
| **Runtime** | Node.js 20 LTS | Samma språk som frontend |
| **Framework** | Fastify | Snabbare än Express, inbyggd TS-stöd |
| **Databas** | PostgreSQL 16 + PostGIS 3.4 | Rumslig data för fastigheter/kartor |
| **ORM** | Prisma | Type-safe queries, migrationer |
| **Filförvaring** | S3-kompatibel (R2/Backblaze) | Billigt, GDPR-vänligt i EU-region |
| **Cache** | Redis | Sessions, rate limiting, hot data |
| **Jobb-kö** | BullMQ | Asynkrona jobb (e-post, submission, PDF-gen) |
| **PDF-generering** | Puppeteer/Playwright headless | Rita situationsplan, kontrollplan, fullmakt |
| **Loggning** | Pino → Loki/CloudWatch | Strukturerad loggning |
| **Monitoring** | Sentry + Plausible | Errors + analytics (privacy-first) |

### 2.3 DevOps & Hosting
| Komponent | Val | Motivering |
|-----------|-----|------------|
| **Hosting** | Vercel (frontend) + Railway/Fly.io (backend) | Snabb deploy, hanterar skalning |
| **CI/CD** | GitHub Actions | Standard, gratis för OSS |
| **Container** | Docker + docker-compose | Reproducerbar utvecklingsmiljö |
| **IaC** | Terraform (valfritt i MVP) | Definiera infra som kod |
| **Domän** | .se-domän via Loopia/One.com | Svensk trovärdighet |
| **Email** | Resend eller Postmark | Bra leverans, EU-baserad |
| **SSL** | Let's Encrypt | Standard |

### 2.4 Externa tjänster (Beroenden)

| Tjänst | Syfte | Status |
|--------|-------|--------|
| **BankID** | Autentisering & signering | Köp API-nyckel via bankid.com |
| **Lantmäteriet Fastighetsinfo API** | Hämta fastighetsdata, ägare, gränser | Kräver avtal, kontakta Lantmäteriet |
| **Lantmäteriet Öppna data (CC0)** | Kartor, ortofoto, topografisk data | Gratis |
| **PostNord Adressvalidering** | Validering av fastighetsadresser | Öppen API |
| **Mina ombud (Boverket)** | Digital fullmakt | Undersök tillgänglighet |
| **Borlänge Artvise API** | Inlämning av ansökan | Kontakta IT-chef |
| **Stripe (eller Swish)** | Betalning | Standard |

---

## 3. Datamodell (PostgreSQL)

### 3.1 ER-Översikt

```
┌──────────┐       ┌──────────┐       ┌──────────┐
│  User    │1─────*│ Project  │1─────*│ Document │
└──────────┘       └─────┬────┘       └──────────┘
                         │1                 │
                         │                  │
                         │*                 │
                   ┌─────▼────┐        ┌────▼─────┐
                   │  Plot    │        │FileStorage│
                   │ (PostGIS)│        └──────────┘
                   └──────────┘
                         │
                         │1
                         │
                         │*
                   ┌─────▼────┐
                   │Submission│
                   └─────┬────┘
                         │1
                         │
                         │*
                   ┌─────▼────┐
                   │ EventLog │
                   └──────────┘
```

### 3.2 Tabeller (MVP — 1 åtgärdstyp)

#### `users` (Privatpersoner)
```sql
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  personnummer_hash VARCHAR(64) UNIQUE,  -- SHA-256(personnummer + salt)
  bankid_pnr VARCHAR(13) UNIQUE,          -- från BankID, 12+1
  email VARCHAR(255) UNIQUE NOT NULL,
  email_verified BOOLEAN DEFAULT FALSE,
  full_name VARCHAR(255),
  phone VARCHAR(20),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### `properties` (Fastigheter)
```sql
CREATE TABLE properties (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  
  -- Från Lantmäteriet
  fastighetsbeteckning VARCHAR(100) NOT NULL,  -- t.ex. "BORLÄNGE TÄRNAN 1:2"
  kommun_code VARCHAR(4) NOT NULL,             -- "2081" (Borlänge)
  kommun_name VARCHAR(100) NOT NULL,           -- "Borlänge"
  lan_code VARCHAR(2),
  
  -- Geometri
  geom GEOMETRY(MultiPolygon, 3006) NOT NULL,  -- SWEREF99 TM
  
  -- Metadata
  area_m2 NUMERIC(10,2),
  address VARCHAR(255),
  postal_code VARCHAR(10),
  city VARCHAR(100),
  
  -- Detaljplan
  detaljplan_id VARCHAR(100),                  -- från Combify/NGP
  detaljplan_status VARCHAR(50),               -- "inom", "utanför"
  
  -- Ägare
  agare_namn VARCHAR(255),
  agare_personnummer_hash VARCHAR(64),
  
  -- Rådata från Lantmäteriet
  raw_data JSONB,
  
  fetched_at TIMESTAMPTZ DEFAULT NOW(),
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_properties_fastighetsbeteckning ON properties(fastighetsbeteckning);
CREATE INDEX idx_properties_user_id ON properties(user_id);
CREATE INDEX idx_properties_geom ON properties USING GIST(geom);
```

#### `projects` (Projekt/Ansökningar)
```sql
CREATE TYPE project_type AS ENUM (
  'TILLBYGGNAD',     -- MVP scope
  'NYBYGGNAD',       -- Fas 2
  'KOMPLEMENTBYGGNAD', -- Fas 2
  'FASADANDRING',    -- Fas 2
  'CARPORT_GARAGE',  -- Fas 2
  'RIVNING'          -- Fas 3
);

CREATE TYPE project_status AS ENUM (
  'DRAFT',                -- Pågående ifyllnad
  'COMPLETED',            -- Klar för granskning
  'SUBMITTED',            -- Skickad till kommun
  'IN_REVIEW',            -- Kommun granskar
  'COMPLEMENT_REQUESTED', -- Komplettering begärd
  'APPROVED',             -- Beviljad
  'REJECTED',             -- Avslagen
  'WITHDRAWN'             -- Återkallad
);

CREATE TABLE projects (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  property_id UUID NOT NULL REFERENCES properties(id) ON DELETE RESTRICT,
  
  project_type project_type NOT NULL DEFAULT 'TILLBYGGNAD',
  status project_status NOT NULL DEFAULT 'DRAFT',
  
  -- Projektdetaljer (tillbyggnad-specifikt)
  project_name VARCHAR(255),
  beskrivning TEXT,
  bruttoarea_m2 NUMERIC(10,2),         -- t.ex. 25.0
  byggnadsarea_m2 NUMERIC(10,2),
  hojd_m NUMERIC(5,2),                  -- t.ex. 3.0
  antal_vaningar SMALLINT DEFAULT 1,
  avstand_tomtgrans_m NUMERIC(5,2),     -- 4,5 m kräver granneintyg
  avstand_jarnvag_m NUMERIC(5,2),
  
  -- Avvikelser från detaljplan
  avviker_fran_detaliplan BOOLEAN DEFAULT FALSE,
  avvikelse_beskrivning TEXT,
  
  -- Avgifter
  preliminart_avgift_belopp NUMERIC(10,2),    -- uppskattat
  preliminart_avgift_kommun_taxa JSONB,         -- rådata från Bygglo/kommun
  
  -- Tidsstämplar
  completed_at TIMESTAMPTZ,
  submitted_at TIMESTAMPTZ,
  approved_at TIMESTAMPTZ,
  rejected_at TIMESTAMPTZ,
  
  -- Diarienummer från kommunen
  diarienummer VARCHAR(50),
  
  -- Fullmakt-status
  fullmakt_signed_at TIMESTAMPTZ,
  fullmakt_id VARCHAR(100),
  
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_projects_user_id ON projects(user_id);
CREATE INDEX idx_projects_status ON projects(status);
CREATE INDEX idx_projects_submitted_at ON projects(submitted_at);
```

#### `documents` (Handlingar)
```sql
CREATE TYPE document_type AS ENUM (
  'SITUATIONSPLAN',
  'PLANRITNING',
  'FASADRITNING_NORR',
  'FASADRITNING_SYD',
  'FASADRITNING_OST',
  'FASADRITNING_VAST',
  'SEKTIONSRITNING',
  'KONTROLLPLAN',
  'BRANDSKYDDSBESKRIVNING',
  'KONSTRUKTIONSRITNING',
  'ENERGIBERAKNING',
  'GRANNEMEDGIVANDE',
  'FULLMAKT',
  'OVRIGT'
);

CREATE TABLE documents (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  document_type document_type NOT NULL,
  file_name VARCHAR(255) NOT NULL,
  file_path VARCHAR(500) NOT NULL,      -- S3 path
  file_size_bytes INTEGER,
  mime_type VARCHAR(50),
  uploaded_at TIMESTAMPTZ DEFAULT NOW(),
  
  -- Auto-validering
  auto_validated BOOLEAN DEFAULT FALSE,
  validation_warnings JSONB,
  
  -- Status
  required BOOLEAN DEFAULT TRUE,
  missing BOOLEAN DEFAULT FALSE
);

CREATE INDEX idx_documents_project_id ON documents(project_id);
```

#### `submissions` (Inlämningar)
```sql
CREATE TYPE submission_method AS ENUM (
  'API',
  'EMAIL',
  'PROXY'
);

CREATE TYPE submission_status AS ENUM (
  'PENDING',        -- Köad
  'IN_PROGRESS',    -- Skickas
  'SENT',           -- Skickad
  'DELIVERED',      -- Bekräftad mottagen (om API)
  'FAILED',         -- Misslyckades
  'RETRYING'
);

CREATE TABLE submissions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID NOT NULL UNIQUE REFERENCES projects(id) ON DELETE CASCADE,
  
  method submission_method NOT NULL,
  status submission_status NOT NULL DEFAULT 'PENDING',
  
  -- API-respons / e-post-bekräftelse
  external_id VARCHAR(100),                -- Kommunens ärende-ID
  external_response JSONB,
  error_message TEXT,
  
  retry_count SMALLINT DEFAULT 0,
  max_retries SMALLINT DEFAULT 3,
  
  submitted_at TIMESTAMPTZ,
  delivered_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### `event_log` (Audit trail)
```sql
CREATE TABLE event_log (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID REFERENCES projects(id) ON DELETE SET NULL,
  user_id UUID REFERENCES users(id) ON DELETE SET NULL,
  event_type VARCHAR(50) NOT NULL,        -- t.ex. 'SUBMISSION_SENT', 'DOC_UPLOADED'
  event_data JSONB,
  ip_address INET,
  user_agent TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_event_log_project_id ON event_log(project_id);
CREATE INDEX idx_event_log_created_at ON event_log(created_at);
```

#### `communes` (Kommundata)
```sql
CREATE TABLE communes (
  code VARCHAR(4) PRIMARY KEY,             -- "2081"
  name VARCHAR(100) NOT NULL,
  lan VARCHAR(100),
  
  -- Avgifter
  avgifter JSONB,                          -- struktur: {tillbyggnad: 5922, ...}
  taxa_url VARCHAR(500),
  
  -- Integration
  integration_method VARCHAR(50),          -- 'API', 'EMAIL', 'PROXY'
  integration_config JSONB,
  e_service_url VARCHAR(500),
  
  -- Avgiftskälla
  avgifter_source VARCHAR(50),             -- 'BYGGLO', 'KOMMUN_TAXA', 'MANUAL'
  avgifter_updated_at TIMESTAMPTZ,
  
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 3.3 Seed Data
```sql
INSERT INTO communes (code, name, lan, integration_method, avgifter) VALUES
('2081', 'Borlänge', 'Dalarnas län', 'EMAIL', 
  '{"tillbyggnad_15_30m2": 5922, "tillbyggnad_30_60m2": 10800, "villa_nybyggnad": 10152, "attefall_anamalan": 2961, "fasadandring": 4653}'),
-- ... lägg till fler kommuner vid expansion
;
```

---

## 4. API Endpoints (REST)

### 4.1 Authentiseringsflöde (BankID)

```
POST /api/auth/bankid/init     → Initiera BankID-session
POST /api/auth/bankid/poll     → Polla status (QR / direct)
POST /api/auth/bankid/cancel   → Avbryt
GET  /api/auth/me              → Hämta inloggad användare
POST /api/auth/logout          → Logga ut
```

### 4.2 Fastigheter

```
GET  /api/properties/search?q=fastighetsbeteckning
   → Sök i Lantmäteriet eller cached data
POST /api/properties
   → Hämta och spara fastighetsinfo baserat på fastighetsbeteckning
GET  /api/properties/:id
   → Hämta detaljer
GET  /api/properties/:id/detaljplan
   → Hämta detaljplan (via Combify API)
GET  /api/properties/:id/grannar
   → Hämta rågrannar (kräver särskild behörighet, se juridisk)
```

### 4.3 Projekt (Ansökan)

```
POST /api/projects                       → Skapa nytt projekt
GET  /api/projects                       → Lista användarens projekt
GET  /api/projects/:id                   → Hämta projekt
PATCH /api/projects/:id                  → Uppdatera (autosave)
POST /api/projects/:id/documents         → Ladda upp dokument
DELETE /api/projects/:id/documents/:docId
GET  /api/projects/:id/validation        → Validera kompletthet
POST /api/projects/:id/fullmakt/sign     → Signera fullmakt (BankID)
POST /api/projects/:id/submit            → Skicka in (till kommun)
GET  /api/projects/:id/status            → Hämta status
```

### 4.4 Kommuner

```
GET  /api/communes/:code
   → Hämta kommundata (avgifter, kontaktinfo)
GET  /api/communes/:code/avgifter?type=tillbyggnad&size=25
   → Hämta specifik avgift
```

### 4.5 Betalning

```
POST /api/payments/create-intent         → Stripe/Swish
POST /api/payments/webhook               → Status från Stripe
```

### 4.6 Admin (för framtida handläggar-gränssnitt)

```
GET  /api/admin/projects?status=SUBMITTED
GET  /api/admin/communes
PATCH /api/admin/communes/:code
```

---

## 5. Frontend Routes (Next.js App Router)

```
/                                    → Landningssida (SEO)
/guide                               → "Vad vill du bygga?"-guide
/kommun/:slug                        → Kommun-sida (t.ex. /kommun/borlange)
/lagar                               → Lagar & regler
/om-oss                              → Om oss
/priser                              → Prissättning
/kontakt                             → Kontakt
/login                               → BankID-login
/dashboard                           → Användarens projekt
/dashboard/projekt/:id               → Projektvy (status, dokument)
/dashboard/projekt/:id/skapa          → Wizard (nytt projekt)
/dashboard/projekt/:id/dokument       → Dokumenthanterare
/dashboard/projekt/:id/skicka-in     → Inlämning
/dashboard/projekt/:id/bekraftelse    → Bekräftelse efter inlämning
/admin                               → Admin (Fas 2)
```

---

## 6. Affärsregler & PBL-2025-motor

### 6.1 Regel-motor: "Behöver jag bygglov?"

**Input:**
- Fastighetsbeteckning
- Åtgärdstyp
- Yta, höjd, våningar
- Avstånd till tomtgräns
- Inom/utanför detaljplan

**Output:**
```
{
  "requires_building_permit": true|false,
  "category": "lov"|"anmalan"|"lovbefriat",
  "reasons": [
    "Tillbyggnaden är 25 m² — överstiger inte 30 m²-gränsen för lovfri tillbyggnad",
    "Avstånd till tomtgräns 1,5 m — kräver granneintyg och bygglov"
  ],
  "next_steps": ["Skapa bygglovsansökan", ...],
  "estimated_fee": 5922,
  "estimated_processing_weeks": 10
}
```

**Beslutsträd (PBL 1 dec 2025):**
```
1. Inom detaljplan?
   ├─ JA → Gå till 2
   └─ NEJ → Gå till 3

2. Inom detaljplan, tillbyggnad:
   Bruttoarea ≤ 30 m²?
   ├─ JA → Lovbefriat (men anmälan kan krävas)
   └─ NEJ → Bygglov krävs

3. Utanför detaljplan, tillbyggnad:
   Bruttoarea ≤ 30 m² OCH > 4,5m från gräns?
   ├─ JA → Lovbefriat (men anmälan kan krävas)
   └─ NEJ → Bygglov krävs

4. Undantag (ALLTID bygglov):
   - Inom riksintresse totalförsvar
   - Särskilt värdefullt område
   - < 30m från järnväg
   - Strandskydd
   - < 4,5m från tomtgräns (om ej granneintyg)
```

**Implementation:**
```typescript
// src/lib/rules/tillbyggnad.ts
interface TillbyggnadInput {
  bruttoareaM2: number;
  avstandTomtgransM: number;
  inomDetaljplan: boolean;
  inomRiksintresse: boolean;
  inomStrandskydd: boolean;
  inomJarnvag: boolean;
  avstandJarnvagM: number;
  harGranneintyg: boolean;
}

function utvarderaTillbyggnad(input: TillbyggnadInput): RegelmotorSvar {
  // ... PBL 2025 + BBR 2026
}
```

### 6.2 Kompletthetsvalidering

Innan inlämning, kontrollera att alla obligatoriska handlingar finns:

```typescript
const REQUIRED_DOCUMENTS = {
  TILLBYGGNAD: [
    'SITUATIONSPLAN',
    'PLANRITNING',
    'FASADRITNING_NORR',
    'FASADRITNING_SYD',
    'FASADRITNING_OST',
    'FASADRITNING_VAST',
    'SEKTIONSRITNING',
    'KONTROLLPLAN',
  ]
};
```

**Output:**
```json
{
  "is_complete": false,
  "missing": [
    {
      "type": "KONTROLLPLAN",
      "name": "Kontrollplan",
      "description": "Kontrollplan enligt PBL 10 kap. 6 §"
    }
  ],
  "warnings": [
    {
      "type": "AVSTAND_TOMTGRANS",
      "message": "Avstånd 1,5m understiger 4,5m — granneintyg krävs"
    }
  ]
}
```

### 6.3 Auto-genererade dokument

**Situationsplan** (genererad):
- Hämta fastighetskarta från Lantmäteriet
- Rita tillbyggnaden baserat på användarens inmatade koordinater
- Inkludera avstånd till gränser
- Exportera som PDF (A3, skala 1:400)

**Kontrollplan** (genererad):
- Standardmall från Boverket
- Ifylld med projekt-specifika punkter
- Signeras med BankID

**Fullmakt** (genererad):
- Boverkets standardmall via Mina ombud
- Eller egen PDF-mall med BankID-signering

---

## 7. Borlänge-integration

### 7.1 Detektions- och integrationsflöde

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Användare   │────►│  Backend     │────►│  Borlänge    │
│  Klickar     │     │  Avgör       │     │              │
│  "Skicka in" │     │  metod       │     │              │
└──────────────┘     └──────┬───────┘     └──────────────┘
                            │
                ┌───────────┴───────────┐
                ▼                       ▼
        API tillgängligt?         E-post-fallback
        ├─ JA: POST /BO-BYGG-PBL    ├─ Generera PDF-paket
        │  + diarienummer return   │  - Ansökningsblankett
        │                          │  - Alla bilagor
        │                          │  - Fullmakt
        │                          │  - Skicka till bygglov@borlange.se
        │                          │  - Spara kvitto
        │
        └─ NEJ: Proxy
           - Använd bankid via bygg.borlange.se
           - Autoifyll formulärfält via Puppeteer
           - Ladda upp filer
           - Returnera diarienummer
```

### 7.2 E-post-fallback (default för MVP)

**Mall för e-post till Borlänge:**
```
Till: bygglov@borlange.se (eller via Artvise e-tjänst)
Från: noreply@bygglansen.se (med användarens e-post i CC)
Ämne: Bygglovsansökan — [Fastighetsbeteckning] — [Projektnamn]

Hej Borlänge kommun,

Här kommer en bygglovsansökan inskickad via Bygglansen som tekniskt ombud.

Byggherre: [Användarens namn]
Personnummer: [Användarens personnummer (om användaren valt att dela)]
Fastighetsbeteckning: [Fastighetsbeteckning]
Adress: [Fastighetsadress]
Kontakt: [E-post], [Telefon]

Åtgärd: Tillbyggnad, 25 m² bruttoarea
Beskrivning: [Kort beskrivning]

Diarienummer: [Auto-genererat av oss, t.ex. BYGG-2026-001234]

Bilagor:
1. Ansökningsblankett (signerad med BankID)
2. Situationsplan (PDF)
3. Planritning (PDF)
4. Fasadritningar (4 st, PDF)
5. Sektionsritning (PDF)
6. Kontrollplan (signerad med BankID)
7. Fullmakt (signerad med BankID)

Med vänliga hälsningar,
Bygglansen som tekniskt ombud för [Användarens namn]
```

### 7.3 Retry-strategi

- 3 försök med exponentiell backoff (1min, 5min, 30min)
- Vid misslyckande: notifiera användaren, spara för manuell hantering
- E-post-leverans bekräftas via ReturnPath/Postmark webhook

---

## 8. Säkerhet & Compliance

### 8.1 Autentisering
- **BankID** för inloggning (Nivå 3 — samma som e-legitimation)
- **BankID** för signering av fullmakt och kontrollplan
- Session-cookie: HTTP-only, Secure, SameSite=Strict, 24h utgång

### 8.2 Auktorisering
- Användare ser bara sina egna projekt
- Admin-roll för framtida handläggar-vy
- Audit-loggning av alla data-access

### 8.3 Datahantering
- All personuppgiftshantering enligt GDPR
- Kryptering i vila (PostgreSQL TDE / disk-encryption)
- Kryptering i transit (TLS 1.3)
- Backup: daglig, krypterad, 30 dagars retention
- Dataminimering: spara bara nödvändig data

### 8.4 DOS-lagen (Tillgänglighet)
- **WCAG 2.1 nivå AA** — implementerat från dag 1
- Tillgänglighetsredogörelse publicerad på /tillganglighet
- Tester: axe-core i CI, manuella tester med skärmläsare
- Synsfokus, kontrast, semantisk HTML, ARIA-attribut

### 8.5 Loggning & Monitoring
- Strukturerade loggar (Pino → JSON)
- Sentry för fel-rapportering
- Plausible för analytics (privacy-first, ingen cookie-banner behövs)
- Uptime monitoring (UptimeRobot/BetterStack)

---

## 9. Testningsstrategi

### 9.1 Enhetstester
- Alla regler-funktioner (tillbyggnad, senare fler)
- Valideringslogik
- Affärsregler
- Target: 80%+ coverage

### 9.2 Integrationstester
- BankID-mock
- Lantmäteriet API-mock
- Stripe/Swish-mock
- Borlänge e-post-mock

### 9.3 E2E-tester (Playwright)
- "Behöver jag bygglov?"-flöde
- Skapa projekt (wizard)
- Ladda upp dokument
- Signera fullmakt
- Skicka in ansökan
- Följa status

### 9.4 Manuella tester
- Användartester med 3-5 privatpersoner
- Demo för Borlänge bygglovshandläggare
- Tillgänglighetstester med riktiga hjälpmedel

---

## 10. Deployment & Miljöer

### 10.1 Miljöer

| Miljö | URL | Syfte | Data |
|-------|-----|-------|------|
| **dev** | localhost:3000 | Lokal utveckling | Sandbox |
| **staging** | staging.bygglansen.se | Tester, demo | Sandbox + anonymiserad data |
| **prod** | bygglansen.se | Pilot + produktion | Riktig data |

### 10.2 CI/CD-pipeline

```yaml
# .github/workflows/main.yml (skiss)
name: CI/CD
on: [push, pull_request]
jobs:
  test:
    steps:
      - Lint (ESLint, Prettier)
      - Type-check (tsc)
      - Unit tests (Vitest)
      - Integration tests
      - E2E tests (Playwright)
      - Accessibility tests (axe-core)
  deploy-staging:
    if: branch == 'main'
    steps:
      - Build
      - Deploy to Vercel (frontend)
      - Deploy to Railway (backend)
      - Run smoke tests
  deploy-prod:
    if: tag == 'v*'
    needs: test
    steps:
      - Deploy
      - Notify team
```

### 10.3 Release-plan
- **Vecka 1-4 (augusti):** Grundläggande wizard + fastighetssök
- **Vecka 5-6 (tidig september):** Dokumentuppladdning + fullmakt
- **Vecka 7 (mitten september):** E-post-inlämning till Borlänge
- **Vecka 8 (23 september):** Demo på Öppet hus, MVP redo för pilot
- **Vecka 9-12 (oktober):** Pilot med 10-20 användare
- **Q4 2026 / Q1 2027:** Iterera + expandera

---

## 11. Kostnadsbudget

### 11.1 Initial setup (engångskostnader)
| Post | Kostnad |
|------|---------|
| Domän + SSL | 500 kr |
| Juridisk granskning (användarvillkor) | 15 000 kr |
| Design (logo, brand) | 5 000 kr |
| Initial marknadsföring | 10 000 kr |
| Diverse (bankkonto, företagsregistrering) | 3 000 kr |
| **Total initialt** | **~33 500 kr** |

### 11.2 Månatliga driftskostnader

| Post | MVP (låg volym) | Skala (1000 ansök/mån) |
|------|-----------------|------------------------|
| Vercel (frontend) | 0 kr (hobby-tier) | 2 500 kr |
| Railway (backend + db) | 500 kr | 5 000 kr |
| BankID-anslutning | 3 000 kr | 3 000 kr |
| Lantmäteriet API | 0–5 000 kr | 10 000 kr |
| S3 (R2/Backblaze) | 100 kr | 1 000 kr |
| Resend (e-post) | 200 kr | 1 000 kr |
| Plausible | 100 kr | 500 kr |
| Sentry | 0 kr (hobby) | 1 000 kr |
| Utvecklarunderhåll (50% tid) | 40 000 kr | 60 000 kr |
| Diverse | 2 000 kr | 5 000 kr |
| **Total** | **~46 000 kr/mån** | **~89 000 kr/mån** |

### 11.3 Intäktsprognos (per scenariot i affärsmodells-dok)

| Scenario | Ansökningar/mån | Intäkt/mån | Vinst/mån |
|----------|----------------|------------|-----------|
| MVP (pilot) | 5 | 5 000 kr | -41 000 kr |
| Tidig tillväxt | 50 | 50 000 kr | +4 000 kr |
| Skala | 250 | 250 000 kr | +161 000 kr |
| Full | 1 000 | 1 000 000 kr | +911 000 kr |

**Break-even: ~50 ansökningar/månad** (~600/år) — rimligt att nå år 2.

---

## 12. Risker & Mitigeringer

| Risk | Sannolikhet | Påverkan | Mitigation |
|------|-------------|----------|------------|
| **Borlänge nekar e-post-inlämning** | Medium | Hög | Tidig kontakt aug 2026, fallback PDF-utskrift |
| **BankID-integration kräver certifiering** | Hög | Hög | Börja process tidigt (4-8 veckor ledtid) |
| **Lantmäteriet API-avtal tar lång tid** | Medium | Medium | Använd öppna data (CC0) som backup |
| **Pilotanvändare kan inte hitta bra projekt att testa** | Medium | Medium | Personlig rekrytering + Garanti för återbetalning |
| **Låg conversion (klick → köp)** | Hög | Hög | Gratis guide som "top of funnel", A/B-testa CTA |
| **GDPR-granskning** | Låg | Hög | Strikt datahantering, användarvillkor, DPIA utförd |
| **DOS-vite (tillgänglighet)** | Låg | Medium | WCAG 2.1 AA från dag 1 |

---

## 13. Definition of Done — MVP

✅ En Borlängebo kan:
1. Logga in med BankID
2. Ange sin fastighetsbeteckning och få detaljplan-info
3. Se "Behöver jag bygglov?"-svar för tillbyggnad
4. Fylla i wizard för tillbyggnad 15-30m²
5. Se avgiftsuppskattning (5 922 kr för Borlänge)
6. Ladda upp situationsplan + 4 fasadritningar + plan + sektion + kontrollplan
7. Signera fullmakt med BankID
8. Skicka in till Borlänge via e-post
9. Få bekräftelse med diarienummer
10. Se status på sitt projekt (manuellt uppdaterad initialt)
11. Betala 995 kr (via Swish eller kort)

✅ Plattformen uppfyller:
- WCAG 2.1 AA
- GDPR-krav
- Användarvillkor publicerade
- Tillgänglighetsredogörelse

✅ Tekniskt:
- Alla endpoints dokumenterade
- Testtäckning >70%
- CI/CD fungerar
- Loggning och monitoring på plats

---

## 14. Nästa steg

| Vecka | Task | Ägare |
|-------|------|-------|
| V25 (denna vecka) | Detta dokument klart | Moss |
| V26-27 (jun-jul) | Sommarpaus, förbered infrastruktur | Moss |
| V28 (v 7/7) | Kontakta Borlänge + påbörja BankID-process | Moss + Oscar |
| V29-30 (jul-aug) | Bygg wizard, datamodell, Lantmäteriet-integration | Moss |
| V31 (aug) | Kontakta Borlänge IT-chef (efter sommaruppehåll) | Oscar |
| V32-34 (aug-sep) | Bygg dokumentuppladdning, fullmakt, inlämning | Moss |
| V35 (v 23/9) | Demo Öppet hus Palladium, MVP redo för pilot | Oscar |
| V36-39 (sep-okt) | Pilot med 10-20 användare, iterera | Oscar + Moss |
| V40+ (okt) | Utvärdera pilot, planera expansion | Oscar |

---

## 15. Relaterade dokument

- [bygglov-mvp-spec.md](./bygglov-mvp-spec.md) — Fullständig produktspec
- [konkurrensanalys-bygglov.md](./konkurrensanalys-bygglov.md) — Konkurrenter
- [affarsmodell-juridik-bygglov.md](./affarsmodell-juridik-bygglov.md) — Affärsmodell & juridik
- Borlänge pilotdata i spec-dokumentet (sektion 12)
