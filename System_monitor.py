import psutil

def get_system_status() -> str:
    """Monitora lo stato delle risorse hardware del Raspberry Pi Zero."""
    try:
        cpu_usage = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        ram_usage = memory.percent
        ram_free_mb = memory.available / (1024 * 1024)

        # Temperatura CPU (funziona nativamente su Linux/Raspberry Pi)
        temp_str = "N/A"
        if hasattr(psutil, "sensors_temperatures"):
            temps = psutil.sensors_temperatures()
            if temps:
                for name, entries in temps.items():
                    for entry in entries:
                        if entry.current:
                            temp_str = f"{entry.current}°C"
                            break

        return (
            f"📊 **Stato Sistema (Jarvis Core):**\n"
            f"- 🧠 CPU: {cpu_usage}%\n"
            f"- 🌡️ Temp SoC: {temp_str}\n"
            f"- 💾 RAM Usata: {ram_usage}% ({ram_free_mb:.0f} MB liberi)"
        )
    except Exception as e:
        print(f"[System Monitor Error] {e}")
        return "⚠️ Impossibile leggere le metriche di sistema."
