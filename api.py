import os, subprocess, sys, json
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI

# ========================
# CONFIG INICIAL
# ========================

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise RuntimeError("OPENAI_API_KEY not set")

client = OpenAI(api_key=api_key)

app = FastAPI(
    title="NetOps: AI-Powered Automation Solution",
    description="Simple backend for a ChatGPT-style NetOps assistant.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str

scriptsAvailable = {
    "runShowCommands-main": {
        "displayName": "Run Show Commands",
        "description": (
            "Execute any show command on one or multiple network devices using SSH. "
            "Validates reachability, runs the command and stores outputs in text files under Outputs."
        ),
        "parameters": [
            {"name": "devices", "description": "Comma-separated list of device IPs/hostnames"},
            {"name": "username", "description": "Username for device login"},
            {"name": "password", "description": "Password (also used as enable/secret)"},
            {"name": "command", "description": "Complete show command to run"},
        ],
    },
    "aclRemoval-main": {
        "displayName": "ACL Removal",
        "description": "Remove or modify ACLs on multiple devices.",
        "parameters": [
            {"name": "devices", "description": "Devices where the ACL will be modified"},
            {"name": "acl_id", "description": "ACL ID or name"},
            {"name": "action", "description": "remove/disable or similar"},
        ],
    },
    "shIntStatHalf_SD-WAN-main": {
        "displayName": "Half Duplex Check (SD-WAN)",
        "description": "Check interfaces in half-duplex mode on SD-WAN routers.",
        "parameters": [
            {"name": "devices", "description": "Routers to check"},
        ],
    },
    "showErrDisableInt-main": {
        "displayName": "Err-Disabled Interfaces",
        "description": "Find interfaces in err-disabled state and optionally recover them.",
        "parameters": [
            {"name": "devices", "description": "Devices to analyze"},
        ],
    },
}

def scriptCatalogText():
    lines = []
    for key, info in scriptsAvailable.items():
        lines.append(f"- ID: {key}")
        lines.append(f"  Name: {info['displayName']}")
        lines.append(f"  Description: {info['description']}")
        if "parameters" in info:
            lines.append("  Parameters:")
            for p in info["parameters"]:
                lines.append(f"    - {p['name']}: {p['description']}")
        lines.append("")
    return "\n".join(lines)

scriptCatalogTextOut = scriptCatalogText()

SYSTEM_PROMPT = f"""
Your name is Automation Hero, you're an AI-powered automation assistant for network and operations engineers.

You have access to exactly the following local scripts (identified by their ID):

{scriptCatalogTextOut}

You must ALWAYS respond with a single JSON object, and nothing else. No markdown, no explanations outside JSON.
The JSON MUST have the following structure:

{{
  "answer": "<short, human readable message to show in the chat>",
  "script_to_run": "<one of: runShowCommands-main | aclRemoval-main | shIntStatHalf_SD-WAN-main | showErrDisableInt-main | null>",
  "parameters": {{
    "...": "..."
  }},
  "run_script": false
}}

Behavior rules:

General rules:
- "answer" is what the user will see in the chat, keep it short, clear, technical but easy to understand and looking good.
- Only show the available scripts when the user asks for them, never show them on the first message.
- When the user asks for available scripts, list ONLY the scripts that appear in the catalog above, using a friendly name and description.
- Do NOT invent or mention scripts that are not in the catalog.
- When the user wants to run a specific script, you must:
  - Set "script_to_run" to the correct script ID.
  - Ask for any missing parameters in "answer" and keep "run_script": false.
  - Only when the user has provided ALL required parameters AND explicitly confirms execution (e.g. "yes, run it"), set "run_script": true.
- When "run_script" is true, "parameters" MUST include all values needed by the script (for runShowCommands-main: devices, username, password, command).
- All the replies to the user must always be short, clear, technical but easy to understand, in a nice and human readable format.
- If you will reply with a list of things or missing parameters, use a clear multi-line format, not everything on the same line.

Very important:
- If you are NOT ready to execute (need more info or no explicit confirmation), set "run_script": false.
- If the user changes their mind or says "do not run it", keep "run_script": false.
- Never say that you executed the script yourself; you only request execution through this JSON.

Remember: respond ONLY with JSON. No text before or after the JSON.
"""

baseScriptDir = os.path.join(os.path.dirname(__file__), "scripts")

def run_runShowCommands(params: dict) -> dict:
    devices = params["devices"]           # "192.168.0.14" o "ip1,ip2"
    username = params["username"]
    password = params["password"]
    command = params["command"]

    script_path = os.path.join(
        baseScriptDir,
        "runShowCommands-main",
        "main.py"
    )

    cmd = [
        sys.executable,
        script_path,
        "--devices", devices,
        "--username", username,
        "--password", password,
        "--command", command,
    ]

    script_dir = os.path.dirname(script_path)

    result = subprocess.run(
        cmd,
        cwd=script_dir,
        capture_output=True,
        text=True,
    )

    return {
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }

# ========================
# HISTORIAL DE CONVERSACIÓN
# ========================

# Para el prototipo: un solo historial global
conversation_history = [
    {"role": "system", "content": SYSTEM_PROMPT}
]

@app.post("/chat")
def chatEndpoint(req: ChatRequest):
    global conversation_history

    # Añadir mensaje del usuario al historial
    conversation_history.append({"role": "user", "content": req.message})

    # Llamar al modelo con TODO el historial
    response = client.chat.completions.create(
        model="gpt-5-nano",
        messages=conversation_history,
        # Si tu versión soporta esto, ayuda a forzar JSON:
        # response_format={"type": "json_object"},
    )

    raw = response.choices[0].message.content

    # Guardar también la respuesta del modelo en el historial
    conversation_history.append({"role": "assistant", "content": raw})

    # Intentar parsear JSON
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        # Si el modelo se portó mal y no devolvió JSON, devolvemos el texto tal cual
        return {
            "assistant_message": raw,
            "script_executed": None,
            "script_result": None,
        }

    answer = data.get("answer", "")
    script_id = data.get("script_to_run")
    run_flag = data.get("run_script", False)
    params = data.get("parameters") or {}

    script_result = None

    if run_flag and script_id == "runShowCommands-main":
        try:
            script_result = run_runShowCommands(params)
        except Exception as e:
            script_result = {
                "error": str(e),
            }
    
    # Combinar el resultado del script dentro del mensaje de la IA
    if script_result is not None:
        # Por si hay error
        if "error" in script_result:
            answer = (
                answer
                + "\n\n--- Script execution failed ---\n"
                + f"Error: {script_result['error']}"
            )
        else:
            answer = (
                answer
                + "\n\n--- Script execution ---\n"
                + f"Return code: {script_result.get('returncode')}\n"
            )
            if script_result.get("stdout"):
                answer += "\nOutput:\n" + script_result["stdout"]
            if script_result.get("stderr"):
                answer += "\nErrors:\n" + script_result["stderr"]

    print("DEBUG RAW FROM MODEL:", raw)
    print("DEBUG SCRIPT_RESULT:", script_result)

    return {
        "assistant_message": answer,
        "script_executed": script_id if run_flag else None,
        "script_result": script_result,
    }
