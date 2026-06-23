# Bygglov B2C MVP — Dokumentation

> **Startpunkt:** Läs `../memory/projects/bygglov-mvp-progress.md` först för överblick.  
> **Status:** Research klar (90%) | Pilotstart 23 september 2026 | Första kommun: Borlänge

---

## 📄 Dokument

| # | Fil | Syfte | När läsa? |
|---|-----|-------|-----------|
| 1 | **[bygglov-mvp-spec.md](./bygglov-mvp-spec.md)** | Fullständig produktspec — bakgrund, juridik, användarflöden, krav, faser | För helhetsförståelse av produkten |
| 2 | **[konkurrensanalys-bygglov.md](./konkurrensanalys-bygglov.md)** | Djupanalys av Bygglo, Bygglov24, Bygglovsportalen, Bygglov.se + positionering | För att förstå marknaden och vår nisch |
| 3 | **[affarsmodell-juridik-bygglov.md](./affarsmodell-juridik-bygglov.md)** | Affärsmodell (transaktion+premium), juridisk analys, go-to-market | Innan prissättning, juridisk dialog, lansering |
| 4 | **[mvp-tech-spec.md](./mvp-tech-spec.md)** | Teknisk spec: arkitektur, datamodell (SQL), API, frontend, deployment, kostnader | Innan utveckling börjar |

---

## 🚀 Snabbstart

**Första gången på projektet?**
1. Läs `memory/projects/bygglov-mvp-progress.md` (5 min)
2. Skumma `konkurrensanalys-bygglov.md` (10 min) — förstå nischen
3. Djupdyk i det dokument du behöver för ditt syfte

**För utvecklare:**
- Börja med `mvp-tech-spec.md` — se Datamodell (sektion 3) och API (sektion 4)

**För sälj/pitch:**
- Börja med `bygglov-mvp-spec.md` sektion 1 (Problem) + `affarsmodell-juridik-bygglov.md` (Affärsmodell)

**För juridisk dialog:**
- Börja med `affarsmodell-juridik-bygglov.md` sektion 2 (Juridik)

---

## 🎯 Beslutade nyckelfakta

- **Målgrupp:** B2C (privatpersoner)
- **Första kommun:** Borlänge (4v handläggning, 97% beviljandegrad)
- **Första åtgärdstyp:** Tillbyggnad 15-30 m²
- **Affärsmodell:** 495-1995 kr per ansökan + Premium 99 kr/mån
- **Integration:** API primärt, e-post fallback
- **Juridisk approach:** Tekniskt ombud med BankID-fullmakt
- **Tech stack:** Next.js + Fastify + PostgreSQL/PostGIS
- **Pilotstart:** 23 september 2026 (Öppet hus Palladium, Borlänge)

---

## ⏰ Kritiska deadlines

| Datum | Händelse |
|-------|----------|
| **1 juli 2026** | BBR-övergångsperiod slutar — enbart nya regler |
| **15 juni – 7 augusti 2026** | Borlänge sommaruppehåll |
| **7 augusti 2026** | Första möjliga kontakt med Borlänge |
| **23 september 2026** | Öppet hus, Palladium Borlänge (demo) |
| **Oktober 2026** | Pilotstart, 10-20 användare |

---

## 📞 Primära kontakter

| Person/Org | Roll | Kontakt |
|------------|------|---------|
| **Peter Sjöberg** | IT-chef Borlänge | peter.sjoberg@borlange.se |
| **Borlänge Servicecenter** | Kommun | 0243-740 00, kommun@borlange.se |
| **Boverket** | Myndighet | Via kontaktformulär |
| **Lantmäteriet** | Myndighet | Via kundtjänst |
| **BankID** | Tjänst | bankid.com |

---

*Skapad: 2026-06-19 | Senast uppdaterad: 2026-06-19*
