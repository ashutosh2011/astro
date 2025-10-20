# Astro MVP Backend — Spec V3 (Final for Dev AI)

> **Goal**: Ship an MVP that produces **credible, time-bound Jyotish predictions** with **one-question-at-a-time** UX. Includes: deterministic calculations (sidereal/Lahiri), a single focused LLM pass per user question, and persistence so users can return and continue.

---

## 0) Scope (MVP)

* **You do**: D1 (Rāśi), Whole Sign houses, ascendant, planetary longitudes, nakshatra+pada, **Vimśottari (MD/AD)**, current **Saturn/Jupiter/Rahu-Ketu transits**, **D9 (signs only)**, **SAV (natal only)**, curated **11 yogas/doshas**, coarse **Bhāva Bala**, optional **sensitivity check**.
* **You don’t** (yet): D10/D7/D12, BAV/Shadbala, RAG/KB, matchmaking, remedies, payments.

---

## 1) High-Level Architecture

**Services**

1. **API** (FastAPI) — auth, validation, endpoints.
2. **Calc Engine** — Swiss Ephemeris adapter + Jyotish logic.
3. **LLM Orchestrator** — one call per user question, strict JSON.
4. **Storage** — Postgres (profiles, calc snapshots, Q&A predictions, sessions).
5. **Cache** — Redis (idempotent calc reuse, 24h TTL).

**Flow**

```
Client -> /auth -> /profiles -> /compute (calc_snapshot)
User asks question -> /predict/question (uses calc + question) -> LLM -> JSON answer
Persist everything -> return to client
```

---

## 2) Inputs & Validation

**Required**

```
name, gender, dob(YYYY-MM-DD), tob(HH:MM[:SS]), tz(IANA), place,
lat (-90..90), lon (-180..180), altitude_m (default 0)
```

**Optional**

```
uncertainty_minutes (0/5/10), ayanamsa(default Lahiri), house_system(default WholeSign)
```

**Rules**: Reject invalid tz/lat/lon; date range 1900–2100; tz required; no runtime geocoding.

---

## 3) Calculations (MVP Set)

### 3.1 Meta & Panchānga

* `ayanamsa=Lahiri`, `house_system=WholeSign`, `timezone`, `dst_used`, `ephemeris='SwissEph'`, `calc_timestamp`, `ruleset_version`.
* Panchānga at birth: weekday, **tithi**, **nakshatra+pada**, yoga, karana.
* Sunrise/sunset (display), JD (UT/TT), ΔT.

### 3.2 D1 & Houses

* **Ascendant**: sign, deg (abs & in-sign), nakshatra+pada.
* **Planets (Sun..Ketu)**: sidereal longitude (abs+in-sign), nakshatra+pada, `retro`, `combust`.
* **Houses (1–12)**: sign; cusp_deg for 1st (others implied by Whole Sign).
* **Planet→house** mapping.

### 3.3 Dignities & Aspects

* Dignity per planet: `Exalted|Debilitated|Own|Mooltrikona|Friend|Neutral|Enemy`.
* Combust orbs (config): Merc 12°, Venus 10°, Mars 17°, Jupiter 11°, Saturn 15°, Moon 12°.
* Parāśari aspects: universal 7th; Mars(4/8), Jupiter(5/9), Saturn(3/10).
  Emit `{from, to, type, orb_deg, strength_0_1}` for planet→planet and planet→house.

### 3.4 Vimśottari (MD/AD) — **Included**

* Compute full MD cycle; expose **current MD/AD** and **next_12m_ads** (see rule below).
* **Next-12-months rule**:

  * Always include **current AD** (even if it extends >12m; truncate end to `now()+12m`).
  * If the next AD starts within 12m, include it (truncate if needed).

### 3.5 Transits (Gochar) — Now

* Sidereal **Saturn, Jupiter, Rahu, Ketu**: sign + `house_from_lagna` + `house_from_moon`.
* Flags: `sade_sati_phase`, `jupiter_house_from_moon`, `rahu_ketu_axis_houses_from_lagna`.

### 3.6 D9 (Navāṁśa) — compact

* Ascendant **sign**; planet **signs only**.
* **d9_better** rule (deterministic):
  Assign dignity tiers: `Exalted=5, Own=4, Mooltrikona=3, Friend=2, Neutral=1, Enemy=0, Debilitated=-1`.
  `d9_better = (tier_D9 > tier_D1)`.

### 3.7 SAV (Ashtakavarga) — **Natal only**

* `sav`: 12 ints (Aries→Pisces).
* Default threshold: `sav_good_threshold = 30`.
* **Usage note**: Natal SAV moderates *baseline strength* of signs/houses (e.g., career if 10th sign SAV > 30).

### 3.8 Curated Yogas/Doshas (11)

**Benefic (6)**

1. **Gaja-Kesari**
2. **Pancha-Mahapurusha** (Mars/Mercury/Jupiter/Venus/Saturn in own/exalt in 1/4/7/10)
3. **Raj-Yoga (simple)**: 9th lord + 10th lord conjunct/aspect/mutual reception
4. **Dhana-Yoga (simple)**: 2nd lord + 11th lord conjunct/aspect
5. **Viparīta-Rāja**: 6/8/12 lords in 6/8/12 (benefic outcome)
6. **Neecha-bhanga** (classical cancellation conditions)
   **Doshas (5)**
7. **Manglik (Strict)**: Mars in 1/2/4/7/8/12 from Lagna
8. **Manglik (Lenient)**: Mars in 1/2/4/7/8/12 from Moon
9. **Kal-Sarpa (Strict)**: all seven planets between Rahu and Ketu
10. **Kal-Sarpa (Loose)**: all seven planets within Rahu–Ketu 180° arc
11. **Kemadruma (Basic)**: Moon isolated (no planets in 2nd/12th; simple check)

Emit: `{name, present: bool, reason: short_string}`.

### 3.9 Bhāva Bala (coarse, deterministic)

```
Start 0.50
+0.15 if house_lord dignity ≥ Friend AND NOT combust
+0.10 if house_lord aspected by Jupiter OR Venus (any Parāśari aspect)
-0.10 if house_lord dignity ≤ Enemy OR combust
-0.10 if ≥3 malefics (Mars/Saturn/Rahu/Ketu) occupy the house
Clamp to [0.00, 1.00]
```

### 3.10 Sensitivity (optional)

If `uncertainty_minutes > 0`, recompute at `tob ± n`:

```json
"sensitivity_report": {
  "uncertainty_minutes": 5,
  "lagna_flips": false,
  "lagna_original_sign": "Leo",
  "lagna_if_minus": "Leo",
  "lagna_if_plus": "Virgo",
  "moon_sign_flips": false,
  "d9_asc_flips": false,
  "dasha_boundary_risky": false,
  "dasha_boundary_reason": "",
  "house_changes": [
    {"planet": "Mars", "house_original": 10, "house_if_plus": 10, "house_if_minus": 10}
  ]
}
```

---

## 5) LLM Integration — **How “Predict” Works**

### 5.1 Conversational (one-question-at-a-time UX)

* The user can ask **any natural question**, e.g.
  “Will I get a new job soon?”, “How are my finances this year?”,
  “When is marriage possible?”, “Is travel abroad shown?”, or any follow-up like
  “What kind of job is most suitable?”

* Backend → `/predict/question`

  1. Loads latest `calc_snapshot` (or triggers `/compute` if missing).
  2. Uses a **light topic classifier** (career / marriage / health / travel / general) to scope context.
  3. Builds a **focused payload** using only relevant chart fields.
  4. Calls the **OpenAI LLM once** per question, requesting **strict JSON**.
  5. Stores the full Q&A (conversation-aware if follow-up).
  6. Returns the structured answer to UI.

* Each follow-up question reuses the **same profile + calc_snapshot** and appends previous Q&A context (last 1–2 turns) so continuity is maintained without re-computing charts.

---

### 5.2 Input to LLM (content fields only; no prompt text here)

**Common fields (always included)**

```json
{
  "user_profile": { "name": "string", "gender": "string", "tz": "string", "place": "string" },
  "calc_summary": {
    "ascendant": "...",
    "d1": {
      "planets": [ {"name":"Sun","sign":"...","deg":...,"dignity":"...","retro":false,"combust":false,"house":...}, ... ],
      "houses": [ {"num":1,"sign":"..."}, ... ],
      "aspects": [ {"from":"Mars","to":"Moon","type":"8th","strength":0.7} ]
    },
    "d9": { "asc_sign":"...", "planet_signs":{...}, "d9_better":{...} },
    "yogas": [ {"name":"Raj-Yoga","present":true}, ... ],
    "bhava_bala": [0.72,0.54,...],
    "timing": {
      "current_md":"Moon","current_ad":"Mars",
      "next_12m_ads":[{"start":"2025-10-12","end":"2026-03-18","md":"Moon","ad":"Mars"}]
    },
    "transits_now": {
      "saturn_house_from_lagna":7,"jupiter_house_from_lagna":10,
      "rahu_ketu_axis_from_lagna":[2,8],"sade_sati_phase":"none"
    },
    "sav": [28,31,34,...],
    "sensitivity": {"lagna_flip":false,"moon_flip":false,"dasha_boundary_risky":false}
  },
  "conversation_context": [
    {"role":"user","question":"previous question text"},
    {"role":"assistant","answer_summary":"short summary of previous answer"}
  ],
  "question": "user's current free-text question",
  "topic": "career|marriage|health|travel|general",
  "time_horizon": {"months_min":3,"months_max":12},
  "style_constraints": {
    "no_remedies": true,
    "no_fatalism": true,
    "show_evidence": true,
    "use_time_windows": true,
    "brevity_target_tokens": 350
  }
}
```

**Extra topic clues** (included only when relevant)

* **Marriage**

  ```json
  {
    "marriage_indicators": {
      "seventh_lord": "Venus", "seventh_lord_sign": "Libra", "seventh_lord_dignity": "Own",
      "venus_sign": "Taurus", "venus_dignity": "Own",
      "d9_asc_sign": "Sagittarius", "d9_venus_sign": "Pisces",
      "manglik_status_strict": false, "manglik_status_lenient": true
    }
  }
  ```

* **Career**

  ```json
  {
    "career_clues": {
      "tenth_lord": "Saturn", "tenth_lord_sign": "Capricorn", "tenth_lord_dignity": "Own",
      "second_lord": "Mercury", "eleventh_lord": "Jupiter",
      "career_yogas_present": ["Raj-Yoga","Pancha-Mahapurusha"],
      "jupiter_transit_house_from_lagna": 10,
      "saturn_transit_house_from_lagna": 7
    }
  }
  ```

* **Health**

  ```json
  {
    "health_clues": {
      "sixth_lord": "Mars", "sixth_lord_sign": "Scorpio", "sixth_lord_dignity": "Own",
      "eighth_lord": "Jupiter", "twelfth_lord": "Mercury",
      "saturn_transit_from_moon": "12th",
      "mars_moon_relation": "conjunction",
      "vitality_hint": { "sun_lagna_separation_deg": 32 }
    }
  }
  ```

---

### 5.3 Expected LLM Output (strict JSON)

```json
{
  "topic": "career",
  "answer": {
    "summary": "≤150 words concise reply to user's specific question",
    "time_windows": [
      {"start":"YYYY-MM-DD","end":"YYYY-MM-DD","focus":"promotion/role-shift","confidence":0.0-1.0}
    ],
    "actions": ["2–4 actionable suggestions"],
    "risks": ["0–2 short cautions (optional)"],
    "evidence": [
      {"calc_field":"timing.current_md","value":"Moon","interpretation":"Current MD activates career house"},
      {"calc_field":"transits.jupiter_house_from_lagna","value":10,"interpretation":"Jupiter supporting career growth"}
    ],
    "confidence_topic": 0.0-1.0
  },
  "confidence_overall": 0.0-1.0
}
```

**Server-side confidence finalization**

```
overall = mean(confidence_topic)
-0.10 if sensitivity.dasha_boundary_risky
-0.05 if sensitivity.lagna_flip OR sensitivity.moon_flip
-0.10 if uncertainty_minutes > 0
Clamp [0,1]
```

---

### 5.4 LLM Provider 

```yaml
llm_provider: openai
model: gpt-5            # or gpt-4o-mini for cost optimisation
temperature: 0.3
top_p: 1
presence_penalty: 0
frequency_penalty: 0
max_tokens: 600
seed: 7                   # deterministic reproducibility
response_format: { type: "json_object" }
timeout_ms: 15000
retry_on_json_parse_failure: 2
retry_on_429_or_5xx: 2
```

**Request construction**

```json
{
  "model": "gpt-5",
  "temperature": 0.3,
  "max_tokens": 600,
  "response_format": { "type": "json_object" },
  "seed": 7,
  "messages": [
    {"role": "system", "content": "You are an expert Vedic astrologer. Reply ONLY in valid JSON matching the given schema. No text outside JSON."},
    {"role": "user", "content": "<payload JSON from above>"}
  ]
}
```

**Validation & Retries**

1. Parse response → validate against topic schema.
2. On failure → retry (max 2) with the same payload + extra system note “Return only valid JSON.”
3. On final failure → return `LLM_JSON_PARSE_FAILED (500)` and log scrubbed output.

---

**Result:**
Users can now chat naturally (“What about finances?”, “Any health issues next year?”),
each question triggers one OpenAI LLM call grounded in their stored chart data,
and responses stay structured, auditable, and consistent.


---

## 6) API Endpoints

### Auth

* `POST /auth/register` {email, password}
* `POST /auth/login` → JWT
* `POST /auth/logout`

### Profiles & Sessions

* `POST /profiles` (create)
* `GET /profiles/:id`
* `PATCH /profiles/:id`
* `GET /profiles` (list)
* `GET /profiles/:id/history` (calc snapshots + Q&A timeline)
* `PATCH /sessions/:id` (update onboarding step, last calc/prediction)

### Compute

* `POST /compute` {profile_id **or** inline birth data} → `calc_snapshot_id`

  * Idempotent via `input_hash = sha256(profile_input + calc_config + ruleset_version)`
  * Recompute triggers:

    * Profile edited
    * `ruleset_version` **or** `ephemeris_version` bumped

### Predict (Q&A)

* `POST /predict/question`

  ```
  {
    "profile_id": "...",
    "question": "free text",
    "time_horizon_months": 12   // optional, default 12
  }
  ```

  **Returns**: LLM JSON (topic + answer), `prediction_id`.
  Also persists original question, topic, inputs used, and LLM result.

* `GET /predictions/:id`

### Health/Admin

* `GET /healthz`, `GET /readyz`
* `DELETE /admin/cache/reset/{profile_id}` (admin-only)

---

## 7) Storage (Postgres)

```
users(id, email, pw_hash, created_at)

profiles(id, user_id, name, gender, dob, tob, tz, place, lat, lon, altitude_m,
         uncertainty_minutes default 0, created_at, updated_at)

calc_snapshots(id, user_id, profile_id, input_hash, ayanamsa, house_system,
               ephemeris_version, payload_json(compressed), created_at)

predictions(id, user_id, profile_id, calc_snapshot_id,
            question, topic, llm_model, llm_params_json,
            result_json, confidence_overall, created_at)

sessions(id, user_id, profile_id, last_calc_snapshot_id, last_prediction_id,
         onboarding_step, updated_at)
```

**Indexes**: `calc_snapshots(input_hash)`, `predictions(profile_id, created_at)`

**Encrypted at rest**:

* `profiles.name`, `profiles.dob`, `profiles.tob`
* (optional) `profiles.lat`, `profiles.lon`
  **Plain**: `tz`, `place`, `gender`, IDs/foreign keys.

---

## 8) Rate Limits & Errors

**Per user**

```
/compute: 10/min
/predict/question: 5/min
other endpoints: 60/min
Burst: 2x for 10s
```

**Error codes**

```
INVALID_TIMEZONE (400)
BIRTH_DATE_OUT_OF_RANGE (400)
MISSING_LAT_LON (400)
EPHEMERIS_LOAD_FAILED (503)
LLM_JSON_PARSE_FAILED (500)   # log and retry once
LLM_TIMEOUT (504)
INPUT_HASH_COLLISION (500)     # log immediately
```

---

## 9) Observability & QA

**Logs**: `request_id`, `user_id`, `profile_id`, timings per calc stage, `llm_duration_ms`, `input_hash`.
**Metrics**: `calc_duration_ms`, `llm_first_pass_json_valid`, `llm_retry_count`, `llm_output_tokens`, `evidence_field_hit_rate`, `errors_by_code`.
**Golden Seeds (5)** with frozen outputs (tolerance ±0.1° planets, ±0.05° Asc), MD/AD boundaries checked, one sensitivity case.
**Sanity**: angle normalization, Whole Sign consistency, dasha continuity.
**Cache**: Redis by `input_hash`, TTL 24h.

---

## 10) What the UI Gets Back (per question)

* `topic`, `answer.summary`, `answer.time_windows[]`, `answer.actions[]`, `answer.risks[]?`,
  `answer.evidence[]` (with `{calc_field, value, interpretation}`),
  `answer.confidence_topic`, `confidence_overall`, `sensitivity_notice?`.

---

## 11) Why This Is “Accurate Enough” (for MVP)

* **Dashā (MD/AD) + Jupiter/Saturn/Rahu-Ketu transits** anchor **timing**.
* **D9 signs + curated yogas + SAV** modulate **quality/strength**.
* **Bhāva Bala** provides deterministic house weight.
* **Sensitivity flags** prevent over-assertion when TOB is shaky.
* Single-topic **LLM JSON** responses with **evidence pointers** keep outputs checkable and consistent.

---

### Ready-to-Code Checklist (we already fixed the must-haves)

* D9 improvement rule ✅
* Bhāva Bala formula ✅
* AD next-12m logic ✅
* Sensitivity schema ✅
* Topic-specific “clues” payload ✅
* Confidence formula ✅
* Rate limits & error codes ✅
* Yogas enumerated (11) ✅
* LLM JSON-mode provider notes ✅

---

## TL;DR

* Compute once (`/compute`), answer **one user question at a time** (`/predict/question`) with a **focused payload**.
* Persist **profiles**, **calc snapshots**, and **Q&A predictions** so users can return and continue.
* Keep it deterministic, fast, and checkable with **evidence fields**.

This is your **final MVP spec**—hand it to the Dev AI and build.
