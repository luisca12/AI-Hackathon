scriptsAvailable = {
    "runShowCommands-main": {
        "displayName": "Run Show Commands",
        "description": (
            "Execute any show command on one or multiple network devices using SSH. "
            "Validates reachability, runs the command and stores outputs in text files under Outputs."
        ),
        # Metadatos para el backend:
        "folder": "runShowCommands-main",
        "entrypoint": "main.py",
        "cli_params": [
            {"name": "devices",  "flag": "--devices",  "required": True},
            {"name": "username", "flag": "--username", "required": True},
            {"name": "password", "flag": "--password", "required": True},
            # <- SOLO este script usa "command"
            {"name": "command",  "flag": "--command",  "required": True},
        ],
        # Info para el modelo (sigue igual, la IA ve esto al armar prompts):
        "parameters": [
            {"name": "devices", "description": "Comma-separated list of device IPs/hostnames"},
            {"name": "username", "description": "Username for device login"},
            {"name": "password", "description": "Password (also used as enable/secret)"},
            {"name": "command", "description": "Complete show command to run"},
        ],
    },

    "aclRemoval-main": {
        "displayName": "ACL Removal in SNMP Group",
        "description": "Remove or modify SNMP Group ACL on multiple devices.",
        "folder": "aclRemoval-main",
        "entrypoint": "main.py",
        "cli_params": [
            {"name": "devices", "flag": "--devices", "required": True},
            {"name": "username", "flag": "--username", "required": True},
            {"name": "password", "flag": "--password", "required": True},
        ],
        "parameters": [
            {"name": "devices", "description": "Devices where the SNMP Group ACL will be modified"},
            {"name": "username", "description": "Username for device login"},
            {"name": "password", "description": "Password (also used as enable/secret)"},
        ],
    },

    "shIntStatHalf_SD-WAN-main": {
        "displayName": "Half Duplex Check (SD-WAN)",
        "description": "Check interfaces in half-duplex mode on SD-WAN routers.",
        "folder": "shIntStatHalf_SD-WAN-main",
        "entrypoint": "main.py",
        "cli_params": [
            {"name": "devices", "flag": "--devices", "required": True},
        ],
        "parameters": [
            {"name": "devices", "description": "Routers to check"},
        ],
    },

    "showErrDisableInt-main": {
        "displayName": "Err-Disabled Interfaces",
        "description": "Find interfaces in err-disabled state and optionally recover them.",
        "folder": "showErrDisableInt-main",
        "entrypoint": "main.py",
        "cli_params": [
            {"name": "devices", "flag": "--devices", "required": True},
        ],
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
- ALl the replies must alsto be in a happy-positive tone, you may use emojis when u think it's good to use them
- On the first message also mention your name, Automation Hero
- For any message, if you are going to present a list of things, please use bullet points or something to make it nicer and more readable.
- If you will reply with a list of things or missing parameters, use a clear multi-line format, not everything on the same line.
- If they ask you to run more than one show command, just execute one at a time, and always prompt something like "do u want to run the next command?" and also show the next command

Very important:
- If you are NOT ready to execute (need more info or no explicit confirmation), set "run_script": false.
- If the user changes their mind or says "do not run it", keep "run_script": false.
- Never say that you executed the script yourself; you only request execution through this JSON.

Additional rule about context:
- You may receive a system message like:
  "Context of last successful command executed: { ... }"
- If the user says "same device", "same router", "same credentials",
  or asks for another command without specifying devices/username/password,
  you MUST reuse those values from the context unless the user overrides them.

Remember: respond ONLY with JSON. No text before or after the JSON.
"""
