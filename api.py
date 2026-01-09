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

baseScriptDir = os.path.join(os.path.dirname(__file__), "scripts")

# Contexto del último comando exitoso (para "same device", etc.)
lastRunCommandContext = {}

def runScript(scriptID: str, params: dict) -> dict:
    """
    Ejecuta cualquier script definido en scriptsAvailable usando subprocess.
    """
    if scriptID not in scriptsAvailable:
        return {"error": f"Unknown scriptID: {scriptID}"}

    info = scriptsAvailable[scriptID]

    folder = info.get("folder")
    entrypoint = info.get("entrypoint", "main.py")
    cli_params = info.get("cli_params", [])

    script_path = os.path.join(baseScriptDir, folder, entrypoint)

    cmd = [sys.executable, script_path]

    # Agregar parámetros CLI según la definición
    for p in cli_params:
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

chatHistory = [
    {"role": "system", "content": SYSTEM_PROMPT}
]

@app.post("/chat")
def chatEndpoint(req: ChatRequest):
    global chatHistory, lastRunCommandContext

    # Construir mensajes para este request
    messages = chatHistory.copy()

    # Inyectar contexto del último comando, si existe
    if lastRunCommandContext:
        context_text = (
            "Context of last successful command executed: "
            + json.dumps(lastRunCommandContext)
        )
        messages.append({"role": "system", "content": context_text})

    # Mensaje actual del usuario
    messages.append({"role": "user", "content": req.message})

    # Llamar al modelo
    response = client.chat.completions.create(
        model="gpt-5-nano",
        messages=messages,
        # response_format={"type": "json_object"},  # si tu modelo lo soporta
    )

    raw = response.choices[0].message.content

    # Guardar en historial (para próximas vueltas)
    chatHistory.append({"role": "user", "content": req.message})
    chatHistory.append({"role": "assistant", "content": raw})

    # Parsear JSON
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        # Modelo se portó mal; devolvemos el texto tal cual
        print("DEBUG JSONDecodeError, raw =", raw)
        return {
            "assistant_message": raw,
            "script_executed": None,
            "script_result": None,
        }

    answer = data.get("answer", "")
    scriptID = data.get("script_to_run")
    run_flag = data.get("run_script", False)
    params = data.get("parameters") or {}

    script_result = None

    # Ejecutar script si corresponde
    if run_flag and scriptID in scriptsAvailable:
        try:
            script_result = runScript(scriptID, params)

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
            script_result = {
                "error": str(e),
            }

    # Combinar resultado del script en el mensaje que verá el usuario
    if script_result is not None:
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

    # Logs de debug en consola del backend
    print("DEBUG RAW FROM MODEL:", raw)
    print("DEBUG scriptID:", scriptID)
    print("DEBUG RUN_FLAG:", run_flag)
    print("DEBUG PARAMS:", params)
    print("DEBUG SCRIPT_RESULT:", script_result)
    print("DEBUG LAST_CONTEXT:", lastRunCommandContext)

    return {
        "assistant_message": answer,
        "script_executed": scriptID if (run_flag and script_result is not None) else None,
        "script_result": script_result,
    }