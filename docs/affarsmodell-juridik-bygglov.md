# Affärsmodell & Juridik — Bygglov B2C MVP

> Skapad: 2026-06-19 | Analys av lämpliga affärsmodeller och juridiska förutsättningar

---

## Del 1: Affärsmodell

### 1.1 Marknadsstorlek & Värde

| Parameter | Värde | Källa |
|-----------|-------|-------|
| Årliga bygglovsansökningar i Sverige | ~72 000 (analyserade av Bygglov.se) | Bygglovsrapporten 2026 |
| Genomsnittlig bygglovsavgift | ~10 000 kr | Snitt riket |
| Genomsnittlig processkostnad (inkl. ritningar, KA) | ~38 000 kr | Bygglov24, Bygglo |
| Andel B2C-ansökningar (uppskattat) | ~60% = ~43 000/år | Uppskattning |
| Adresserbar marknad (B2C, vill göra det själva) | ~15-20 000 ansökningar/år | Uppskattning |
| **Total transaktionsvolym B2C** | **~200-400 Mkr/år** | Bygglovsavgifter + kringtjänster |

### 1.2 Rekommenderad Affärsmodell: Hybridmodell (3 intäktsströmmar)

#### Ström 1: Transaktionsavgift per ansökan (PRIMÄR)
**"Betala när du skickar in"**

| Ansökningstyp | Pris (MVP) | Pris (skala) |
|---------------|-----------|--------------|
| Enkel (t.ex. fasadändring, carport) | **495 kr** | 395 kr |
| Medel (tillbyggnad, komplementbyggnad) | **995 kr** | 795 kr |
| Komplex (nybyggnad villa) | **1 995 kr** | 1 495 kr |

**Varför denna modell:**
- Användaren betalar bara när värde levereras (slipper prenumerationsbarriär)
- Naturlig koppling till framgång — du betalar för att få hjälp att skicka in
- Priset är lågt relativt den totala processkostnaden (~2-5% av 38 000 kr)
- Psykologiskt lätt att motivera: "Kostar mindre än en timmes arkitektkonsultation"
- Enkel att skala — en transaktion per användare

**Jämförbara prisreferenser:**
- SigneraDokument.se: 49 kr per signering (B2C transaktion)
- Deklarationstjänster: 149-499 kr per deklaration
- BankID-signeringstjänster: 49-149 kr per signatur

#### Ström 2: Premium-funktioner (SEKUNDÄR)
**Freemium-modell där grundansökan är gratis, men avancerade funktioner kostar**

| Funktion | Gratis | Premium |
|----------|--------|---------|
| "Behöver jag bygglov?"-guide | ✅ | ✅ |
| Avgiftskalkylator | ✅ | ✅ |
| Kommunjämförelse | ✅ | ✅ |
| Mallar för handlingar | ❌ | ✅ (99 kr/mån) |
| Autoifyllnad från Lantmäteriet | ❌ | ✅ |
| Smart kompletthetskontroll | ❌ | ✅ |
| Faktisk inlämning | ❌ | ✅ (engångsavgift) |
| Tidsfristbevakning | ❌ | ✅ |
| Ärendestatus | ❌ | ✅ |
| Expert-kontakt (KA-matchning) | ❌ | ✅ (per lead) |

#### Ström 3: Expert-marknadsplats (FRAMTIDA, Fas 3)
**Inspirerad av Bygglov.se: experter betalar för synlighet**

| Intäkt | Modell | Uppskattad intäkt/expert/mån |
|--------|--------|------------------------------|
| Verifierad profil | Månadsabonnemang | 299-999 kr/mån |
| Lead-förmedling | Per kvalificerad lead | 99-299 kr/lead |
| Prioriterad listning | Premium-placement | +199 kr/mån |

*Notera: Detta är Fas 3 — Bygglov.se har redan 8 experter i Borlänge till denna modell. Vi kan konkurrera på integration snarare än matchning.*

### 1.3 Intäktsscenarier

#### Scenario A: Låg penetration (år 1)
- 200 ansökningar via plattformen
- Snittpris: 795 kr
- **Intäkt: ~159 000 kr** (enbart transaktioner)

#### Scenario B: Medel penetration (år 2, Borlänge + 5 kommuner)
- 1 500 ansökningar
- Snittpris: 795 kr + 20% premiumkonvertering (99 kr/mån × 12 = 1 188 kr/år × 300 användare)
- **Intäkt: ~1,2 Mkr** (transaktioner) + **~356 000 kr** (premium) = **~1,55 Mkr**

#### Scenario C: Skala (år 3, 20+ kommuner)
- 8 000 ansökningar
- Transaktioner: 8 000 × 695 kr = 5,56 Mkr
- Premium: 1 600 abonnenter × 1 188 kr = 1,9 Mkr
- Experter: 100 experter × 499 kr/mån × 12 = 599 000 kr
- **Total intäkt: ~8 Mkr/år**

### 1.4 Kostnadsstruktur (MVP-fas)

| Kostnadspost | Månadskostnad | Årskostnad |
|-------------|---------------|------------|
| Hosting/infra (AWS/Vercel) | 2 000 kr | 24 000 kr |
| Lantmäteriet API (uppskattat) | 5 000 kr | 60 000 kr |
| BankID-integration | 3 000 kr | 36 000 kr |
| Domän/SSL/övrigt | 500 kr | 6 000 kr |
| Underhåll/utveckling | 15 000 kr | 180 000 kr |
| **Total** | **~25 500 kr/mån** | **~306 000 kr/år** |

**Break-even vid ~385 ansökningar/år** (Scenario A-nivå).

### 1.5 Varför INTE rena prenumerationer?
- Lågfrekvent användning — de flesta gör 0-1 bygglovsansökningar per år
- Hög churn — ingen kommer prenumerera månad efter månad efter att bygglovet är klart
- Transaktionsmodellen passar användningsmönstret bättre
- Premium-månadsabonnemang fungerar endast för proffsanvändare (arkitekter, KA)

---

## Del 2: Juridik

### 2.1 Huvudfynd — Fullmakt & Ombud

**🟢 POSITIVT BESKED: Det finns redan ett ramverk för digitala fullmakter i bygglovsprocessen.**

**Lagstöd:**
- **Förvaltningslag (2017:900) 15 §** — En myndighet får begära att ett ombud styrker sin behörighet genom en skriftlig eller muntlig fullmakt. Fullmakten ska innehålla ombudets namn och uppdragets omfattning.
- Myndigheten FÅR begära fullmakt — inte MÅSTE. Det är upp till kommunens byggnadsnämnd.
- Om ombudet inte styrker behörigheten får myndigheten förelägga om detta.

**Boverkets arbete:**
- Boverket HAR redan tagit fram en **standardfullmaktsmall** specifikt för lov- och byggprocessen
- Mallen finns tillgänglig via **Mina ombud** — en digital fullmaktstjänst
- Boverket skriver: *"Det är inte självklart vem som har rätt att behandla eller ta del av informationen. Även om det är möjligt för vem som helst att söka bygglov varsomhelst, får inte vem som helst ändra en befintlig ansökan. Därför finns det ett behov av digitala fullmakter."*

**Vad detta betyder för MVP:n:**
1. ✅ Det är **fullt lagligt** att lämna in en bygglovsansökan som ombud
2. ✅ Boverket har redan tänkt på digitala fullmakter för detta ändamål
3. ✅ Det finns en standardmall att använda
4. ⚠️ Rättsläget: Kommunen **får** begära fullmakt men måste inte. Vissa kommuner kanske inte accepterar digital fullmakt utan kräver papper.
5. ⚠️ Praktisk risk: Borlänge kan neka digitala fullmakter. Detta måste testas i praktiken.

### 2.2 MVP:ns juridiska position

MVP:n agerar som **tekniskt ombud** — en digital mellanhand som:
1. Hjälper användaren fylla i ansökan (information/guidning)
2. Låter användaren signera med BankID (fullmaktsbekräftelse)
3. Skickar in ansökan + fullmakt till kommunen

**Detta är en standardmodell som redan används av:**
- Skatteverket (deklarationsombud via BankID)
- Banker (fullmaktshantering digitalt)
- Bygglovskonsulter (lämnar in för kunders räkning — detta görs redan idag, bara inte digitalt)

### 2.3 Implementationskrav för fullmakt

```
Användarflöde:
1. Användare fyller i ansökan på plattformen
2. Användare granskar och godkänner
3. Systemet genererar digital fullmakt (enligt Boverkets mall via Mina ombud)
4. Användare signerar fullmakten med BankID
5. Systemet skickar ansökan + signerad fullmakt till kommunen
6. Kommunen registrerar ärendet med användaren som byggherre och plattformen som ombud
```

### 2.4 Risker & Mitigations

| Risk | Nivå | Mitigation |
|------|------|------------|
| Kommun nekar digital fullmakt | 🟡 Medium | Fallback: generera PDF-fullmakt för utskrift + fysisk signatur. Erbjud "printa och posta"-alternativ. |
| Kommun saknar digitalt mottagningssystem | 🟡 Medium | E-post + strukturerad PDF som fallback. Borlänge har redan Artvise — bedöms låg risk |
| GDPR — plattformen hanterar personuppgifter som ombud | 🟢 Låg | Standard GDPR-krav. Inget utöver normala dataskyddsrutiner. |
| Användaren missförstår och tror att plattformen ÄR kommunen | 🟡 Medium | Tydlig disclaimer: "Vi är en digital tjänst, inte en myndighet. Det är kommunen som fattar beslutet." |
| Kommunen kommunicerar direkt med användaren istället för via plattformen | 🟢 Låg | Plattformen vidarebefordrar bara — ärendestatus läses från kommunens system eller uppdateras manuellt. |

### 2.5 Rekommenderad Legal Setup

**Steg 1: Före MVP-lansering**
- [x] Analysera Boverkets fullmaktsmall (redan gjord)
- [ ] Integrera med Mina ombuds API för digital fullmakt
- [ ] Upprätta användarvillkor (terms of service) som klargör plattformens roll
- [ ] Förbered PDF-baserad fullmakt som fallback
- [ ] Kontakta Borlänge kommun för tekniskt godkännande

**Steg 2: Under pilot (Borlänge)**
- [ ] Testa digital fullmakt med 5-10 pilotanvändare
- [ ] Få feedback från Borlänges bygglovsenhet
- [ ] Justera fullmaktsformat vid behov

**Steg 3: Skala**
- [ ] Kontakta Boverket för vägledning om nationell standard
- [ ] Samarbeta med GovTech Sweden för synlighet/legitimitet
- [ ] Standardisera fullmakter för alla kommuner

### 2.6 Andra juridiska aspekter att beakta

| Aspekt | Status | Åtgärd |
|--------|--------|--------|
| **Användarvillkor** | ⚠️ Ej skapade | Måste finnas före lansering |
| **Integritetspolicy (GDPR)** | ⚠️ Ej skapad | Krävs, särskilt pga. personuppgifter i ansökningar |
| **Cookie-policy** | ⚠️ Ej skapad | Krävs enligt LEK |
| **Tillgänglighetsredogörelse** | ⚠️ Ej skapad | Kan krävas enligt DOS-lagen |
| **Konsumenträtt (distansavtal)** | 🟡 | Gäller vid försäljning till konsument (ångerrätt 14 dagar) |
| **Penningtvätt** | 🟢 Ej relevant | Ingen betalningsförmedling |
| **Försäkring** | 🟡 | Ansvarsförsäkring rekommenderas om plattformen anses ge "rådgivning" |

---

## Del 3: Rekommendation

### 🚀 Go-to-market strategi

**Fas 0 (augusti 2026): Förankring**
1. Kontakta Peter Sjöberg (IT-chef Borlänge) — teknisk dialog
2. Kontakta bygglovsenheten Borlänge — processgodkännande
3. Bygg fungerande MVP (guide + kalkylator + ansökan för en åtgärdstyp)

**Fas 1 (september 2026): Pilot**
1. Demo på Öppet hus 23 sep (Palladium, Borlänge)
2. 10-20 pilotanvändare via personlig rekrytering
3. 1 åtgärdstyp (tillbyggnad) → 1 kommun (Borlänge) → 1 kanal (API/e-post)

**Fas 2 (oktober-december 2026): Iterera**
1. Analysera pilot: kompletteringsfrekvens, användarfeedback, tekniska problem
2. Bygg ut till fler åtgärdstyper (carport, garage, komplementbyggnad)
3. Förbered expansion till ytterligare kommuner

### 💰 Affärsmodellsrekommendation

| Prioritet | Intäktsström | Timing | 
|-----------|-------------|--------|
| **1:a** | Transaktionsavgift (495-1995 kr) | Fas 1 — Direkt från pilot |
| **2:a** | Premium-funktioner (99 kr/mån) | Fas 2 — När basen fungerar |
| **3:e** | Expert-marknadsplats | Fas 3 — När volym finns |

### ⚖️ Juridisk rekommendation

**Kör.** Det finns inget juridiskt hinder för att agera som digitalt ombud för bygglovsansökningar. Boverket har redan banat vägen med sin fullmaktsmall. Nyckeln är att få Borlänge kommun att acceptera digital fullmakt — och det är en relationsfråga, inte en juridisk fråga.

**Prioritera att kontakta Borlänge direkt efter semestern (7 augusti)** för att:
1. Få tekniskt godkännande för API/e-post-inlämning
2. Få processgodkännande för digital fullmakt
3. Boka demo-tid på Öppet hus 23 september