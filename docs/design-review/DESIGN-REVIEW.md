# Capstone Design Review

**Course:** CS-AI-2025 — Building AI-Powered Applications | Spring 2026
**Assessment:** Design Review — 10 points
**Due:** Thursday 2 April 2026 at 23:59 Georgia Time
**Submission:** Team repo (see required tree in Lab 3 README) + Google Form (link on Teams)
**Team:** Binary Bros & Byte Queen
**Project:** Cost Accounting Automation
**Repo:** https://github.com/team-binary-bros-byte-queen-kiu-2026/Cost_Accounting_Automation

---

## Section 1 — Problem Statement and Users

*Built on your Lab 2 proposal Section 1. Sharpen to a single precise sentence.*

**Problem statement (one sentence):**
Format: "[Specific user group] struggle to [do thing] because [root cause], which means [consequence]."

```
[fill in]
```

**Who exactly has this problem:**
Not a demographic — a specific person in a specific situation. If you have spoken to one real potential user, describe that conversation briefly.

```
[fill in]
```

**What they do today without your solution:**

```
[fill in]
```

**Why AI is the right tool:**
What does AI enable that a conventional approach cannot? One paragraph.

```
[fill in]
```

---

## Section 2 — Proposed Solution and Features

*Built on your Lab 2 proposal Section 2.*

**Solution summary (3–5 sentences):**

```
[fill in]
```

**Core features:**

| Feature | AI-powered? | The AI differentiator? |
|---|---|---|
| | | |
| | | |
| | | |

**The one feature that would not exist without AI:**

```
[fill in — one sentence]
```

---

## Section 3 — Measurable Success Criteria

*New in Lab 3. This section did not exist in your Lab 2 proposal.*

A measurable criterion has three parts: what you measure, how you measure it, and a target number. "Users will be satisfied" is not a criterion. "The vision extraction achieves greater than 85% field accuracy on our 20-item test set" is.

Write at least two criteria.

| Criterion | How you will measure it | Target |
|---|---|---|
| | | |
| | | |

---

## Section 4 — Architecture

*Your Lab 2 proposal had a prose description. The Design Review requires a visual diagram.*

**Architecture diagram:**
Commit your diagram as `docs/design-review/architecture-diagram.png` and reference it here.

```
See: docs/design-review/architecture-diagram.png
```

The diagram must show: frontend, backend, AI model(s), storage layer, and arrows showing data direction. Use the checklist in `templates/architecture-template.md` to verify before committing.

**Technology stack:**

| Layer | Technology | Why |
|---|---|---|
| Frontend | | |
| Backend | | |
| Primary AI model | | |
| Secondary model (fallback) | | |
| Storage | | |
| Hosting | | |

**Multimodal capabilities (check all that apply now or planned by Week 8):**

- [ ] Text generation
- [ ] Vision / image understanding (Lab 2)
- [ ] Image generation (planned Lab 3 / Week 3)
- [ ] Audio TTS or STT
- [ ] Document / PDF understanding
- [ ] Function calling
- [ ] RAG

---

## Section 5 — Prompt and Data Flow

*New in Lab 3. Trace one specific user action step by step.*

Choose your most important AI feature. Trace the complete path from user input to user-visible output.

```
User action:
  [what the user does — types, uploads, clicks]

Preprocessing:
  [what happens to the input before the API call]

Prompt construction:
  [describe the system prompt, how user input is inserted, what context is added]

API call:
  [which model, via OpenRouter or direct, what parameters]

Response parsing:
  [how you extract what you need from the response]

Confidence / validation:
  [how you decide whether the response is reliable enough to show]

User output:
  [what appears on screen — including the fallback path described in Section 7]
```

---

## Section 6 — Team Roles and Contract

*Built on your Lab 2 proposal Section 5. Team contract is new in Lab 3.*

**Team members and roles:**

| Name | Primary role |
|---|---|
| | |
| | |
| | |
| | |

**Team Contract:** Committed to repo root as `TEAM-CONTRACT.md`.

```
Link: https://github.com/team-binary-bros-byte-queen-kiu-2026/Cost_Accounting_Automation/blob/main/TEAM-CONTRACT.md
```

---

## Section 7 — Safety Threats and Fallback UX

*New in Lab 3.*

### Safety Threats

Fill in every row that applies. For rows that do not apply, write "N/A" and one sentence explaining why.

| Threat | Relevant? | Your mitigation |
|---|---|---|
| Prompt injection — user input hijacks system behaviour | | |
| Hallucination in high-stakes output | | |
| Bias affecting specific user groups | | |
| Content policy violation (image generation, user-generated prompts) | | |
| Privacy violation via stored model inputs or logs | | |
| Data exfiltration via model response | | |

**Top risk you are most concerned about:**

```
[one sentence — name the specific risk and why it is your biggest concern for this product]
```

### Fallback UX

Describe what the user sees when your AI fails, is unavailable, or returns a low-confidence answer. Write this as a user experience description, not an error handling description.

Start with: "The user sees..."

```
[fill in — e.g., "The user sees the extracted fields highlighted in amber with
the label 'Please check these values'. A manual entry option appears below.
The word 'AI' does not appear in the error state — we describe it as
'our system could not read this clearly'."]
```

---

## Section 8 — Data Governance

*New in Lab 3. Required by the syllabus (Week 4: data governance plan).*

Answer all six questions. "We have not decided yet" is not an answer — make a decision now and note that it is provisional.

| Question | Your answer |
|---|---|
| What user data does your app collect or process? | |
| Where is it stored? (service name, country) | |
| How long is it retained? | |
| Who has access to it? | |
| How can a user request deletion? | |
| Does your app send user data to third-party AI APIs? Which ones? | |

---

## Section 9 — IRB-Light Checklist

*Built on your Lab 2 proposal Section 6. Review and confirm.*

Check all that apply:

- [ ] My app collects or processes images of real people
- [ ] My app collects or processes audio recordings
- [ ] My app handles personal health information
- [ ] My app handles financial information
- [ ] My app involves users under 18
- [ ] My app processes documents containing personal data

**For each box checked, describe consent flow and data retention:**

```
[fill in — or write "None of the above apply"]
```

---

## Section 10 — Submission Checklist

Complete before Thursday 2 April 23:59.

- [ ] All sections above have no `[fill in]` remaining
- [ ] `docs/design-review/architecture-diagram.png` committed and readable
- [ ] `TEAM-CONTRACT.md` in repo root with all member names
- [ ] `.env` is not committed (check `.gitignore`)
- [ ] Lab 1 work visible or linked in repo
- [ ] Lab 2 proposal and vision call visible in repo
- [ ] `lab-3/generation-strategy.md` committed
- [ ] Team repo matches the tree in the Lab 3 README
- [ ] Google Form completed by one team member

---

*Design Review for CS-AI-2025 Spring 2026.*
*Questions: zeshan.ahmad@kiu.edu.ge or course forum.*
