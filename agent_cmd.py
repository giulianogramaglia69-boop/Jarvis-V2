import subprocess

# Dizionario dei comandi sicuri pre-approvati che Jarvis può lanciare sul Raspberry Pi
ALLOWED_COMMANDS = {
    "uptime": "uptime",
    "disk": "df -h /",
    "memory": "free -m",
    "docker": "docker ps --format 'table {{.Names}}\t{{.Status}}'",
    "temp": "vcgencmd measure_temp 2>/dev/null || cat /sys/class/thermal/thermal_zone0/temp",
    "services": "systemctl list-units --type=service --state=running"
}

def run_system_command(user_input: str) -> str:
    """
    Interpreta la richiesta dell'utente ed esegue il comando di sistema associato,
    restituendo l'output formattato per Telegram.
    """
    user_input_lower = user_input.lower()
    
    # Cerca quale comando consentito corrisponde alla richiesta
    cmd_to_run = None
    matched_key = None
    
    for key, cmd in ALLOWED_COMMANDS.items():
        if key in user_input_lower:
            cmd_to_run = cmd
            matched_key = key
            break
            
    if not cmd_to_run:
        return (
            "⚙️ **Comando di sistema non riconosciuto o non sicuro.**\n\n"
            "Puoi chiedermi di verificare:\n"
            "- `uptime` (Tempo di attività)\n"
            "- `disk` (Spazio su disco)\n"
            "- `memory` (Uso della RAM)\n"
            "- `docker` (Container attivi)\n"
            "- `temp` (Temperatura CPU)\n"
            "- `services` (Servizi attivi)"
        )
        
    try:
        # Esegue il comando in modo sicuro sul Raspberry Pi
        output = subprocess.check_output(
            cmd_to_run, 
            shell=True, 
            text=True, 
            stderr=subprocess.STDOUT, 
            timeout=10
        )
        
        # Gestione speciale per la temperatura se legge il file di sistema
        if matched_key == "temp" and "sys/class" in cmd_to_run:
            try:
                temp_val = int(output.strip()) / 1000.0
                output = f"CPU Temperature: {temp_val:.1f}°C"
            except:
                pass

        return f"💻 **Output comando (`{matched_key}`):**\n```\n{output.strip()}\n```"
        
    except subprocess.TimeoutExpired:
        return "❌ Il comando ha impiegato troppo tempo a rispondere."
    except subprocess.CalledProcessError as e:
        return f"❌ Errore durante l'esecuzione del comando:\n```\n{e.output.strip()}\n```"
    except Exception as e:
        return f"❌ Errore inatteso: {str(e)}"
