# 🤖 TalentScout Hiring Assistant

> An intelligent conversational AI chatbot for initial candidate screening, built with **Streamlit** and **Groq**.

---

## 📌 Project Overview

TalentScout Hiring Assistant automates the first stage of technical recruitment by:

1. **Greeting** candidates and explaining the process
2. **Gathering** essential candidate information (name, email, phone, experience, desired role, location)
3. **Collecting tech stack** declarations (languages, frameworks, databases, tools)
4. **Generating 3–5 tailored technical questions** per candidate based on their declared stack
5. **Conducting** a structured Q&A and gracefully **closing** the session
6. **Persisting** session data securely with PII redaction in logs

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- An [Groq API key](https://console.groq.com/)

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/YOUR_USERNAME/talentscout-hiring-assistant.git
cd talentscout-hiring-assistant

# 2. Create and activate a virtual environment (recommended)
python -m venv venv
source venv/bin/activate        # Linux/macOS
# venv\Scripts\activate         # Windows

# 3. Install dependencies
pip install -r requirements.txt

```

### Run Locally

```bash
streamlit run app.py
```

Open your browser at **http://localhost:8501**

---

## 🗂️ Project Structure

```
talentscout-hiring-assistant/
├── app.py                  # Streamlit frontend + orchestration
├── conversation_manager.py # Stage machine, prompt engineering, info extraction
├── data_handler.py         # Secure data persistence (PII-aware)
├── requirements.txt        # Python dependencies
├── candidate_data/         # Auto-created at runtime (gitignored)
│   ├── candidates/         # Full PII profiles (restricted)
│   └── sessions/           # Anonymised session logs
└── README.md
```

---

## 💬 Usage Guide

| Step | What happens |
|------|-------------|
| Launch the app | The bot greets you and asks for your name |
| Provide basic info | Name → Email → Phone → Experience → Desired role → Location |
| Declare your tech stack | List any languages, frameworks, databases, tools |
| Answer technical questions | 3–5 questions auto-generated from your stack |
| End the session | Type `exit`, `bye`, or `done` at any time |

**Sidebar** shows real-time progress: stage, collected fields, and Q&A count.

---

## 🔧 Technical Details

### Libraries & Models

| Component | Choice | Reason |
|-----------|--------|--------|
| Frontend | Streamlit | Fast to build, great chat support |
| LLM | Groq | Strong reasoning, instruction-following |
| LLM SDK | `groq` Python SDK | Official, async-ready |
| Storage | Local JSON | Simple, no infrastructure overhead |

### Architecture

```
User Input
    │
    ▼
app.py  ──── ConversationManager ──── System Prompt (stage-aware)
    │               │                         │
    │          extract_info()           Groq API
    │          process_response()            │
    │               │                   AI Response
    ▼               ▼
DataHandler    Stage Advance
(save session)
```

---

## 🧠 Prompt Design

### Multi-Stage System Prompts

The system prompt is **dynamically rebuilt on every turn** based on the current conversation stage. Each stage injects:

- **Role definition** — who TalentScout is and what it must NOT do
- **Stage-specific instructions** — exactly what to ask/do next
- **Candidate context block** — all already-collected info so the LLM never re-asks

This eliminates hallucination of already-provided data and keeps the bot on task.

### Key Prompt Engineering Techniques

| Technique | Application |
|-----------|-------------|
| **Role prompting** | "You are TalentScout Hiring Assistant. Your ONLY purpose is…" |
| **Constraint injection** | Hard rules (one question at a time, no off-topic) |
| **Context grounding** | Candidate data injected as structured facts every turn |
| **Output formatting** | Explicit format for question lists (`Question 1:`, `**bold**`) |
| **Transition signals** | LLM response is scanned for trigger phrases to advance stage |
| **Fallback instructions** | Graceful handling of unclear or off-topic input |

### Technical Question Generation

When the `technical_questions` stage is entered with an empty question list, the system prompt instructs Claude to:
- Generate **3–5 questions** covering the exact tech stack provided
- Mix difficulty (foundational → advanced)
- Use open-ended questions (not yes/no)
- Format questions with numbering for easy parsing

---

## 🔒 Data Privacy & GDPR Compliance

| Practice | Implementation |
|---------|---------------|
| Minimal data collection | Only collect fields needed for screening |
| Purpose limitation | Data used solely for recruitment assessment |
| Data separation | Full PII in `candidates/`; logs anonymised in `sessions/` |
| PII redaction | Email and phone replaced with `[REDACTED]` in transcripts |
| Hashing | Email hashed (SHA-256) in session logs |
| User rights | Users can end session at any time; data stored locally |

> ⚠️ For production deployment, store `candidate_data/` outside the repo and add it to `.gitignore`. Consider encrypting the `candidates/` directory.

---

## ⚡ Challenges & Solutions

| Challenge | Solution |
|-----------|----------|
| Keeping LLM on-topic | Hard constraint in system prompt + fallback instruction |
| Avoiding re-asking collected info | Context block injected every turn with current state |
| Stage transitions from free text | Hybrid: heuristic extraction + AI response scanning |
| PII in logs | Two-file approach: full PII vs redacted transcript |
| Question counting | Regex parser extracts numbered questions; user replies increment counter |

---

## 🌟 Optional Enhancements Implemented

- **Custom CSS dark theme** with gradient accents
- **Real-time sidebar progress** — stage, field checklist, Q&A counter
- **PII-redacted session logging** for GDPR alignment
- **Regex-based info extraction** (email, phone, experience, tech keywords) to pre-populate context

---

## 📄 License

MIT — free to use and modify.
