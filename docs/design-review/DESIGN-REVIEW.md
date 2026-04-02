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

**Problem statement (one sentence):**

```
Georgian construction cost accountants struggle to compile legally compliant accounting
files because they must manually search thousands of legacy Soviet-era reference tables,
which means the process is slow, error-prone, and impossible to scale.
```

**Who exactly has this problem:**

```
A professional cost accountant in Tbilisi working on a mid-size construction project.
They spend hours each day searching through printed or PDF tables — materials, labour
rates, overhead coefficients — looking up values one by one to assemble a compliant
accounting report. We have consulted directly with professional accountants and attended
construction accounting courses in Georgia to understand this workflow first-hand. One
senior expert we spoke with had previously attempted to build software for this problem
but could not complete it due to technical limitations. Their confirmation of the problem
and its difficulty validated our direction.
```

**What they do today without your solution:**

```
Accountants manually search thousands of static reference tables (often in PDF or printed
form), cross-reference values by hand, and assemble construction accounting files
document by document. The process is largely unchanged since the Soviet era. It requires
deep memorisation of table structures and significant time per project. Errors are common
and hard to catch before submission to authorities.
```

**Why AI is the right tool:**

```
The core challenge is variability at scale: thousands of tables exist in inconsistent formats
that no conventional script can reliably parse. AI enables us to generate tailored
data-conversion logic for each table type, something that would be impractical manually.
On the user-facing side, AI powers a conversational interface that can answer
context-specific accounting questions in natural language — a capability that a
rule-based or keyword-search system cannot replicate at the depth professional
accountants require. Without AI, the table conversion alone would consume most of the
team's time, and the chatbot would lack the reasoning depth needed to serve as a
reliable virtual assistant for a regulated profession.
```

---

## Section 2 — Proposed Solution and Features

**Solution summary (3–5 sentences):**

```
We are building a web platform that automates the Georgian construction accounting
workflow end to end. The foundation is a structured, queryable database built from
thousands of legacy reference tables converted using an AI-driven agent. On top of this
database, users can upload project documents and receive automatically generated,
legally compliant construction accounting reports. A RAG-powered chatbot allows cost
accountants and business owners to ask detailed questions about any active project using
text or voice. The system is designed to eliminate manual table lookups and reduce
report compilation time from hours to minutes.
```

**Core features:**

| Feature | AI-powered? | The AI differentiator |
|---|---|---|
| Automated table-to-database conversion | Yes | AI agent generates tailored conversion scripts per table format, handling variability that fixed scripts cannot |
| Project document parsing and structuring | Yes | GPT-4o extracts and structures content from mixed-format PDFs and scanned files |
| Compliant accounting report generation | Partially | Backend assembles the report; AI structures the extracted source data that feeds it |
| RAG-powered conversational chatbot | Yes | GPT-4.1 + Pinecone vector search answers project-specific accounting questions grounded in real data |
| Voice input (speech-to-text) | Yes | Whisper-1 transcribes voice queries so accountants can interact hands-free |

**The one feature that would not exist without AI:**

```
The conversational chatbot that functions as a virtual professional cost accountant —
capable of answering context-specific questions about Georgian construction regulations
and project data grounded in the actual reference database.
```

---

## Section 3 — Measurable Success Criteria

| Criterion | How you will measure it | Target |
|---|---|---|
| Table conversion accuracy | Manually verify a sample of 50 converted table entries against the original source; count correctly mapped fields | ≥ 90% field-level accuracy |
| Chatbot answer correctness | Present 30 representative accounting questions to a certified cost accountant; they rate each answer as correct, partially correct, or wrong | ≥ 80% rated correct |
| Report generation time | Measure wall-clock time from project document upload to downloadable report on a standardised test project | ≤ 5 minutes |
| Chatbot grounding (no hallucination) | Check 30 chatbot responses for citations; each must reference a specific table or regulation in the database | 100% of responses cite a source |

---

## Section 4 — Architecture

**Technology stack:**

| Layer | Technology | Why |
|---|---|---|
| Frontend | React (Next.js) + Tailwind CSS | Server-side rendering for dashboard and chatbot UI; fast consistent styling |
| Backend | Node.js (TypeScript) + NestJS | Strong typing, modular architecture suitable for complex AI-heavy workflows |
| Primary AI model — parsing | GPT-4o via OpenRouter | Strong at extracting structured data from mixed-format PDFs |
| Primary AI model — chatbot | GPT-4.1 via OpenRouter | High reasoning accuracy for professional Q&A in a specialised domain |
| Embeddings | text-embedding-3-large | High-quality semantic search for RAG pipeline |
| Speech-to-text | Whisper-1 | Accurate transcription for voice-based queries |
| Fallback model | GPT-4o-mini | Lower-cost fallback when primary model is unavailable or for low-stakes queries |
| Database (primary) | MongoDB | Handles highly variable construction table schemas with nested data |
| Vector database | Pinecone | Fast similarity search for RAG-based chatbot responses |
| File storage | AWS S3 | Scalable secure storage for uploaded project documents |
| File processing | pdf-parse + Tesseract OCR | Handles both digital and scanned documents |
| Report generation | PDFKit / ExcelJS | Generates compliant construction accounting reports |
| Authentication | JWT + OAuth (optional) | Secure, scalable user management |
| Hosting — frontend | Vercel | Optimised for Next.js; simple deployment |
| Hosting — backend | AWS (EC2 / Lambda) | Scalable infrastructure for AI-heavy workloads |
| Caching / queue | Redis + BullMQ | Handles heavy AI jobs asynchronously; improves performance |

**Multimodal capabilities (check all that apply now or planned by Week 8):**

- [x] Text generation
- [x] Vision / image understanding (Lab 2)
- [ ] Image generation
- [x] Audio TTS or STT (Whisper-1 for voice input)
- [x] Document / PDF understanding
- [x] Function calling
- [x] RAG

---

## Section 5 — Prompt and Data Flow

*Most important AI feature: RAG-powered chatbot answering a project-specific accounting question.*

```
User action:
  The user opens the chatbot panel, selects an active construction project from a
  dropdown, and types (or speaks) a question such as: "What is the labour cost rate
  for concrete foundation work under code НР-123?"

Preprocessing:
  If voice: Whisper-1 transcribes the audio to text.
  The question text is cleaned and combined with the selected project's metadata
  (project ID, type, region, contract date) to form the query context.
  The combined text is embedded using text-embedding-3-large.

Prompt construction:
  System prompt: "You are a professional Georgian construction cost accounting
  assistant. Answer only based on the provided reference data. Always cite the
  specific table name or regulation code. If the answer is not in the context,
  say so explicitly — do not guess."
  The top-k (k=5) most relevant chunks retrieved from Pinecone are inserted as
  context blocks. The user's question is appended as the human turn.

API call:
  Model: GPT-4.1 via OpenRouter.
  Temperature: 0.2 (low, to reduce hallucination).
  Max tokens: 1024.
  Response is streamed back to the frontend.

Response parsing:
  The streamed response is displayed token-by-token in the chat UI.
  A citation parser scans the response for table/regulation references and renders
  them as linked footnotes.

Confidence / validation:
  If no Pinecone chunks scored above the similarity threshold (0.75), the system
  prepends a warning banner: "Limited reference data found — verify this answer
  manually." The response is still shown but flagged amber.
  If the model explicitly states it cannot find the answer, the UI shows a
  "No match found" state instead of a streamed response.

User output:
  The answer appears in the chat with inline citations. Uncertain answers are
  flagged amber. The user can click any citation to view the source table entry.
  If the AI is unavailable, the user sees: "The assistant is temporarily
  unavailable. You can search the reference database directly using the table
  browser below."
```

---

## Section 6 — Team Roles and Contract

**Team members and roles:**

| Name | Primary role |
|---|---|
| Guga | Backend & System Architecture |
| Nikoloz | AI & Data Engineering |
| Anastasia | Product, UX & Business / Compliance |

**Team Contract:** Committed to repo root as `TEAM-CONTRACT.md`.

---

## Section 7 — Safety Threats and Fallback UX

### Safety Threats

| Threat | Relevant? | Your mitigation |
|---|---|---|
| Prompt injection — user input hijacks system behaviour | Yes | System prompt is separated from user input; user content is inserted as a delimited context block, not concatenated into the instruction layer. Backend validates that no instruction-like patterns appear in the query before forwarding to the model. |
| Hallucination in high-stakes output | Yes — critical | RAG anchors every response to verified database entries. Confidence threshold on Pinecone similarity score (0.75); responses below threshold are flagged amber. Chatbot is instructed to cite sources and explicitly refuse to answer when data is absent. |
| Bias affecting specific user groups | Low | The domain is technical and regulatory, not demographic. N/A for user-group bias, but we monitor for regional table gaps (some Georgian regions have fewer reference entries). |
| Content policy violation (image generation, user-generated prompts) | Low | No image generation in the product. User prompts are scoped to accounting questions; the system prompt restricts the model to the domain. OpenRouter's content filtering applies as an additional layer. |
| Privacy violation via stored model inputs or logs | Yes | Project documents contain sensitive business and financial data. API calls are not logged beyond session scope. Inputs are not used for model training (OpenRouter/OpenAI enterprise terms). Users are shown a data processing agreement before uploading. |
| Data exfiltration via model response | Yes | The model only receives project metadata and retrieved reference chunks — not raw uploaded files. S3 files are accessed via signed URLs; the model never receives a file path or credential. |

**Top risk you are most concerned about:**

```
Hallucination in the chatbot for high-stakes cost estimates — because an accountant
acting on a wrong figure could produce a non-compliant report that is rejected by
Georgian construction authorities, causing real financial and legal harm to their client.
```

### Fallback UX

```
The user sees their question displayed normally in the chat, but the response area
shows a soft amber card that reads: "We could not find a confident match in the
reference database for this question. The answer below is based on partial data —
please verify before using it in a report." The partial response is shown beneath
the warning in muted text. A "Search tables manually" button appears below,
opening the reference table browser filtered to the most relevant category.
If the AI service is fully unavailable, the amber card is replaced with: "The assistant
is temporarily offline. Your question has been saved and will be answered when
the service resumes." No technical error language is shown to the user at any point.
```

---

## Section 8 — Data Governance

| Question | Your answer |
|---|---|
| What user data does your app collect or process? | User account details (email, name); uploaded project documents (construction specifications, financial data); project metadata (type, region, dates); chat query history per session. |
| Where is it stored? (service name, country) | Documents: AWS S3 (EU region, Frankfurt). Structured project data and user records: MongoDB Atlas (EU region). Vector embeddings: Pinecone (US region, provisional — may move to EU). |
| How long is it retained? | Project data is retained for the duration of the active project. Upon project finalisation and explicit user sign-off, all uploaded documents and derived data are deleted within 30 days. Account data is retained until account deletion. |
| Who has access to it? | Only authenticated team members (developers) have backend access during development. In production, access is role-based: the user sees only their own projects. No third party has access except the AI API providers under their data processing agreements. |
| How can a user request deletion? | A "Delete project" action in the UI triggers immediate removal of all project files and metadata. An "Delete account" option removes all user data. Both are processed within 72 hours. |
| Does your app send user data to third-party AI APIs? Which ones? | Yes. Project metadata and retrieved reference chunks are sent to OpenAI (via OpenRouter) for chatbot responses. Uploaded document text is sent to OpenAI (GPT-4o) for parsing. Audio queries are sent to OpenAI (Whisper-1). No raw files or PII beyond the document content are transmitted. OpenRouter and OpenAI enterprise terms prohibit training on this data. |

---

## Section 9 — IRB-Light Checklist

- [ ] My app collects or processes images of real people
- [ ] My app collects or processes audio recordings *(voice input is transcribed and discarded; not stored)*
- [ ] My app handles personal health information
- [x] My app handles financial information
- [ ] My app involves users under 18
- [x] My app processes documents containing personal data

**For each box checked, describe consent flow and data retention:**

```
Financial information and sensitive business documents:
Users are presented with a clear data usage and privacy notice at the start of each
new project. The notice explains what data is collected, how it is used, how long it
is stored, and the security measures applied. Users must explicitly accept this notice
(a checkbox + confirm button) before they can proceed to the file upload step.
This acceptance is logged with a timestamp and user ID. Data is retained only for
the active project lifetime and deleted within 30 days of project finalisation.
Audio: voice queries are transcribed by Whisper-1 and only the resulting text is
stored as part of the chat session. The audio file is not persisted.
```

---

## Section 10 — Submission Checklist

- [x] All sections above have no `[fill in]` remaining
- [ ] `docs/design-review/architecture-diagram.png` committed and readable
- [x] `TEAM-CONTRACT.md` in repo root with all member names
- [x] `.env` is not committed (check `.gitignore`)
- [ ] Lab 1 work visible or linked in repo
- [ ] Lab 2 proposal and vision call visible in repo
- [ ] `lab-3/generation-strategy.md` committed
- [x] Team repo matches the tree in the Lab 3 README
- [ ] Google Form completed by one team member

---