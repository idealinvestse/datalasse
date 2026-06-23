# Konkurrensanalys — Bygglov B2C (Sverige 2026)

> Skapad: 2026-06-19 | Syfte: Kartlägga B2C-konkurrenters features, styrkor & svagheter för att forma MVP:ns positionering

---

## Sammanfattning — Marknadsgap

**Ingen aktör erbjuder plattformsoberoende digital inlämning av bygglov.** Alla B2C-spelare är antingen:
- **Informationsguider** (Bygglo, Bygglovsportalen) — talar om vad som gäller, men lämnar inte in
- **Lead-gen / marknadsplatser** (Bygglov24, Bygglov.se) — matchar dig med konsulter
- **Kommunala e-tjänster** — tar emot ansökan, men bara för EN kommun

**GAP:** En tjänst som guidar användaren → förbereder ALLA handlingar → och sedan **skickar in till valfri kommun** digitalt. Detta finns inte idag.

---

## 1. Bygglo (bygglo.com)

### Positionering
"Sveriges bygglovsguide" — vägledning, inte myndighetsbeslut.

### Features
| Feature | Detalj | Betyg |
|---------|--------|-------|
| Projektbibliotek | 9 projekttyper: friggebod, attefall, garage, carport, tillbyggnad, altan, balkong, staket/plank, pool, fasadändring | ⭐⭐⭐⭐⭐ |
| Kommunjämförelse | 290 kommuner — avgifter, handläggningstider, e-tjänst-status | ⭐⭐⭐⭐⭐ |
| Avgiftsdatabas | Snittavgifter för 275 kommuner (CSV-export) | ⭐⭐⭐⭐ |
| Guider | ~8 min lästid per guide, praktiska och konkreta | ⭐⭐⭐⭐ |
| Ritningsguide | Genomgång av situationsplan, planritning, fasadritning, sektionsritning | ⭐⭐⭐ |
| Grannemedgivande | Guide om när det krävs, mall | ⭐⭐⭐ |
| Nyhetsbrev | ❌ Saknas | — |
| Inloggning/Konto | ❌ Saknas — ingen persistent användardata | — |
| Digital inlämning | ❌ Finns inte — "vägledning, inte myndighetsbeslut" | — |
| Expert-matchning | ❌ Finns inte | — |

### Affärsmodell (uppskattad)
- Troligtvis SEO-drivet → annonsintäkter + affiliate-länkar till tjänsteföretag
- Ingen synlig betalvägg eller prenumeration
- Lågintensiv men bred trafikstrategi

### Styrkor
- Mest omfattande kommunjämförelse (275-290 kommuner)
- Tydlig projektbaserad navigation
- Välskrivna, SEO-optimerade guider
- Data-driven (avgifter, handläggningstider)

### Svagheter
- Renodlad informationssajt — ingen transaktionsförmåga
- Ingen användarregistrering — kan inte följa ärenden
- Ingen integration med Lantmäteriet eller kommunsystem
- Ingen dokumentgenerering — bara förklarar vad som behövs

### Ta med till MVP
- ✅ Projektbaserad navigation ("Vad vill du bygga?")
- ✅ Kommunjämförelse med avgiftsdata
- ✅ Tydliga steg-för-steg guider

---

## 2. Bygglov24.se

### Positionering
"Allt om bygglov — samlat på ett ställe" — stark lead-gen mot konsulter.

### Features
| Feature | Detalj | Betyg |
|---------|--------|-------|
| Bygglovskalkylator | Uppskattar kostnad per åtgärdstyp | ⭐⭐⭐⭐ |
| Kommunguider | 290 kommuner med specifika regler | ⭐⭐⭐⭐ |
| Konsultmatchning | Gratis, svar inom 24h — formulärbaserad | ⭐⭐⭐⭐ |
| Åtgärdstyper | 15+ typer (mer detaljerade än Bygglo) | ⭐⭐⭐⭐ |
| Guider | 4-stegsprocess: Identifiera → Regler → Ansök → Konsult | ⭐⭐⭐ |
| Nyhetsbrev | ❌ Saknas | — |
| Inloggning/Konto | ❌ Saknas | — |
| Digital inlämning | ❌ Finns inte — hänvisar till kommun | — |
| Dokumentmallar | ❌ Saknas | — |

### Affärsmodell
- **Lead generation** — huvudintäkt från konsultmatchning (tar betalt av konsulter/företag för leads)
- Gratis för slutanvändaren
- Låg barriär — inget konto krävs, bara formulär

### Styrkor
- Enkel, konverteringsoptimerad UX
- Tydlig CTA ("Få hjälp av en konsult")
- Brett utbud av åtgärdstyper
- Betald lead-modell ger direkt intäkt

### Svagheter
- Ytligare guider än Bygglo
- Ingen egen dokumenthantering
- Beroende av tredjeparts-konsulter för värdeleverans
- Lågt förtroende — känns som en mellanhand

### Ta med till MVP
- ✅ Kalkylator för totalkostnad
- ✅ 4-stegs tydlig process
- ⚠️ Lead-gen kan vara sekundär intäkt, men inte primär

---

## 3. Bygglovsportalen (bygglovsportalen.se)

### Positionering
"Smidig väg till bygglov från start till mål" — processplattform.

### Features
| Feature | Detalj | Betyg |
|---------|--------|-------|
| Processguide | Från start till mål, checkpoints | ⭐⭐⭐⭐ |
| Kommuninfo | Specifik info per kommun (t.ex. Haninge) | ⭐⭐⭐ |
| Ritningsstöd | Mallar och exempel | ⭐⭐⭐ |
| Expert-nätverk | Möjlighet att hitta experter | ⭐⭐⭐ |
| Inloggning/Konto | ✅ Möjligt (Wix-baserad medlemsfunktion) | ⭐⭐ |
| Mobilapp | ❌ Saknas | — |
| Digital inlämning | ❌ Inte fullständig — guide, inte inlämning | — |
| Notifieringar | ❌ Saknas | — |

### Affärsmodell (uppskattad)
- Sannolikt freemium: gratis guider → betalt för premium (mallar, checklistor, personlig rådgivning)
- Byggd på Wix — mindre teknisk komplexitet, snabbare time-to-market
- Mindre datatung än Bygglo

### Styrkor
- Helhetsgrepp om processen (inte bara info)
- Kommun-specifik information
- Visuellt tilltalande (Wix-design)

### Svagheter
- Wix-baserad → tekniskt begränsad för API-integrationer
- Ingen faktisk digital inlämning
- Grundare kommunjämförelse än Bygglo
- Mindre känd — lägre trafik

### Ta med till MVP
- ✅ "Från start till mål"-positionering
- ✅ Kommun-specifika sidor
- ❌ Wix-begränsningen — MVP bör byggas på egen stack för API-flexibilitet

---

## 4. Bygglov.se (Bygglov.se 290 AB)

### Positionering
"Ditt byggprojekt börjar här" — marknadsplats + guide.

### Features
| Feature | Detalj | Betyg |
|---------|--------|-------|
| Expert-marknadsplats | Verifierade profiler för arkitekter, KA, byggare | ⭐⭐⭐⭐⭐ |
| Bygglovsrapporten | 72 474 bygglov analyserade från 248 kommuner | ⭐⭐⭐⭐⭐ |
| Guider per projekt | Friggebod, garage, carport m.fl. | ⭐⭐⭐⭐ |
| Nyhetsbrev | Månatligt — marknadstrender, nya regler | ⭐⭐⭐⭐ |
| Prenumeration för experter | Profil, portfolio, recensioner, leads | ⭐⭐⭐⭐ |
| Personlig vägledning | Experter tolkar regler, återkoppling inom 60 min | ⭐⭐⭐⭐ |
| Inloggning/Konto | ✅ För experter | ⭐⭐⭐ |
| Digital inlämning | ❌ Ingen — hänvisar till kommun | — |
| Dokumentgenerering | ❌ Saknas | — |

### Affärsmodell (bekräftad)
- **Prenumeration från experter** — månadsavgift för att synas på plattformen
- "Inga bindningstider, inga uppstartsavgifter"
- Verifiering av experter krävs
- Bygglovsrapporten 2026 som dragplåster (content marketing)
- Gratis för slutanvändare

### Styrkor
- Starkast marknadsplats — tvåsidig plattform (sökande ↔ experter)
- Bygglovsrapporten ger auktoritet och SEO
- Kvalificerad lead-gen (experter betalar för synlighet)
- Snabb återkoppling (60 min)

### Svagheter
- Fokus på matchning, inte på att faktiskt skicka in bygglov
- Experter kostar pengar — inte en DIY-lösning
- Ingen automation av ansökningsprocessen
- Beroende av experters kvalitet för användarnöjdhet

### Ta med till MVP
- ✅ Tvåsidig plattform (ansökare + experter)
- ✅ Prenumerationsmodell för proffs
- ⚠️ Bygglovsrapport-koncept — unik data som SEO-magnet

---

## 5. Kommunala e-tjänster (ex. Stockholm)

### Positionering
Officiell digital ansökan för en specifik kommun.

### Features (Stockholm exempel)
| Feature | Detalj |
|---------|--------|
| BankID-inloggning | ✅ Fullt implementerat |
| Digital ansökan | ✅ Strukturerat formulär |
| Ärendestatus | ✅ Realtid |
| Dokumentuppladdning | ✅ PDF, ritningar |
| Betalning | ✅ Integrerad |
| Handläggarkommunikation | ✅ Meddelanden |

### Styrkor
- Faktisk inlämning — transaktionsvärde
- BankID — stark autentisering
- Direkt koppling till handläggare
- Förtroende (officiell myndighetsplattform)

### Svagheter
- **En kommun per plattform** — största bristen
- Olika system i olika kommuner
- Ingen vägledning — förutsätter att du vet vad du ska göra
- Oftast bara formulär, ingen smart validering

---

## 6. Samlad Jämförelsematris

| Feature | Bygglo | Bygglov24 | Bygglovs-portalen | Bygglov.se | Kommunal e-tjänst | **Vår MVP** |
|---------|--------|-----------|-------------------|------------|-------------------|-------------|
| **Projekt-guide** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ❌ | ✅ Måste ha |
| **Kommunjämförelse** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ❌ | ✅ Måste ha |
| **Avgiftskalkylator** | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ | ⭐ | ❌ | ✅ Måste ha |
| **Dokument-mallar** | ⭐⭐ | ❌ | ⭐⭐⭐ | ❌ | ❌ | ✅ **Unik** |
| **Faktisk inlämning** | ❌ | ❌ | ❌ | ❌ | ✅ (1 kommun) | ✅ **Unik → alla** |
| **BankID** | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ Måste ha |
| **Ärendestatus** | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ Måste ha |
| **Notifieringar** | ❌ | ❌ | ❌ | ❌ | ⭐⭐ | ✅ Måste ha |
| **Lantmäteri API** | ❌ | ❌ | ❌ | ❌ | ⭐⭐⭐ | ✅ Differentiator |
| **KA-matchning** | ❌ | ❌ | ❌ | ⭐⭐⭐ | ❌ | ⚠️ Fas 2 |
| **Expert-marknadsplats** | ❌ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ❌ | ⚠️ Fas 3 |
| **Data/rapporter** | ⭐⭐⭐ | ❌ | ❌ | ⭐⭐⭐⭐⭐ | ❌ | ⚠️ Fas 3 |
| **Konto/profil** | ❌ | ❌ | ⭐⭐ | ⭐⭐⭐ | ✅ | ✅ Måste ha |
| **Affärsmodell** | Annons/affil. | Lead-gen | Freemium? | Expert-prenum. | Skattefinans. | 🟡 Att besluta |

---

## 7. Positionering & MVP-differentiering

### Var passar MVP:n?

```
HÖG TRANSAKTION                LÅG TRANSAKTION
     │
     │    🏛️ Kommunala            │
     │    e-tjänster              │
     │                            │
     │         ⬅️ VÅRT GAP        │
     │    ★ MVP ★                 │
     │    (Inlämning +            │
     │     vägledning +           │
     │     alla kommuner)         │
     │                            │
     │              Bygglovs-     │
     │              portalen      │    Bygglo
     │                            │
     │         Bygglov.se         │
     │                            │    Bygglov24
     │                            │
     └─────────────────────────────────────
                    GUIDE/INFO
```

### Unik MVP-positionering:
> **"Den enda plattformen där du guidas genom hela processen — och faktiskt kan skicka in ansökan digitalt till vilken kommun som helst."**

### Differentiatorer sammanfattat:
1. **Faktisk inlämning** (ingen annan B2C gör detta utanför kommunala e-tjänster)
2. **Kommunoberoende** (ingen kommunlåsning)
3. **Smart dokumentgenerering** (mallar, autoifyllnad från Lantmäteriet)
4. **Kompletthetsvalidering** (minskar de 50% kompletteringsfallen)
5. **Tidsfristbevakning** (ingen låter användaren glömma deadlines)

---

## 8. Rekommenderade Features från Konkurrentanalys

### Ta från Bygglo:
- ✅ Projektbaserad navigation ("Välj vad du vill bygga")
- ✅ Kommunjämförelse med avgiftsdata (använd Bygglos öppna data eller bygg egen)
- ✅ SEO-optimerade guider som dragplåster

### Ta från Bygglov24:
- ✅ Avgiftskalkylator med totalkostnad (inte bara bygglovsavgift)
- ✅ 4-stegs tydlig process för användaren
- ⚠️ Lead-gen som sekundär intäktskälla

### Ta från Bygglovsportalen:
- ✅ "Från start till mål"-positionering
- ✅ Kommun-specifika landningssidor

### Ta från Bygglov.se:
- ✅ Tvåsidig plattformstanke (ansökare + experter)
- ✅ Datadrivet innehåll som SEO-magnet (bygglovsstatistik)
- ✅ Prenumerationsmodell för experter

### Ta från Kommunala e-tjänster:
- ✅ BankID-integration
- ✅ Ärendestatus i realtid
- ✅ Faktisk digital inlämning

### MVP:ns egna unika features:
- 🆕 **Smart kompletthetskontroll** — auto-validerar att alla handlingar finns innan inskick
- 🆕 **Regel-motor "Behöver jag bygglov?"** — interaktiv wizard baserad på PBL 2025
- 🆕 **Autoifyllnad från Lantmäteriet** — fastighetsdata, grannar, detaljplan
- 🆕 **Dokument-mallar** — generera situationsplan, kontrollplan från ifyllda uppgifter

---

## 9. Öppna Frågor för MVP-beslut

1. ~~Hur integrerar vi mot kommunerna?~~ → ✅ **API/e-post hybrid** (API först, e-post som fallback)
2. ~~Första kommun?~~ → ✅ **Borlänge Kommun** — 52K invånare, 356 ansökningar/år, 4v median handläggning, hög digital mognad
3. **Affärsmodell:** Premium-funktioner? Per-ansökan-avgift? Expert-prenumeration? *(🟡 Obeslutat)*
4. **Regulatory:** Är en privat plattform som skickar in bygglov lagligt? Krävs fullmakt från sökande? *(🟡 Kräver juridisk granskning)*

## 10. Borlänge Kommun — Pilotspecifikation

### Kommunens digitala landskap
- **E-tjänstplattform:** Artvise (artvisemobile.borlange.se)
- **Bygglovs-e-tjänst:** https://bygg.borlange.se/BO-BYGG-PBL (egen subdomän)
- **Digital strategi:** "Digitalt först" — medborgarcentrerad
- **IT-chef:** Peter Sjöberg (peter.sjoberg@borlange.se)
- **Nyckeltal 2025:** 356 ansökningar, 4v median handläggning, 97% beviljandegrad

### Avgifter Borlänge 2026
| Villa | Tillbyggnad | Anmälan/Attefall | Fasadändring |
|-------|-------------|------------------|--------------|
| 10 152 kr | 5 922 kr | 2 961 kr | 4 653 kr |

### Integrationsmöjligheter
1. **API** — undersök bygg.borlange.se + Artvise-plattformens API-kapacitet
2. **E-post** — strukturerad PDF+XML till kommun@borlange.se
3. **Proxy** — autoifyll kommunens e-tjänst via HTTP POST

### Tidslinje för pilotkontakt
- ⏸️ Juni–Augusti: Sommarstängt (15/6–7/8)
- ✅ Augusti 2026: Kontakta IT-chef + bygglovsenhet
- 🎯 September 2026: Demo på Öppet hus (Palladium, 23 sep)