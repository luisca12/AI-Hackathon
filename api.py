import os, subprocess, shlex, sys
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI

# Cargar variables de entorno (.env)
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise RuntimeError("OPENAI_API_KEY not set")

client = OpenAI(api_key=api_key)

# Inicializar FastAPI
app = FastAPI(
    title="NetOps: AI-Powered Automation Solution",
    description="Simple backend for a ChatGPT-style NetOps assistant.",
)

# CORS para poder llamar desde el HTML (localhost)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],      # en producción deberías restringir esto
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modelo de entrada del chat
class ChatRequest(BaseModel):
    message: str

# Catálogo de scripts LOCALES disponibles
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
        lines.append("")  # línea en blanco
    return "\n".join(lines)

scriptCatalogTextOut = scriptCatalogText()

SYSTEM_PROMPT = f"""
Your name is Automation Hero, yuou're an AI-powered automation assistant for network and operations engineers.

We are going to follow the rules/instructions defined on:
- Rules about the first message 
- General Rules
- Rules about scripts
- Your job for now is

Rules about the first message:
- The first message should be a short greeting and ask what they would like to do.
- You can suggest that you can list available scripts or running a specific script, but do not prompt it on the first message

Generale rules:
- All the replies must have a nice and human readable format.
- Only prompt the available scripts if the user ask for it
- Keep answers technical but easy to understand and short, don't put too much text, keep things simple.
- When the user asks about the available scripts, only show the name and description, no need to put the ID and parameters section yet.
- When the user wants to run a specific script, only then you can show and ask for the parameters
- Use a human readable format when presenting the available scripts or any reply
- Do not ask for what ID the user would like to run, instead, prompt something more user friendly like "what script would you like to run?"

You have access to exactly the following local scripts (identified by their ID):

{scriptCatalogTextOut}

Rules about scripts:
- When the user asks about "available scripts", you MUST list ONLY these scripts, using their IDs and descriptions.
- NEVER invent or mention scripts that are not in the catalog above.
- If the user mentions a script that is not in the catalog, tell them that script is not available and suggest one of the existing ones.
- Later, the backend will use the script ID to execute the corresponding local Python automation.

Your job for now is:
- Answer questions clearly and concisely.
- Help the user understand what scripts exist in the catalog above and how to use them.
- Ask for any parameters required by a script (devices, username, password, commands, etc.) before execution.
- Do NOT say that you executed a script yourself; you only propose which script to run and with which parameters.
- Do NOT propose running any script without explicit confirmation from the user.

"""

@app.post("/chat")
def chatEndpoint(req: ChatRequest):
    """
    Simple chat endpoint:
    - Receives a user message.
    - Sends it to OpenAI with a system prompt.
    - Returns the assistant message.
    """
    response = client.chat.completions.create(
        model="gpt-5-nano",  # tu modelo actual
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": req.message},
        ],
        # temperature=0.2,
    )

    assistant_message = response.choices[0].message.content
    return {"assistant_message": assistant_message}

baseScriptDir = os.path.join(os.path.dirname(__file__), "scripts")

def run_runShowCommands(params: dict) -> dict:
    devices = params["devices"]           # "10.1.1.1,10.1.1.2"
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

    # Opcional: poner cwd en la carpeta del script para que logs/Outputs se
    # creen ahí dentro
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