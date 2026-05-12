# Data Map — Cost Accounting Automation

**Version:** 1.0
**Last updated:** 12 May 2026
**Owner:** Binary Bros & Byte Queen

This document describes every category of data the application collects or processes,
where it is stored, how long it is retained, and how it can be deleted.
It satisfies the data governance requirement from the Design Review and the Safety Audit.

---

## 1. Data Inventory

| Data Type | Description | Source | Sensitivity |
|---|---|---|---|
| User account data | Email address, display name, hashed password, auth tokens | User registration | Medium |
| Project metadata | Project name, type, region, contract date, status | User input | Low |
| Uploaded documents | Construction specification PDFs and scanned tables | User upload | High |
| Extracted structured data | JSON records derived from uploaded documents by GPT-4o | AI pipeline | High |
| Chat query history | User questions per project session | User input | Medium |
| Episode log | LLM call metrics: tokens, cost, latency, model (no user content) | Backend logging | Low |
| MCP audit log | Tool call events: tool name, input hash, status, latency (no raw input) | MCP server | Low |
| Construction reference tables | Thousands of cost norms, material rates, labour norms from official Georgian sources | Admin import | Public |
| Vector embeddings | Numerical representations of reference table chunks | AI pipeline | Low |

---

## 2. Storage Locations

| Data Type | Service | Region | Encryption at rest |
|---|---|---|---|
| User account data | MongoDB Atlas | EU (Frankfurt) | Yes — AES-256 |
| Project metadata | MongoDB Atlas | EU (Frankfurt) | Yes — AES-256 |
| Uploaded documents | AWS S3 | EU (Frankfurt, eu-central-1) | Yes — SSE-S3 |
| Extracted structured data | MongoDB Atlas | EU (Frankfurt) | Yes — AES-256 |
| Chat query history | MongoDB Atlas (session only, not persisted long-term) | EU (Frankfurt) | Yes — AES-256 |
| Episode log | Local filesystem (`logs/`) → S3 archive after 30 days | EU (Frankfurt) | Yes in S3 |
| MCP audit log | Local filesystem (`logs/`) → S3 archive after 30 days | EU (Frankfurt) | Yes in S3 |
| Construction reference tables | MongoDB Atlas + Pinecone (vector index) | EU (Frankfurt) / US (Iowa, provisional) | Yes |
| Vector embeddings | Pinecone | US (Iowa, provisional — migration to EU planned) | Yes |

---

## 3. Retention Policy

| Data Type | Retention Period | Deletion Trigger |
|---|---|---|
| User account data | Until account deletion | User requests account deletion |
| Project metadata | Duration of active project + 30 days | User finalises project or requests deletion |
| Uploaded documents | Duration of active project + 30 days | Project finalisation or manual user deletion |
| Extracted structured data | Duration of active project + 30 days | Same as uploaded documents |
| Chat query history | Current session only; not persisted beyond session end | Session end |
| Episode log | 90 days rolling | Automated cleanup after 90 days |
| MCP audit log | 90 days rolling | Automated cleanup after 90 days |
| Construction reference tables | Indefinite (public data, updated as regulations change) | Admin action |
| Vector embeddings | Same as reference tables | Rebuilt on table update |

---

## 4. Third-Party Data Transfers

| Third Party | Data Sent | Purpose | Data Processing Agreement |
|---|---|---|---|
| OpenAI (via OpenRouter) | Extracted document text, user chat queries, project metadata | Document parsing (GPT-4o), chatbot Q&A (GPT-4.1), embeddings | OpenAI API Terms — no training on API data |
| OpenAI Whisper | Audio clip (transcription only; clip not stored) | Voice query transcription | Same as above |
| AWS | Uploaded document files | Secure file storage | AWS DPA |
| Pinecone | Vector embeddings only (no raw text) | Similarity search for RAG | Pinecone DPA |

**No PII (names, emails, phone numbers, ID numbers) is ever sent to third-party AI APIs.**

---

## 5. User Rights and Deletion Procedure

Users can exercise the following rights from within the application:

| Right | How to exercise | Processing time |
|---|---|---|
| Access | "Export my data" button in account settings → downloads JSON archive | Immediate |
| Deletion | "Delete project" → removes all project files and metadata | Within 72 hours |
| Account deletion | "Delete account" in account settings → removes all user data | Within 72 hours |
| Restrict processing | Disable AI features per project in project settings | Immediate |

Users who cannot access the application may email: team@cost-accounting-app.ge

---

## 6. PII Absence in Logs

The episode log (`logs/episode-log.jsonl`) records only operational metrics:
timestamps, model names, token counts, costs, latencies, and error codes.
No user query text, email addresses, names, or document content is written to the log.

MCP audit log entries record only: tool name, SHA-256 hash of input (not raw input), result status, and latency.

**Verification command:**
```bash
grep -E "[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}" logs/episode-log.jsonl
grep -E "[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}" logs/mcp-audit.jsonl
```
Both commands should return no output.

---

*Data Map · Cost Accounting Automation · CS-AI-2025 Spring 2026*
