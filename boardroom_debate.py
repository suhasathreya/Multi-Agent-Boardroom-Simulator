"""
Boardroom Debate Simulator - Production Deployment Version
----------------------------------------------------------

This orchestrates a 1–3 round debate between:
- PM Agent (argues for idea)
- Engineering Agent (pushes back)
- CEO Agent (final verdict)

Models used (OpenRouter free tiers):
- Summaries: meta-llama/llama-3.2-3b-instruct:free
- PM/ENG Arguments: google/gemma-3-27b-it:free
- CEO Verdict: meta-llama/llama-3.3-70b-instruct:free

Environment variable required:
    OPENROUTER_API_KEY
"""

import os
import time
import json
import requests

# --------------------------------------------
# LOCAL .env SUPPORT (loads ONLY during dev)
# --------------------------------------------

# If python-dotenv is installed, load .env file into os.environ.
# If running in production (AWS Lambda, Docker), this silently does nothing.
try:
    from dotenv import load_dotenv
    load_dotenv()          # <-- THIS is what loads .env variables
except ImportError:
    # No python-dotenv installed = production environment = ignore silently
    pass

# --------------------------------------------
# REQUIRED ENV VARS
# --------------------------------------------
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")

if not OPENROUTER_API_KEY:
    raise RuntimeError(
        "OPENROUTER_API_KEY is missing.\n"
        "Local: Add it to .env\n"
        "Prod: Set it as an environment variable in AWS / Docker."
    )

SITE_URL = os.environ.get("OPENROUTER_SITE_URL", "")
SITE_NAME = os.environ.get("OPENROUTER_SITE_NAME", "")

# ============================================================
# 2. RAW REQUESTS WRAPPER WITH RETRIES
# ============================================================
def openrouter_request(model: str, messages: list, retries: int = 3, temperature: float = 0.7) -> str:
    """
    Calls OpenRouter's chat/completions endpoint using raw HTTP.
    Retries automatically on rate limits or transient failures.
    """

    url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }
    '''
    if SITE_URL:
        headers["HTTP-Referer"] = SITE_URL
    if SITE_NAME:
        headers["X-Title"] = SITE_NAME
    '''

    body = {
        "model": model,
        "messages": messages,
        "temperature": temperature
    }

    for attempt in range(1, retries + 1):

        try:
            response = requests.post(url, headers=headers, data=json.dumps(body), timeout=50)

            if response.status_code == 200:
                resp_json = response.json()
                return resp_json["choices"][0]["message"]["content"]

            # Rate limit or server throttle
            if response.status_code in (429, 500, 502, 503, 504):
                if attempt == retries:
                    raise RuntimeError(f"OpenRouter error after retries: {response.text}")
                time.sleep(1.5 * attempt)
                continue

            # Other errors: crash now
            raise RuntimeError(f"OpenRouter call failed: {response.status_code} - {response.text}")

        except requests.exceptions.RequestException as e:
            if attempt == retries:
                raise RuntimeError(f"Network error calling OpenRouter: {e}")
            time.sleep(1.5 * attempt)

# ============================================================
# 3. MODEL ROUTING
# ============================================================
MODEL_SUMMARY = "mistralai/mistral-7b-instruct:free"
MODEL_ARGUMENT = "google/gemma-3-27b-it:free"
MODEL_CEO = "meta-llama/llama-3.3-70b-instruct:free"


# ============================================================
# 4. AGENT FUNCTIONS
# ============================================================
def summarize(text):
    messages = [
        {
            "role": "system",
            "content": (
                "You are a summarization engine. "
                "Summarize the input text into 5 very short bullet points. "
                "Ignore details. Avoid markdown. Keep it under 120 words."
            )
        },
        {"role": "user", "content": text}
    ]
    return openrouter_request(MODEL_SUMMARY, messages, temperature=0.3)


def pm_initial(user_idea: str | None) -> str:
    if user_idea:
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a Product Manager. Your output MUST be between 130 and 160 words — "
                    "never exceed this limit. Do NOT produce long essays. "
                    "Use short paragraphs and at most 4 to 5 bullet points. "
                    "If you exceed 160 words, regenerate until you meet constraints."
                )
            },
            {
                "role": "user",
                "content": (
                    f"Product Idea: {user_idea}\n\n"
                    "Write a compelling PM argument that sells this idea. "
                    "Focus on strategic value, impact, customer pain, and why it must be prioritized. "
                    "Use tight prose — no rambling, no long sections."
                )
            }
        ]
    else:
        messages = [
            {
                "role": "system",
                "content": (
                    "Generate a realistic new software product idea AND argue for it. "
                    "Output must be strictly 130 to 160 words. "
                    "No long paragraphs. No more than 5 bullets. "
                    "Keep it crisp and professional."
                )
            },
            {
                "role": "user",
                "content": "Generate a PM argument for the new idea (130 to 160 words)."
            }
        ]
    return openrouter_request(MODEL_ARGUMENT, messages)



def engineering_reply(summary: str, pm_msg: str) -> str:
    messages = [
        {
            "role": "system",
            "content": (
                "You are the Engineering Lead. Write a strict 130 to 160 word rebuttal. "
                "Use numbered concerns only (1 to 4). "
                "Focus on feasibility, cost, tech risk, ambiguity, scaling, integration, and delivery realism. "
                "No long essays. No walls of text. "
                "If output exceeds 160 words, regenerate."
            )
        },
        {
            "role": "user",
            "content": (
                f"Summary of discussion:\n{summary}\n\n"
                f"PM said:\n{pm_msg}\n\n"
                "Write your engineering pushback (130–160 words)."
            )
        }
    ]
    return openrouter_request(MODEL_ARGUMENT, messages)



def pm_reply(summary: str, eng_msg: str) -> str:
    messages = [
        {
            "role": "system",
            "content": (
                "You are the PM responding to engineering concerns. "
                "Write 130 to 160 words maximum. "
                "Use short labelled sections OR 4 to 5 bullets. "
                "Tone: collaborative but firm. "
                "No essay-style writing."
            )
        },
        {
            "role": "user",
            "content": (
                f"Summary:\n{summary}\n\n"
                f"Engineering concerns:\n{eng_msg}\n\n"
                "Write PM rebuttal (130 to 160 words)."
            )
        }
    ]
    return openrouter_request(MODEL_ARGUMENT, messages)



def ceo_verdict(full_transcript: str) -> str:
    messages = [
        {
            "role": "system",
            "content": (
                "You are the CEO. Deliver a final APPROVE or REJECT decision. "
                "Your TOTAL output must be 130 to 160 words. "
                "Use short paragraphs + a micro scorecard (5 items, short phrases). "
                "Do NOT exceed 160 words under any circumstance."
            )
        },
        {
            "role": "user",
            "content": (
                f"Transcript:\n{full_transcript}\n\n"
                "Now output the final CEO verdict (130 to 160 words)."
            )
        }
    ]
    return openrouter_request(MODEL_CEO, messages)



# ============================================================
# 5. MAIN DYNAMIC DEBATE LOOP
# ============================================================
def run_debate(user_idea: str | None, rounds: int):
    """
    Runs the debate for the number of rounds specified by the frontend (1–3).
    """

    transcript = []
    summary = ""

    # ---- ROUND 1 ----
    pm_msg = pm_initial(user_idea)
    transcript.append(("PM_R1", pm_msg))

    eng_msg = engineering_reply("Initial proposal only.", pm_msg)
    transcript.append(("ENG_R1", eng_msg))

    summary = summarize(pm_msg + "\n" + eng_msg)

    # ---- ROUNDS 2..N ----
    for r in range(2, rounds + 1):
        pm_msg = pm_reply(summary, eng_msg)
        transcript.append((f"PM_R{r}", pm_msg))

        eng_msg = engineering_reply(summary, pm_msg)
        transcript.append((f"ENG_R{r}", eng_msg))

        summary = summarize(summary + "\n" + pm_msg + "\n" + eng_msg)

    # ---- CEO DECISION ----
    full_text = ""
    for role, msg in transcript:
        full_text += f"{role}:\n{msg}\n\n"

    ceo = ceo_verdict(full_text)

    return {
        "rounds": rounds,
        "transcript": transcript,
        "summary_final": summary,
        "ceo_verdict": ceo,
    }


# ============================================================
# 6. OPTIONAL LOCAL TEST
# ============================================================
if __name__ == "__main__":
    result = run_debate("AI tool that summarizes Zoom meetings automatically.", rounds=1)
    print(json.dumps(result, indent=2))