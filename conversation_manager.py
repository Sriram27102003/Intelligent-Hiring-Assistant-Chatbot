"""
conversation_manager.py
Manages conversation state, stage transitions, candidate info extraction,
and system prompt engineering for TalentScout.
"""

import re
import json
from typing import Any


class ConversationManager:
    """
    Tracks conversation stage, candidate profile, and Q&A progress.
    Provides carefully engineered system prompts for each stage.
    """

    STAGES = ["greeting", "gathering_info", "tech_stack", "technical_questions", "closing"]

    # Fields we need to collect, in preferred order
    REQUIRED_FIELDS = [
        "full_name", "email", "phone",
        "years_experience", "desired_position", "location",
    ]

    # Exit triggers
    EXIT_KEYWORDS = {"exit", "quit", "bye", "goodbye", "end", "stop", "done"}

    def __init__(self):
        self.stage = "greeting"
        self.candidate_info: dict[str, Any] = {
            "full_name": None,
            "email": None,
            "phone": None,
            "years_experience": None,
            "desired_position": None,
            "location": None,
            "tech_stack": [],
        }
        self.questions: list[str] = []        # Generated technical questions
        self.answered_count: int = 0
        self.missing_fields_asked: list[str] = []  # Fields already asked about

    # ── Public accessors ──────────────────────────────────────────────────────

    def get_stage(self) -> str:
        return self.stage

    @property
    def qa_progress(self) -> dict:
        return {"total": len(self.questions), "answered": self.answered_count}

    # ── Greetings & farewells ─────────────────────────────────────────────────

    def get_greeting(self) -> str:
        return (
            "👋 **Welcome to TalentScout's Hiring Assistant!**\n\n"
            "I'm here to help with your initial screening for technology positions. "
            "Our conversation will take about 5–10 minutes and covers:\n\n"
            "1. 📋 **Basic information** — name, contact details, experience\n"
            "2. 🛠️ **Tech stack** — languages, frameworks, tools you work with\n"
            "3. 💡 **Technical questions** — a few questions tailored to your stack\n\n"
            "Everything you share is handled securely and only used for recruitment purposes.\n\n"
            "**To begin, could you please tell me your full name?** 😊\n\n"
            "*(Type `exit` or `bye` at any time to end the session.)*"
        )

    def get_farewell_message(self) -> str:
        name = self.candidate_info.get("full_name") or "there"
        first = name.split()[0] if name != "there" else name
        return (
            f"🎉 **Thank you, {first}!**\n\n"
            "Your profile has been submitted to the TalentScout team. Here's what happens next:\n\n"
            "- 📧 You'll receive a confirmation email within **24 hours**\n"
            "- 👥 A recruiter will review your profile within **3–5 business days**\n"
            "- 📞 If shortlisted, we'll reach out to schedule a detailed interview\n\n"
            "We appreciate your time and wish you the best of luck! 🚀\n\n"
            "*This session has ended. You can start a new one using the sidebar.*"
        )

    # ── System prompt engineering ─────────────────────────────────────────────

    def get_system_prompt(self) -> str:
        """
        Returns a stage-appropriate system prompt that keeps the LLM
        focused on the hiring-assistant task.
        """
        base = self._base_instructions()
        stage_specific = self._stage_instructions()
        context = self._context_block()
        return f"{base}\n\n{stage_specific}\n\n{context}"

    def _base_instructions(self) -> str:
        return """You are the TalentScout Hiring Assistant, an intelligent chatbot for a \
technology recruitment agency called TalentScout. Your ONLY purpose is to screen \
technology job candidates through a structured conversation.

CORE RULES — follow these absolutely:
1. NEVER go off-topic. If the user asks about anything unrelated to the hiring process, \
   politely redirect them back to the screening conversation.
2. Be warm, professional, and encouraging — you represent TalentScout's brand.
3. Ask ONE question at a time. Never overwhelm the candidate with multiple questions.
4. If the user's response is unclear or off-topic, acknowledge it gently and ask again.
5. Do NOT generate harmful, discriminatory, or biased content. Treat all candidates equally.
6. Keep responses concise (3–6 sentences max) unless you are listing technical questions.
7. Always maintain conversation context — reference what the candidate has already told you.
8. If the candidate tries to skip a required field, politely explain why it's important \
   and ask again.

FALLBACK: If you genuinely cannot understand the user's input after two attempts, say: \
"I'm having trouble understanding. Could you rephrase that?" and move on."""

    def _stage_instructions(self) -> str:
        stage = self.stage
        info = self.candidate_info

        if stage == "greeting":
            return """CURRENT STAGE: Greeting
Your job: Welcome the candidate and start collecting their full name.
If they have provided their name, acknowledge it warmly and ask for their email address next."""

        elif stage == "gathering_info":
            missing = [f for f in self.REQUIRED_FIELDS if not info.get(f)]
            if not missing:
                return """CURRENT STAGE: Gathering Info — COMPLETE
All basic info collected. Transition to tech stack: Tell the candidate you have all their \
basic details and ask them to list their tech stack (programming languages, frameworks, \
databases, and tools they are proficient in). Be specific about what you want."""
            else:
                next_field = missing[0]
                field_prompts = {
                    "full_name": "Ask for their full name.",
                    "email": "Ask for their email address.",
                    "phone": "Ask for their phone number (explain it's for scheduling interviews).",
                    "years_experience": "Ask how many years of professional experience they have.",
                    "desired_position": "Ask what position(s) they are interested in.",
                    "location": "Ask for their current city/location.",
                }
                return f"""CURRENT STAGE: Gathering Info
You are collecting candidate details. Missing fields: {missing}.
Next action: {field_prompts.get(next_field, f'Ask for their {next_field}.')}
Acknowledge any info they've already provided before asking the next question."""

        elif stage == "tech_stack":
            return """CURRENT STAGE: Tech Stack Declaration
The candidate is telling you about their tech stack.
Your job:
- Encourage them to be comprehensive: languages, frameworks, databases, DevOps tools, cloud platforms.
- If they've provided a list, summarise what you heard and confirm it with them.
- Once confirmed, transition to generating technical questions by saying you'll now ask \
  some technical questions tailored to their stack.
- Do NOT generate the questions yet — just transition smoothly."""

        elif stage == "technical_questions":
            q_count = len(self.questions)
            answered = self.answered_count
            remaining = q_count - answered

            if q_count == 0:
                stack = ", ".join(info.get("tech_stack", []))
                return f"""CURRENT STAGE: Technical Questions — GENERATE NOW
The candidate's tech stack is: {stack}

Generate exactly 3–5 technical interview questions covering their declared stack. Rules:
- Questions must be relevant to the specific technologies listed.
- Mix difficulty: 1–2 foundational, 1–2 intermediate, 1 advanced.
- Questions should be open-ended (not yes/no).
- Number them clearly: "Question 1:", "Question 2:", etc.
- After listing ALL questions, invite them to answer question 1.

Example format:
"Here are your technical questions:

**Question 1:** [question about tech 1]
**Question 2:** [question about tech 2]
...

Please go ahead and answer **Question 1** when you're ready!"
"""
            elif remaining > 0:
                return f"""CURRENT STAGE: Technical Questions — IN PROGRESS
Questions generated: {q_count}. Answered so far: {answered}. Remaining: {remaining}.

Your job:
- Acknowledge the candidate's answer to the current question briefly and constructively.
- Prompt them to move to the next question (Question {answered + 1}).
- If their answer is very short or vague, you may ask a brief follow-up ONCE before moving on.
- Do NOT re-ask questions they have already answered."""
            else:
                return """CURRENT STAGE: Technical Questions — COMPLETE
All technical questions have been answered. Transition to closing:
- Thank the candidate for their time and thoughtful answers.
- Summarise what was collected (their name, position of interest, and stack).
- Explain the next steps (recruiter review, timeline).
- Ask if they have any questions for TalentScout before you wrap up."""

        elif stage == "closing":
            return """CURRENT STAGE: Closing
Wrap up the conversation gracefully. Answer any final questions the candidate has about \
the process. Remind them they can type 'exit' or 'bye' to end the session. \
Keep it warm and encouraging."""

        return "Help the candidate with their hiring screening process."

    def _context_block(self) -> str:
        info = self.candidate_info
        tech = ", ".join(info.get("tech_stack", [])) or "not yet provided"
        return f"""CANDIDATE CONTEXT (already collected — do NOT re-ask for this):
- Full Name: {info.get('full_name') or 'not yet provided'}
- Email: {info.get('email') or 'not yet provided'}
- Phone: {info.get('phone') or 'not yet provided'}
- Years of Experience: {info.get('years_experience') or 'not yet provided'}
- Desired Position: {info.get('desired_position') or 'not yet provided'}
- Location: {info.get('location') or 'not yet provided'}
- Tech Stack: {tech}
- Technical Questions Generated: {len(self.questions)}
- Questions Answered: {self.answered_count}"""

    # ── Info extraction ───────────────────────────────────────────────────────

    def extract_and_update_info(self, user_message: str):
        """
        Heuristically extract candidate info from free-form user messages.
        Updates candidate_info dict in place.
        """
        msg = user_message.strip()

        # Email
        if not self.candidate_info["email"]:
            email_match = re.search(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", msg)
            if email_match:
                self.candidate_info["email"] = email_match.group(0)

        # Phone (international or local)
        if not self.candidate_info["phone"]:
            phone_match = re.search(r"(\+?[\d\s\-().]{7,15})", msg)
            if phone_match:
                candidate = phone_match.group(0).strip()
                if sum(c.isdigit() for c in candidate) >= 7:
                    self.candidate_info["phone"] = candidate

        # Years of experience
        if not self.candidate_info["years_experience"]:
            exp_match = re.search(r"(\d+)\s*(years?|yrs?)", msg, re.IGNORECASE)
            if exp_match:
                self.candidate_info["years_experience"] = f"{exp_match.group(1)} years"

        # Tech stack keywords
        TECH_KEYWORDS = {
            "python", "javascript", "typescript", "java", "c++", "c#", "go", "rust",
            "ruby", "php", "swift", "kotlin", "scala", "r", "matlab",
            "react", "angular", "vue", "next.js", "nuxt", "svelte",
            "django", "flask", "fastapi", "spring", "express", "nest.js",
            "node.js", "nodejs", "deno",
            "postgresql", "mysql", "sqlite", "mongodb", "redis", "cassandra",
            "elasticsearch", "firebase", "supabase",
            "docker", "kubernetes", "terraform", "ansible",
            "aws", "gcp", "azure", "heroku", "vercel",
            "git", "github", "gitlab", "jira", "linux",
            "machine learning", "ml", "deep learning", "tensorflow", "pytorch",
            "pandas", "numpy", "scikit-learn", "spark", "hadoop",
            "graphql", "rest", "grpc", "kafka", "rabbitmq",
        }
        msg_lower = msg.lower()
        found = []
        for tech in TECH_KEYWORDS:
            if re.search(rf"\b{re.escape(tech)}\b", msg_lower):
                found.append(tech.title() if len(tech) > 3 else tech.upper())

        if found:
            existing = set(t.lower() for t in self.candidate_info["tech_stack"])
            for t in found:
                if t.lower() not in existing:
                    self.candidate_info["tech_stack"].append(t)

    # ── Stage transitions ─────────────────────────────────────────────────────

    def process_ai_response(self, ai_response: str, user_message: str):
        """
        Inspect the AI response and user message to advance the conversation stage.
        """
        info = self.candidate_info
        stage = self.stage

        if stage == "greeting":
            # Move to gathering info once we see a name-like response
            if len(user_message.split()) <= 5 and not any(
                kw in user_message.lower() for kw in ["hello", "hi", "hey", "help"]
            ):
                self._advance_stage("gathering_info")
            elif info.get("full_name"):
                self._advance_stage("gathering_info")

        elif stage == "gathering_info":
            all_collected = all(info.get(f) for f in self.REQUIRED_FIELDS)
            if all_collected:
                self._advance_stage("tech_stack")

        elif stage == "tech_stack":
            if info.get("tech_stack") and len(info["tech_stack"]) >= 1:
                # Move to technical questions when LLM signals transition
                transition_signals = [
                    "technical question", "few questions", "based on your stack",
                    "assess your", "let's test", "now ask"
                ]
                if any(sig in ai_response.lower() for sig in transition_signals):
                    self._advance_stage("technical_questions")

        elif stage == "technical_questions":
            # Extract questions from AI response on first generation
            if not self.questions:
                self.questions = self._parse_questions(ai_response)

            # Count answered questions (rough heuristic: each user reply = 1 answer)
            if self.questions and len(user_message) > 10:
                self.answered_count = min(self.answered_count + 1, len(self.questions))

            if self.answered_count >= len(self.questions) and self.questions:
                self._advance_stage("closing")

        # Extract name heuristically from first user message in gathering stage
        if not info.get("full_name") and stage in ("greeting", "gathering_info"):
            words = user_message.strip().split()
            if 1 <= len(words) <= 4 and all(w[0].isupper() or w.isalpha() for w in words if w):
                info["full_name"] = user_message.strip().title()

    def _advance_stage(self, new_stage: str):
        """Move to a new stage if it's a valid forward transition."""
        try:
            current_idx = self.STAGES.index(self.stage)
            new_idx = self.STAGES.index(new_stage)
            if new_idx > current_idx:
                self.stage = new_stage
        except ValueError:
            pass

    @staticmethod
    def _parse_questions(text: str) -> list[str]:
        """Extract numbered questions from AI response text."""
        pattern = r"(?:question\s*\d+[:\.]?\s*)(.+?)(?=question\s*\d+|$)"
        matches = re.findall(pattern, text, re.IGNORECASE | re.DOTALL)
        questions = [q.strip().replace("\n", " ") for q in matches if len(q.strip()) > 10]
        if not questions:
            # Fallback: split by numbered list
            lines = text.split("\n")
            for line in lines:
                if re.match(r"^\s*[\*\-]?\s*\d+[\.\)]\s+.{10,}", line):
                    clean = re.sub(r"^\s*[\*\-]?\s*\d+[\.\)]\s+", "", line).strip()
                    if clean:
                        questions.append(clean)
        return questions[:5]
