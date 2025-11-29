**Multi-Agent-Boardroom-Simulator**
Boardroom debate simulator featuring a PM, an Engineer, and a CEO (judge)
**# 👔 The Boardroom Simulator (Agent 002)

> **Experiment #2 in the "Autonomous Organization" Series.** > A multi-agent orchestration system that simulates high-stakes strategic conflict between a PM, an Engineer, and a CEO.

## 💡 The Thesis
Most AI "reasoning" is linear and agreeable. But in a real company, good strategy comes from **friction**—the conflict between Growth (PM) and Stability (Engineering).

This project replaces the standard "Chatbot" pattern with a **Distributed State Machine**. Instead of one model trying to be everyone, three distinct agents with opposing system prompts debate a user-defined topic, with a fourth agent acting as the Judge.

## 🏗️ System Architecture

This is not a single prompt. It is a **Model Routing Mesh** designed to optimize for cost and persona fidelity.

### The Flow:
1.  **User Input:** Enters a strategic pivot (e.g., *"Switch database from SQL to NoSQL"*).
2.  **Agent A (PM):** Generates an aggressive growth pitch.
3.  **Agent B (Engineering):** Reads the PM's pitch and generates a technical rebuttal.
4.  **Agent C (Summarizer):** Compresses the conflict into high-signal bullet points.
5.  **Agent D (CEO):** Weighs the trade-offs and issues a binary GO/NO-GO verdict.



[Image of multi agent system architecture]


## 🧠 The "Model Mesh" (Routing Logic)

I deliberately avoided using a single "God Model" (like GPT-5) for everything. Instead, I routed tasks via **OpenRouter** to the best-fit model for the specific cognitive task:

| Role | Model Used | Reasoning |
| :--- | :--- | :--- |
| **The Fighters** (PM & Eng) | **Google Gemma 2 27B** | High creativity, "punchy" writing style, excellent role adherence. |
| **The Scribe** (Summarizer) | **Mistral 7B** | Fast, low latency, extremely cheap. No need to burn heavy tokens for compression. |
| **The Judge** (CEO) | **Llama 3.3 70B** | High parameter count for complex reasoning and nuance. |

## 🛠️ Tech Stack

* **Orchestration:** Python (Raw State Machine, no LangChain)
* **Gateway:** OpenRouter API
* **Frontend:** Streamlit
* **Observability:** Built-in error handling and retry logic.

## 🚀 Quick Start

### 1. Clone
```bash
git clone [https://github.com/yourusername/boardroom-simulator.git](https://github.com/yourusername/boardroom-simulator.git)
cd boardroom-simulator
```
### 2. Install Dependencies
```bash
pip install streamlit openai supabase python-dotenv requests
```
### 3. Configure Secrets
Create a .streamlit/secrets.toml file:
```bash
OPENROUTER_API_KEY = "sk-or-..."
```
