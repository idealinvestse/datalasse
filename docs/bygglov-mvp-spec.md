# Bygglov MVP — Fullständig Specifikation

> Skapad: 2026-06-19  
> Senast uppdaterad: 2026-06-19 (Deep Research Round 2 — B2C-fokus)  
> Målgrupp: **B2C (privatpersoner)**  
> Status: 🟢 Research till ~80% — återstår nisch/positionering & första kommun

---

## ⚡ EXECUTIVE SUMMARY — Nyckelfynd från Research

**🔥 AKUT TIDSFAKTOR:** Den 1 juli 2026 (om 12 dagar!) upphör övergångsperioden för BBR. Från detta datum gäller **enbart** Boverkets nya byggregler (9 separata föreskrifter). Detta är ett hårt cut-off datum som påverkar ALLA bygglovsärenden.

**Största fynd:**
1. **PBL totalreviderades 1 december 2025** — helt nya bygglovsregler gäller
2. **BBR-övergångsperiod slutar 1 juli 2026** — efter detta enbart nya funktionsbaserade regler utan allmänna råd
3. **Lovbefriade åtgärder utökade kraftigt** — komplementbyggnader 30-50m², tillbyggnader 30m²
4. **Combify har redan ett API** med 112 000+ bygglov och 288+ kommuners data
5. **Boverket driver digitalisering** via NGP + begreppsbank + modellbibliotek
6. **Stockholm har 6 månaders väntetid** bara för att få en handläggare
7. **~50% av bygglov behöver kompletteras** (smärtpunkt)

---

## 1. Bakgrund & Problembild

### 1.1 Vad är bygglov?
Bygglov är tillstånd från kommunens byggnadsnämnd för att uppföra, ändra eller riva byggnad. Regleras i **Plan- och bygglagen (PBL, 2010:900)**, **Plan- och byggförordningen (PBF, 2011:338)** samt **Boverkets byggregler (BBR/fristående föreskrifter)**.

### 1.2 Problembild & Smärtpunkter (🟢 Verifierade via research)
| Smärtpunkt | Detalj | Källa |
|-----------|--------|-------|
| Långa handläggningstider | Stockholm: upp till 6 mån väntan på handläggare. Nationellt varierar 6 dagar (Härnösand) → 10+ veckor | Bygglovsrapporten 2026, Stockholm e-tjänst |
| Höga kompletteringskrav | ~50% av alla bygglovsansökningar behöver kompletteras | Bygglov.se (20 maj 2026) |
| Stor kommunal variation | Olika blanketter, processer, digital mognad | Boverket: "hanteras på olika sätt i olika kommuner" |
| Krånglig process för privatpersoner | Svårt veta vad som krävs, vilka handlingar, vilka regler | Flera konkurrenters UX-positionering |
| Nya regler skapar osäkerhet | PBL-ändring 1 dec 2025 + BBR-övergång → förvirring | Boverket, Berg kommunpresentation |

### 1.3 Målgrupp (🟢 Fastställd: B2C)
- **Primär:** Privatpersoner som vill bygga mindre projekt (tillbyggnad, garage, komplementbyggnad)
- **Sekundär:** Små byggföretag, arkitekter som hanterar bygglov åt kunder (B2B2C)
- **Tertiär:** Kommunala handläggare (endast om plattformen senare expanderar till B2G)
- *(🟢 Fastställt: B2C.)*

### 1.4 Konkurrentlandskap (🟢 Kartlagd)

| Aktör | Typ | Täckning | B2C? | Styrkor |
|-------|-----|----------|------|---------|
| **Combify** | API/dataplattform | 288+ kommuner, 112K bygglov | ❌ B2B | Största databasen för bygglov/byggrätter/detaljplaner |
| **Bygglovsportalen** | Digital guide (B2C) | Rikstäckande | ✅ | Steg-för-steg, skapa handlingar själv, hitta experter, gratis |
| **Bygglov.se** | Marknadsplats/guide | Rikstäckande | ✅ | Bygglovsrapporten, hitta experter, information |
| **Bygglo** | Kommunjämförelse | 275 kommuner | ✅ | Jämför avgifter/handläggningstider per kommun, CSV-export |
| **Bygglov24.se** | Guide/kalkylator | 290 kommuner | ✅ | Bygglovskalkylator, guider, offerter från konsulter |
| **Bygglovstjänst** | Tjänsteföretag | Rikstäckande | ✅ | Ritningar, konstruktion, VVS-handlingar |
| **Kommunala e-tjänster** | Myndighetsplattform | Per kommun | ✅ | Stockholm: BankID, ärendehantering, digital ansökan |
| **Boverkets NGP** | Nationell infrastruktur | Nationell | ❌ | Nationell geodataplattform, begreppsbank, modellbibliotek |

**🟡 Positioneringsfråga:** Bygglovsportalen har B2C-guide (gratis). Bygglo/Bygglov24 har kommunjämförelser. Combify har API-databasen. Ingen har en **inlämningsplattform som fungerar över kommungränser** — dagens kommunala e-tjänster är per kommun. Detta kan vara MVP:ns unika nisch.

---

## 2. MVP Scope & Funktioner

### 2.1 Användare & Roller (🟡 Grundstruktur verifierad)

| Roll | Beskrivning | Behörighet |
|------|-------------|------------|
| **Ansökare** | Privatperson/företag som söker bygglov | Skapa/följa ärende |
| **Handläggare** | Kommuntjänsteman | Granska, besluta, begära komplettering |
| **Kontrollansvarig (KA)** | Certifierad extern part | Ladda upp KA-handlingar, signera |
| **Granne/Sakägare** | Berörda av ansökan | Ta del av remiss, yttra sig |
| **Admin** | Systemadministratör | Full tillgång |

*(🟢 KA-rollen bekräftad som obligatorisk vid de flesta byggprojekt enligt PBL.)*

### 2.2 Kernefunktioner (Must-Have)

#### 2.2.1 Ansökan

- [ ] **Guide: "Behöver du bygglov?"** — interaktiv wizard
  - *(🟢 Flera åtgärder är nu lovfria enligt PBL 1 dec 2025. Systemet bör först avgöra om bygglov ens behövs.)*
  
- [ ] **Digital ansökningsblankett** med fält:
  - *(🟢 Följande fältlista verifierad från bygglovstjanst.se, Stockholm e-tjänst, PBL)*
  - Fastighetsbeteckning (auto-komplettering från Lantmäteriet)
  - Typ av åtgärd (nybyggnad, tillbyggnad, komplementbyggnad, ändrad användning, rivning)
  - Byggnadsarea (m²), bruttoarea, höjd, antal våningar
  - Placering på tomt (avstånd till gränser)
  - Projektbeskrivning (fritext)
  - Kontrollansvarig (KA) — *(🟢 Obligatorisk vid de flesta åtgärder)*

- [ ] **Dokumentuppladdning** med checklista per åtgärdstyp:
  - *(🟢 Verifierad lista från bygglovstjanst.se, bygglovs-ritning.se, Stockholm stad)*
  
  | Handling | När krävs? | Format |
  |----------|-----------|--------|
  | Situationsplan (nybyggnadskarta/baskarta) | Alltid | PDF, DWG |
  | Planritningar | Alltid | PDF, DWG |
  | Fasadritningar (4 st) | Alltid | PDF, DWG |
  | Sektionsritning | Alltid | PDF, DWG |
  | Kontrollplan | De flesta projekt | PDF |
  | Brandskyddsbeskrivning | Beroende på projekt | PDF |
  | Konstruktionsritningar | Tekniskt samråd | PDF, DWG |
  | Energiberäkning | Större projekt | PDF |
  | Luftkvalitetsdokumentation | *(🟡 Nytt krav BBR 2025)* | PDF |
  | Fuktsäkerhetsdokumentation | *(🟡 Nytt krav BBR 2025)* | PDF |
  | Vattensäkerhetsdokumentation | *(🟡 Nytt krav BBR 2025)* | PDF |
  | Bullerdokumentation | *(🟡 Nytt krav BBR 2025)* | PDF |
  | Tillgänglighetsutlåtande | Vid större ändringar | PDF |

- [ ] **Fastighetsinformation** — integration med:
  - *(🟢 Lantmäteriet API finns: Direktåtkomst, Visning, Nedladdning)*
  - *(🟡 Behöver utreda: exakt vilket API/avtal som krävs, kostnad)*
  - Automatisk hämtning av fastighetsdata (ägare, yta, gränser)
  - Detaljplanekontroll — *(🟡 Combify har detaljplane-data för 122K+ planer)*

- [ ] **Kartunderlag / situationsplan**
  - *(🟢 Verifierat via Stockholm stad: nybyggnadskarta (1:400, SWEREF99, RH2000) eller baskarta för mindre projekt)*
  - *(🟡 Fråga: Ska systemet generera kartunderlag eller bara ta emot?)*

- [ ] **Närbelägna fastigheter / grannar**
  - *(🟢 Lantmäteriet har fastighetsgränser, kan identifiera rågrannar)*
  - *(🟡 Remiss till grannar krävs vid avvikelse från detaljplan eller utanför detaljplanerat område — ej vid enkel komplementbyggnad.)*

#### 2.2.2 Handläggning

- [ ] **Inkommande ärendehantering** (dashboard för handläggare)
- [ ] **Kompletteringsbegäran** — *(🟢 Viktigt: ~50% av ärenden kräver komplettering)*
- [ ] **Tidsfristbevakning** — *(🟢 10 veckor standard, +10 veckor förlängning)*
- [ ] **Remisshantering:**
  - *(🟢 Grannar: vid avvikelse från detaljplan, eller utanför detaljplanerat område)*
  - *(🟢 Från 1 dec 2025: publiceras även på kommunens anslagstavla)*
  - *(🟡 Myndighetsremisser kvarstår som öppen fråga — se 3.4)*
- [ ] **Beslutsmallar** — bevilja/avslå med motivering
- [ ] **Digital signering**

#### 2.2.3 Status & Uppföljning

- [ ] **Ärendestatus i realtid** — *(🟢 Stockholm e-tjänst har detta)*
- [ ] **Notifieringar:**
  - *(🟢 Bekräftelse vid mottagen ansökan)*
  - *(🟢 Underrättelse vid förlängd handläggningstid — lagkrav)*
  - *(🟢 Beslut + överklagandeinfo — lagkrav)*
  - *(🟢 Kompletteringsbegäran)*
- [ ] **Tidslinje/logg** över alla händelser

### 2.3 Tilläggfunktioner (Nice-to-Have)

- [ ] AI-assisterad ifyllnad / förhandsbedömning
- [ ] Automatisk validering av komplett ansökan
- [ ] CAD/PDF-ritningsgranskning (BIM-integration)
- [ ] Kostnadsuppskattning baserat på kommunal taxa
- [ ] E-legitimation (BankID) — *(🟢 Stockholm använder redan detta)*
- [ ] Integration med Boverkets begreppsbank och modellbibliotek

---

## 3. Juridisk Ram & Krav (🟢/🟡 Uppdaterad)

### 3.1 Lagrum (🟢 Verifierat)

| Lag/Författning | Status | Senaste ändring |
|-----------------|--------|-----------------|
| **Plan- och bygglag (2010:900)** | 🟢 Totalreviderad 1 dec 2025 (Lag 2025:974) | 9 kap. 99 § ny version 1 juli 2026 |
| **Plan- och byggförordning (2011:338)** | 🟢 Översedd 2025 | 1 dec 2025 |
| **Boverkets byggregler (nya)** | 🟢 9 fristående föreskrifter, ikraft 1 juli 2025 | BFS 2024:14 (BBR 31) |
| **BBR 31 (energihushållning)** | 🟢 Tillfällig, gäller tills ny energiförfattning finns | 1 juli 2025 |
| **BBR 30 (aktsamhet)** | 🟢 Upphävde BBR 2:3-2:4 | 1 jan 2025 |
| **BBR 29 (gamla)** | 🟢 Gäller övergångsvis t.o.m. 30 juni 2026 | T.o.m. 30 juni 2026 |

**⚠️ VIKTIGT:** Övergångsperiod BBR slutar 1 juli 2026. Efter detta får gamla och nya regler INTE blandas. Byggherre måste välja ett regelverk fullt ut.

### 3.2 Handläggningstider (🟢 Verifierat)

| Ärendetyp | Standardtid | Max förlängning | Lagrum |
|-----------|------------|-----------------|--------|
| **Bygglov / förhandsbesked** | 10 veckor | +10 veckor (engångs) | 9 kap. 99 § PBL |
| **Anmälan (startbesked)** | 4 veckor | +4 veckor (engångs) | 9 kap. PBL |

**Tidsstart räknas från:**
1. Ansökningsdagen
2. Eller dagen komplettering/ändring inkommer
3. Eller dagen Försvarsmakten/MCF svarar
4. Eller dagen brist avhjälpts (om förelagd inom 3 veckor)

**Reduktion av avgift:** Sökande har rätt till avgiftsreduktion om tidsfristen överskrids (prop. 2017/18:210).

**Praktisk verklighet:** Trots lagstadgade 10 veckor rapporterar Stockholm "ovanligt långa väntetider" — upp till 6 månader bara för att få handläggare tilldelad (juni 2026).

### 3.3 Avgifter (🟢 Detaljerat verifierat via Bygglov24, Bygglo, Bygglovsproffsen)

**Bygglovsavgift (kommunal avgift, självkostnadsprincip):**

| Åtgärd | Lägsta | Typiskt (snitt) | Högsta |
|--------|--------|-----------------|--------|
| Anmälan (komplementbyggnad) | 2 500 kr | 3 345 kr | 8 000 kr |
| Tillbyggnad 15-30 m² | 5 000 kr | 10 903 kr | 25 000 kr |
| Tillbyggnad 30-60 m² | 8 000 kr | 18 000 kr | 35 000 kr |
| Carport/Garage ≤40 m² | 4 000 kr | 5 991 kr | 20 000 kr |
| Nybyggnad enbostadshus | 20 000 kr | 45 000 kr | 90 000 kr |
| Rivningslov | 2 000 kr | 5 000 kr | 10 000 kr |

*Källa: Bygglov24 (riksgenomsnitt), Bygglo (275 kommuner, snitt 2026)*

**Geografiska skillnader (tillbyggnad 25 m²):**
- Storstäder (Sthlm/Gbg/Malmö): 12 000 - 25 000 kr
- Medelstora (Uppsala/Linköping): 8 000 - 18 000 kr
- Landsbygdskommuner: 5 000 - 12 000 kr

**Tillkommande avgifter (utöver bygglovsavgift):**
| Post | Kostnad |
|------|---------|
| Situationskarta (från kommun/Lantmäteriet) | 500 - 1 500 kr |
| Arkitekt/ritningar | 8 000 - 80 000 kr |
| Kontrollansvarig (KA) | 5 000 - 40 000 kr |
| Tekniskt samråd | 3 000 - 10 000 kr |
| Startbesked + slutbesked | Oftast inkluderat, annars 2 000-5 000 kr/st |

**Total processkostnad exempel — tillbyggnad 25 m² villa:** ~37 800 kr (avgift + karta + ritningar + KA)

**Avgiftsgrund:** Beräknas per kommun enligt taxa (självkostnadsprincip). Baseras på åtgärdstyp + bruttoarea (BTA). Prisbasbelopp 2025: 56 500 kr används ofta som bas.

🟢 **Avgiftsreduktion:** Sökande har rätt till reduktion om tidsfrist överskrids (prop. 2017/18:210).

🟡 *Notera: Bygglo har avgiftsdata för 275 kommuner — kan användas som datakälla för automatisk avgiftsuppskattning.*

### 3.4 Remissinstanser & Grannunderättelse (🟡 Delvis verifierat)

**Grannar (🟢 Verifierat):**
- Remiss till berörda sakägare (rågrannar) krävs när:
  - Åtgärden avviker från detaljplan
  - Åtgärden sker utanför detaljplanerat område (EJ vid enkel komplementbyggnad/tillbyggnad till 1-2 bostadshus)
- Ingen remiss om "uppenbart att lov inte kan ges"
- 🆕 Från 1 dec 2025: Alla remissärenden publiceras även på kommunens digitala anslagstavla

**Myndigheter (🔴 Behöver ytterligare research):**
- 🟢 Försvarsmakten / Myndigheten för civilt försvar (MCF) — obligatorisk i vissa ärenden (9 kap. 80 § PBL)
- 🟡 Länsstyrelsen — vid riksintresse, strandskydd, etc.
- 🟡 Övriga myndigheter — beroende på ärendetyp och plats

### 3.5 Lovbefriade åtgärder (🟢 Verifierat från PBL 1 dec 2025)

| Åtgärd | Inom detaljplan | Utanför detaljplan |
|--------|----------------|-------------------|
| **Komplementbyggnad** (enskild) | Max 30 m² | Max 50 m² |
| **Komplementbyggnader** (totalt) | Max 45 m² | Max 65 m² |
| **Tillbyggnad** | Max 30 m² brutto+öppenarea | Max 30 m² brutto+öppenarea |
| **Max höjd komplement** | 4 meter | 4,5 meter |
| **Fasadändring** (1-2 bostadshus) | 🟢 Lovfri! | 🟢 Lovfri! |

**Viktiga undantag från lovfrihet:**
- Inom riksintresse för totalförsvaret
- Särskilt värdefulla områden/byggnader (kulturhistoria)
- Nära gräns eller järnväg (< 30m)
- Mindre än 4,5m till tomtgräns (om ej skriftligt medgivande från granne)
- Strandskyddsområden
- 🟡 *Kan behöva anmälan även om lovfritt*

### 3.6 Gällande Detaljplan & ÖP (🟡 Delvis verifierat)

- 🟢 Detaljplaner finns per kommun
- 🟢 Combify har 122 000+ detaljplaner i sin databas
- 🟡 Nationell plattform under utveckling via Boverket + Lantmäteriet (NGP)
- 🟡 *API för detaljplaner: Combify har, Boverket bygger*

---

## 4. Teknisk Arkitektur (Uppdaterad)

### 4.1 Integrationer (🟢/🟡 Uppdaterad)

| Integration | Status | Detalj |
|-------------|--------|--------|
| **Lantmäteriet — Fastighetsinformation** | 🟢 API finns | Direktåtkomst (Hitta/Hämta), Visning, Nedladdning. Fastighetsgränser, ägare, beteckning. |
| **Lantmäteriet — Kartdata** | 🟢 Öppna data (CC0) | Ortofoto via STAC/COG, topografisk data via STAC/GeoPackage eller OGC API Features |
| **Lantmäteriet — NGP** | 🟢 Under utveckling | Nationell Geodataplattform, samverkan med Boverket |
| **Combify API** | 🟢 Finns | Byggrätter (12K), Bygglov (112K), Detaljplaner (122K), 288+ kommuner, 24-48h synk |
| **Boverket — Begreppsbank** | 🟢 Finns | Harmoniserade termer för samhällsbyggnad |
| **Boverket — Modellbibliotek** | 🟢 Finns | Process- och informationsmodeller för digital PBL |
| **BankID** | 🟢 Officiell SDK | Används av Stockholm, krävs för e-legitimation |
| **EUnet4DBP** | 🟢 EU-nätverk | European Network for Digital Building Permits |

### 4.2 Datastruktur — Uppdaterad (🟡 Baserat på research)

**Ansökan:**
- Diarienummer (auto)
- Status (inkommen, komplett, under handläggning, remiss, beslutad, överklagad)
- Datum (ansökan, komplett, beslut)
- Fastighetsbeteckning (FK → Lantmäteriet)
- Fastighetsägare (FK → Lantmäteriet)
- Typ av åtgärd (enum: nybyggnad, tillbyggnad, komplement, ändrad användning, rivning)
- Byggnadsarea (m²), bruttoarea, höjd, våningar
- Detaljplaneområde (enum: inom, utanför, områdesbestämmelser)
- Koordinater (SWEREF99)
- Avstånd till tomtgräns (m)
- KA (kontrollansvarig) — certifierings-ID
- Bilagor: [{typ, fil, status}]
- Remisser: [{typ, mottagare, status, svar}]
- Beslut: {typ, datum, motivering, handläggare}

### 4.3 Tech Stack — oförändrad (🟢 Kan itereras)

| Komponent | Förslag |
|-----------|---------|
| Frontend | React / Next.js |
| Backend | Node.js / FastAPI |
| Database | PostgreSQL + PostGIS |
| Filförvaring | S3-kompatibel |
| Auth | BankID / OIDC |
| Kartmotor | Leaflet / OpenLayers + Lantmäteriet tiles |

---

## 5. Användarflöden (Uppdaterade)

### 5.1 Ansökan (Ansökare) 🟢
1. **Behöver jag bygglov?** → Interaktiv guide baserad på PBL-regler
2. Logga in med BankID
3. Ange fastighetsbeteckning → auto-hämtning från Lantmäteriet
4. Välj åtgärdstyp → systemet visar exakt vilka handlingar som krävs
5. Ladda upp handlingar (guidad checklista)
6. Fyll i ansökningsformulär
7. Ange kontrollansvarig (KA)
8. Betala avgift (om integrerat)
9. Signera & skicka in
10. Bekräftelse + diarienummer + tidsfristinfo

### 5.3 Boverkets officiella process (🟢 10 steg, källa: Boverket Guide för bygglov och byggprocessen)
1. **Fråga byggnadsnämnden** om du behöver bygglov (→ rådgivning i rimlig omfattning)
2. **Skicka in ansökan** + alla handlingar (skriftlig, rätt ritningar)
3. **Byggnadsnämnden gör första granskning** — kontrollerar kompletthet
   - Om ofullständig → föreläggande om komplettering inom viss tid
4. **Remisser till grannar och myndigheter** (se 3.4) + publicering på anslagstavla
5. **Beslut om bygglov** (bevilja/avslå)
6. **Kungörelse i Post- och Inrikes Tidningar** + 4 veckor överklagandetid
7. **Tekniskt samråd** (om KA krävs) — genomgång av kontrollplan och handlingar
8. **Startbesked** — då får bygget påbörjas (tidigast 4v efter kungörelse)
   - Byggsanktionsavgift om man börjar utan startbesked
9. **Arbetsplatsbesök** — minst ett under byggtiden
10. **Slutsamråd + slutbesked** — byggnaden godkänns för användning

*Detta är det kompletta flödet en sökande måste igenom.* 🟡 *Fråga: Hur mycket av detta ska MVP:n täcka? Hela flödet eller bara steg 1-5?*

### 5.4 Komplett B2C-användarresa (🟡 Förslag)
1. **Landning:** "Vad vill du bygga?" → välj åtgärdstyp
2. **Guide:** "Behöver du bygglov?" → smart wizard som kollar PBL-regler
   - Input: fastighetsbeteckning → hämtar detaljplaneinformation
   - Svar: "Ja, du behöver bygglov" / "Nej, men anmälan krävs" / "Nej, helt fritt"
3. **Priskalkyl:** Uppskattad bygglovsavgift för din kommun + kringkostnader
4. **Handlingguide:** Exakt lista på vad du behöver för din åtgärdstyp
5. **Skapa handlingar:** Guidade mallar / integration med ritverktyg
6. **KA-matchning:** Hitta certifierad kontrollansvarig i din kommun
7. **Ansökningsformulär:** Fyll i + ladda upp → validering av kompletthet
8. **Betala:** Integration mot kommunens betalsystem (🟡 framtida)
9. **Signera & skicka:** BankID → vidarebefordra till rätt kommun
10. **Följ ärende:** Statusuppdateringar, tidsfristbevakning, notifieringar

*Denna resa skiljer sig från Bygglovsportalen genom att vara en FAKTISK inlämningsplattform, inte bara en guide.*

---

## 6. Krav & Kompatibilitet

### 6.1 Tillgänglighet (🟢 Krav verifierat)
- **DOS-lagen** (Lag 2018:1937) — implementerar EU-direktiv 2016/2102
- **WCAG 2.1 nivå AA** — bekräftad standard
- Tillsynsmyndighet: **DIGG** (Myndigheten för digital förvaltning)
- Krav: Tillgänglighetsredogörelse + följa WCAG 2.1 AA
- **Gäller för:** Offentliga aktörer + vissa privatfinansierade. Även LPTT (tillgänglighetslagen) gäller för konsumenttjänster från 2025 — PTS tillsyn.
- DIGG granskar 418 webbplatser + 17 appar per år, har hotat med vite (Ockelbo kommun fick vite)
- 🟢 *Om plattformen räknas som offentlig digital service → DOS-lagen gäller. Annars → LPTT (konsumenttjänst).*

### 6.2 Data, Integritet & Offentlighet (🟢 Rättsläge verifierat)

**GDPR vs Offentlighetsprincipen:**
- 🟢 **TF har företräde framför GDPR** (1 kap. 7 § dataskyddslagen, artikel 86 GDPR)
- 🟢 Bygglovsansökningar blir **allmänna handlingar** vid inlämning (2 kap. TF)
- 🟢 Kan inte vägra utlämning enbart pga GDPR
- 🟢 **21 kap. 7 § OSL** — dataskyddssekretess: kan neka utlämning om personuppgiften skulle behandlas i strid med GDPR efter utlämning
- 🟢 **21 kap. 3 § OSL** — sekretess för skyddade personuppgifter (hot/våld). Gäller EJ fastighetsbeteckning.

**Arkiv:**
- 🟢 Arkivlag (1990:782): Allmänna handlingar ska bevaras, gallras enligt gallringsbeslut
- 🟢 Kommunal arkivmyndighet (kommunstyrelsen) ansvarar
- 🟡 *B2C-plattform som mellanhand: fråga om arkivansvar — är plattformen arkivmyndighet eller bara vidarebefordrare?*

**Sekretessmarkering:**
- 🟢 Systemet måste kunna flagga för skyddade personuppgifter (Stockholm varnar för detta)
- 🟢 Fastighetsbeteckning är EJ sekretess — men ägares namn/adress kan vara det

**Praktisk implikation för MVP:**
- Alla inskickade ansökningar är potentiellt offentliga
- GDPR gäller för plattformens egen behandling (sparande, matchning, analys)
- Användardata måste hanteras med samtycke + ändamålsbegränsning

### 6.3 Säkerhet
- BankID för autentisering
- Rollbaserad åtkomstkontroll
- Audit trail (alla åtgärder loggade)
- Kryptering i vila och transit

---

## 7. KPI & Mått (🟡)

- Genomgångstid (ansökan → beslut, per kommun)
- Kompletteringsfrekvens (~50% är baseline)
- Andel digitala vs pappersansökningar
- Användarnöjdhet (NKI — SKR mäter redan detta för kommuner)
- Andel beviljade/avslagna
- Handläggartid per ärende

---

## 8. Riskanalys (Uppdaterad med research)

| Risk | Beskrivning | Sannolikhet | Påverkan |
|------|-------------|------------|----------|
| **Regeländring mitt i utveckling** | BBR-övergång slutar 1 juli 2026. Nya BBR-föreskrifter kan tolkas olika | 🔴 Hög | Kritisk |
| **Kommunal fragmentering** | 290 kommuner, olika processer/taxor/system | 🔴 Hög | Hög |
| **Combify har redan API** | Konkurrent med omfattande databas | 🟡 Medium | Medium |
| **GDPR + allmän handling** | Bygglovsdata är offentlig men innehåller personuppgifter | 🟡 Medium | Hög |
| **Långa handläggartider** | Systemet kan inte påverka kommunernas interna resursbrist | 🟢 Hög | Medium |

---

## 9. Implementation & Faser (Uppdaterad)

### Fas 1: Grundläggande Digital Ansökan (MVP)
- [ ] Interaktiv guide "Behöver jag bygglov?"
- [ ] Digital ansökningsblankett med auto-komplettering
- [ ] Dokumentuppladdning med guidad checklista
- [ ] Fastighetsinformation från Lantmäteriet
- [ ] BankID-inloggning
- [ ] Bekräftelse + diarienummer + tidsfristinfo
- [ ] Grundläggande ärendehantering för handläggare

### Fas 2: Smart Handläggning
- [ ] Automatisk kompletthetskontroll
- [ ] Remisshantering (grannar + anslagstavla)
- [ ] Statusuppföljning för sökande
- [ ] Notifieringar
- [ ] Tidsfristbevakning + automatisk avgiftsreduktion

### Fas 3: Avancerad Integration
- [ ] BIM/ritningsgranskning
- [ ] AI-assisterad förhandsbedömning
- [ ] Full Lantmäteri/NGP integration
- [ ] Kommunalt ekonomisystem (avgifter)
- [ ] EUnet4DBP-kompatibilitet

---

## 10. Research Status — Sammanfattning

### 🟢 Verifierat (Klart)
- [x] Handläggningstider: 10 veckor (+10), anmälan 4 veckor (+4)
- [x] PBL reviderad 1 december 2025
- [x] BBR: 9 nya föreskrifter, övergångsperiod till 1 juli 2026
- [x] Lovbefriade åtgärder (nya gränser)
- [x] Obligatoriska handlingar (lista med 12+ typer)
- [x] Grannunderrättelse: när, hur, anslagstavla
- [x] Lantmäteriet API finns (Direktåtkomst, Visning, Nedladdning)
- [x] Konkurrentlandskap kartlagt (inkl. Bygglo, Bygglov24)
- [x] Boverkets digitaliseringsarbete och officiella 10-stegsprocess
- [x] Avgiftsstruktur (detaljerad tabell, kommunala skillnader)
- [x] DOS-lagen → WCAG 2.1 AA, DIGG tillsyn
- [x] GDPR/allmän handling: TF företräde, 21 kap. 7 § OSL skyddsventil
- [x] Målgrupp: B2C (privatpersoner)

### 🟡 Delvis verifierat (Mer research behövs)
- [ ] Exakta myndighetsremisser per ärendetyp
- [ ] Lantmäteriet API — exakt avtalsmodell/kostnad för kommersiell användning
- [ ] Detaljplane-API (Combify vs NGP — vilket är bäst för MVP?)
- [ ] Arkivansvar: är B2C-plattformen arkivmyndighet eller vidarebefordrare?
- [ ] Integrationspunkter mot kommunala system (Hur tar kommunen emot digital ansökan?)

### 🔴 Kritiska luckor — MÅSTE beslutas före MVP-utveckling
- [x] ~~Unik positionering~~ → ✅ Fastställd: Plattformsoberoende inlämning
- [x] ~~Första målkommun~~ → ✅ Borlänge Kommun (pilot)
- [x] ~~Integrationsteknik~~ → ✅ API/e-post hybrid
- [ ] 🟡 **Affärsmodell:** Hur tjänar MVP:n pengar? (avgift per ansökan? abonnemang? leads?)
- [ ] 🟡 **BBR-övergång slutar 1 juli 2026** — MVP måste byggas mot NYA regler

---

## 11. Referenser & Källor (🟢 Uppdaterade — Round 2)

| Källa | URL | Relevans |
|-------|-----|----------|
| PBL (2010:900) | [riksdagen.se](https://www.riksdagen.se/sv/dokument-och-lagar/dokument/svensk-forfattningssamling/plan-och-bygglag-2010900_sfs-2010-900/) | Huvudlag |
| PBF (2011:338) | [riksdagen.se](https://www.riksdagen.se/sv/dokument-och-lagar/dokument/svensk-forfattningssamling/plan-och-byggforordning-2011338_sfs-2011-338/) | Detaljföreskrifter |
| BBR — Wikipedia | [sv.wikipedia.org](https://sv.wikipedia.org/wiki/Boverkets_byggregler) | Översikt BBR 2025 |
| Boverket — Tidsfrister | [boverket.se](https://www.boverket.se/sv/PBL-kunskapsbanken/lov--byggande/handlaggning/tidsfrister-for-handlaggning/) | Handläggningstider |
| Boverket — Guide bygglov | [boverket.se](https://www.boverket.se/sv/byggande/bygglov-rivningslov-marklov-och-anmalan/guide-bygglov-byggprocess) | Officiell 10-stegsprocess |
| DIGG — DOS-lagen | [digg.se](https://www.digg.se/analys-och-uppfoljning/lagen-om-tillganglighet-till-digital-offentlig-service-dos-lagen) | WCAG 2.1 AA, tillsyn DIGG |
| SKR — GDPR + allmän handling | [skr.se](https://skr.se/funktioner/fragorochsvar/gdpr/fragorochsvargdpr/narnagonbegarutpersonuppgiftersomallmannahandlingarvadgaller.8187.html) | TF företräde framför GDPR |
| JP Infonet — GDPR/OSL | [jpinfonet.se](https://www.jpinfonet.se/kunskap/nyheter4/2023/januari/gdpr-och-utlamning-av-allman-handling-i-form-av-sammanstallningar-med-personuppgifter/) | 21 kap. 7 § OSL dataskyddssekretess |
| Arkivlag (1990:782) | [riksdagen.se](https://www.riksdagen.se/sv/dokument-och-lagar/dokument/svensk-forfattningssamling/arkivlag-1990782_sfs-1990-782/) | Bevarande/gallring |
| Bygglov24 — Kostnader | [bygglov24.se](https://www.bygglov24.se/guide/kostnad) | Avgiftsöversikt per åtgärdstyp |
| Bygglo — Avgifter 275 kommuner | [bygglo.com](https://bygglo.com/bygglovsavgifter/) | Avgiftsdatabas, kommunjämförelse |
| Bygglovsproffsen — Kostnader | [bygglovsproffsen.se](https://bygglovsproffsen.se/vad-kostar-ett-bygglov/) | Total processkostnad |
| Combify API | [combify.com/api](https://combify.com/api) | Konkurrent API, 112K bygglov |
| Bygglovsportalen | [bygglovsportalen.se](https://www.bygglovsportalen.se/) | Konkurrent B2C |
| Stockholm — E-tjänst bygglov | [etjanster.stockholm.se](https://etjanster.stockholm.se/Bygglov/hem/ansokan) | Referensimplementation |
| EUnet4DBP | [eu4dbp.net](https://eu4dbp.net/) | EU digital building permits |

---

## 12. Borlänge Kommun — Pilotkommun (🟢)

> Fastställt: Borlänge är första målkommun för MVP-piloten.

### 12.1 Kommunfakta

| Parameter | Värde |
|-----------|-------|
| Län | Dalarnas län |
| Invånarantal | ~52 000 |
| Bygglov 2025 | 356 ansökningar |
| Median handläggningstid | 4 veckor (mycket snabbt, under rikssnitt) |
| Beviljandegrad | 97% |
| Digital mognad | Hög — "Digitalt först"-strategi |

### 12.2 Avgifter Borlänge (2026)

| Åtgärd | Avgift |
|--------|--------|
| Villa (nybyggnad) | 10 152 kr |
| Tillbyggnad | 5 922 kr |
| Attefall/Anmälan | 2 961 kr |
| Fasadändring | 4 653 kr |

*Källa: brabyggfirmor.se, bekräftat mot bygglov.se + Bygglo*

### 12.3 Digital Infrastruktur

| Resurs | Detalj |
|--------|--------|
| **E-tjänst bygglov** | https://bygg.borlange.se/BO-BYGG-PBL |
| **E-tjänstplattform** | Artvise (artvisemobile.borlange.se) |
| **Generell e-tjänst** | https://artvisemobile.borlange.se/eservice/ |
| **Digital post** | Aktiv sedan 2024 (digital brevlåda) |
| **Digital strategi** | "Digitalt först" — medborgarcentrerad, medarbetardriven |
| **IT-chef** | Peter Sjöberg (peter.sjoberg@borlange.se) |
| **Servicecenter** | 0243-740 00, kommun@borlange.se |
| **Bygglovsguide** | Finns på borlange.se ("Byggplaner? Börja i vår bygglovsguide!") |

### 12.4 Varför Borlänge är en bra pilotkommun

✅ **Hög digital mognad** — Egen e-tjänst, digital post, uttalad "digitalt först"-strategi  
✅ **Snabb handläggning** — 4 veckor median (vs. rikssnitt ~8 veckor). Kort feedback-loop för pilot.  
✅ **Lagom volym** — 356 ansökningar/år. Hanterbar pilot, men tillräckligt för signifikanta data.  
✅ **Egen bygglovsguide** — Kommunen förstår redan värdet av digital vägledning.  
✅ **Hög beviljandegrad (97%)** — Indikerar välfungerande processer.  
✅ **Öppet hus-event** — Nästa 23 sep 2026 på Palladium → möjlighet att presentera/demo:a MVP:n.  
✅ **Egen domän för bygg-e-tjänst** (bygg.borlange.se) — tyder på dedikerad infrastruktur, ej delad med annan verksamhet.  
⚠️ **Sommarstängt** 15 juni – 7 augusti för telefon/möten → planera kontakt efter augusti.

### 12.5 Integrationsstrategi för Borlänge (API/e-post)

**Primär approach: API (om tillgängligt)**
- Undersök om bygg.borlange.se har API-endpoints för ärendeinskick
- Artvise-plattformen kan ha API:er att integrera mot
- Kontakta Peter Sjöberg (IT-chef) för teknisk dialog

**Sekundär approach: E-post (fallback)**
- Generera strukturerad ansökan som PDF + XML/JSON
- Skicka till kommun@borlange.se med ämnesradsmall: `Bygglovsansökan [Fastighetsbeteckning] [Åtgärdstyp]`
- Inkludera alla bilagor som PDF:er
- CC:a sökanden för transparens

**Tertiär approach: Proxy till befintlig e-tjänst**
- Om API saknas: autoifyll Borlänges egna e-tjänstformulär via HTTP POST
- Kräver reverse-engineering av bygg.borlange.se/BO-BYGG-PBL

### 12.6 Action Items för Borlänge-pilot
- [ ] Kontakta Peter Sjöberg (IT-chef) — fråga om API/teknisk integration
- [ ] Kontakta bygglovsenheten — förankra pilotsamarbete
- [ ] Delta på Öppet hus 23 sep 2026 på Palladium (demo-tillfälle)
- [ ] Kartlägga exakta fält/blanketter i bygg.borlange.se/BO-BYGG-PBL
- [ ] Undersöka Artvise plattformens API-kapacitet
- [ ] Sätta upp testmiljö för Borlänge-inlämning
