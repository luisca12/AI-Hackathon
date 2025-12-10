import os, subprocess, sys, json
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI
from strings import scriptsAvailable, SYSTEM_PROMPT

# ========================
# CONFIG INICIAL
# ========================

load_dotenv()
apiKey = os.getenv("OPENAI_API_KEY")
if not apiKey:
    raise RuntimeError("OPENAI_API_KEY not set")

client = OpenAI(apiKey=apiKey)

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

baseScriptDir = os.path.join(os.path.dirname(__file__), "scripts")

lastRunCommandContext = {}

def runScript(scriptID: str, params: dict) -> dict:
    """
    Execute the needed script that is available using subprocess.
    """
    if scriptID not in scriptsAvailable:
        return {"error": f"Unknown scriptID: {scriptID}"}

    info = scriptsAvailable[scriptID]

    folder = info.get("folder")
    entrypoint = info.get("entrypoint", "main.py")
    cliParams = info.get("cliParams", [])

    scriptPath = os.path.join(baseScriptDir, folder, entrypoint)

    cmd = [sys.executable, scriptPath]

    for p in cliParams:
        name = p["name"]         # ejemplo: "devices"
        flag = p["flag"]         # ejemplo: "--devices"
        required = p.get("required", True)

        value = params.get(name)

        if value is None or value == "":
            if required:
                raise ValueError(
                    f"Missing required parameter '{name}' for script '{scriptID}'"
                )
            else:
                continue

        cmd.extend([flag, str(value)])

    script_dir = os.path.dirname(scriptPath)

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

chatHistory = [
    {"role": "system", "content": SYSTEM_PROMPT}
]

@app.post("/chat")
def chatEndpoint(req: ChatRequest):
    global chatHistory, lastRunCommandContext

    messages = chatHistory.copy()

    if lastRunCommandContext:
        contextTxt = (
            "Context of last successful command executed: "
            + json.dumps(lastRunCommandContext)
        )
        messages.append({"role": "system", "content": contextTxt})

    messages.append({"role": "user", "content": req.message})

    response = client.chat.completions.create(
        model="gpt-5-nano",
        messages=messages,
    )

    raw = response.choices[0].message.content

    chatHistory.append({"role": "user", "content": req.message})
    chatHistory.append({"role": "assistant", "content": raw})

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        print("DEBUG JSONDecodeError, raw =", raw)
        return {
            "assistantMessage": raw,
            "scriptExecuted": None,
            "scriptResult": None,
        }

    answer = data.get("answer", "")
    scriptID = data.get("scriptToRun")
    runFlag = data.get("runScript", False)
    params = data.get("parameters") or {}

    scriptResult = None

    if runFlag and scriptID in scriptsAvailable:
        try:
            scriptResult = runScript(scriptID, params)

            # Actualizar contexto si tiene sentido
            if (
                "devices" in params
                and "username" in params
                and "password" in params
            ):
                lastRunCommandContext = {
                    "scriptID": scriptID,
                    "devices": params.get("devices"),
                    "username": params.get("username"),
                    "password": params.get("password"),
                }

        except Exception as e:
            scriptResult = {
                "error": str(e),
            }

    if scriptResult is not None:
        if "error" in scriptResult:
            answer = (
                answer
                + "\n\n--- Script execution failed ---\n"
                + f"Error: {scriptResult['error']}"
            )
        else:
            answer = (
                answer
                + "\n\n--- Script execution ---\n"
                + f"Return code: {scriptResult.get('returncode')}\n"
            )
            if scriptResult.get("stdout"):
                answer += "\nOutput:\n" + scriptResult["stdout"]
            if scriptResult.get("stderr"):
                answer += "\nErrors:\n" + scriptResult["stderr"]

    print("DEBUG RAW FROM MODEL:", raw)
    print("DEBUG scriptID:", scriptID)
    print("DEBUG RUN FLAG:", runFlag)
    print("DEBUG PARAMS:", params)
    print("DEBUG SCRIPT RESULT:", scriptResult)
    print("DEBUG LAST CONTEXT:", lastRunCommandContext)

    return {
        "assistantMessage": answer,
        "scriptExecuted": scriptID if (runFlag and scriptResult is not None) else None,
        "scriptResult": scriptResult,
    }
