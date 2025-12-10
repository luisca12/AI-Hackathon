# NetOps: AI-Powered Automation Solution

**Version:** 1.2  
**Type:** Internal AI + Network Automation Assistant  
**Stack:** FastAPI (Python) + OpenAI API + Simple HTML/JS frontend + Local Python scripts

---

## 1. Overview

NetOps: AI-Powered Automation Solution is a small web application that behaves like a ChatGPT-style assistant for network engineers.

The assistant can:

- Talk with the user in natural language.
- Suggest and explain available automation scripts.
- Collect the needed parameters (devices, credentials, commands, etc.).
- Ask for explicit confirmation before running anything.
- Execute **local Python scripts** (existing automations) securely on the server.
- Show the **output of the scripts** directly in the chat.

The project is designed as a proof-of-concept for an **AI-driven NetOps assistant** that orchestrates existing automation instead of replacing it.

---

## 2. Features

### Core Features

- 💬 **Chat-style web UI** similar to ChatGPT (simple HTML + JS).
- 🤖 **LLM backend** using OpenAI (`gpt-5-nano` for tests).
- 📂 **Local script catalog**:
  - Scripts are stored locally under the `scripts/` directory.
  - Each script has its own folder (e.g. `runShowCommands-main`, `aclRemoval-main`, etc.).
- 🧠 **AI-aware script selection**:
  - The model receives a catalog of available scripts.
  - It **must** choose only among the allowed scripts.
  - It asks for missing parameters (IP, username, password, command, etc.).
- ✅ **Explicit user confirmation** before execution.
- 🖥️ **Script output in the chat**:
  - Return code
  - Standard output (command results)
  - Standard error (if any)

### Version 1.2 – New Additions

In version **1.2** we added:

- 🧩 **Generic script runner**:
  - A single function `run_local_script(script_id, params)` can execute **any** script defined in `scriptsAvailable`.
  - No need to write a new Python function per script.
- 🧱 **Script metadata in `scriptsAvailable`**:
  - Each script now includes:
    - `folder` (directory under `scripts/`)
    - `entrypoint` (usually `main.py`)
    - `cli_params` (how to map JSON parameters to CLI flags).
- 🧷 **Context of last successful command**:
  - After a script runs successfully, we store:
    - `script_id`
    - `devices`
    - `username`
    - `password`
  - On the next request, this context is sent to the model so it can understand:
    - “Run another command on the same device”
    - “Use the same credentials”
- 🧩 **Multi-script support**:
  - Now the backend can execute:
    - `runShowCommands-main`
    - `aclRemoval-main`
    - `shIntStatHalf_SD-WAN-main`
    - `showErrDisableInt-main`
  - Adding new scripts only requires updating the catalog; no new Python functions.

---

## 3. Architecture

High-level architecture:

```text
[Browser: index.html + JS]
          |
          |  HTTP POST /chat  (JSON: { "message": "..." })
          v
[FastAPI Backend (api.py / main.py)]
          |
          |  Calls OpenAI Chat Completions
          |  (system prompt + chat history + optional last-run context)
          v
[OpenAI LLM: "Automation Hero"]
          |
          |  Returns STRICT JSON:
          |    {
          |      "answer": "...",
          |      "script_to_run": "runShowCommands-main" | ... | null,
          |      "parameters": {...},
          |      "run_script": true | false
          |    }
          v
[Backend]
  - Shows "answer" in chat.
  - If run_script = true:
        -> run_local_script(script_id, parameters)
        -> execute local Python script with subprocess
        -> combine stdout/stderr into the answer.
