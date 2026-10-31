import os
import logging
import shutil

logger = logging.getLogger(__name__)

class SystemMonitorAgent:
    def __init__(self):
        pass

    def get_cpu_temperature(self) -> str:
        """Legge la temperatura del SoC del Raspberry Pi."""
        try:
            # Percorso standard per la temperatura su Raspberry Pi OS
            temp_path = "/sys/class/thermal/thermal_zone0/temp"
            if os.path.exists(temp_path):
                with open(temp_path, "r") as f:
                    temp_millidegrees = int(f.read().strip())
                    return f"{temp_millidegrees / 1000.0:.1°C}"
        except Exception as e:
            logger.error(f"Errore lettura temperatura CPU: {e}")
        return "N/D"

    def get_memory_usage(self) -> dict:
        """Legge l'utilizzo della RAM tramite /proc/meminfo (senza librerie esterne pesanti)."""
        mem_info = {}
        try:
            with open("/proc/meminfo", "r") as f:
                for line in f:
                    parts = line.split()
                    if len(parts) >= 2:
                        # I valori in meminfo sono in kB
                        mem_info[parts[0].rstrip(":")] = int(parts[1])
            
            total_kb = mem_info.get("MemTotal", 0)
            free_kb = mem_info.get("MemFree", 0)
            buffers_kb = mem_info.get("Buffers", 0)
            cached_kb = mem_info.get("Cached", 0)
            
            # RAM effettivamente disponibile
            available_kb = free_kb + buffers_kb + cached_kb
            used_kb = total_kb - available_kb
            
            total_mb = total_kb / 1024
            used_mb = used_kb / 1024
            percentage = (used_kb / total_kb) * 100 if total_kb > 0 else 0
            
            return {
                "total": f"{total_mb:.1f} MB",
                "used": f"{used_mb:.1f} MB",
                "percent": f"{percentage:.1f}%"
            }
        except Exception as e:
            logger.error(f"Errore lettura memoria: {e}")
            return {"total": "N/D", "used": "N/D", "percent": "0%"}

    def get_disk_usage(self, path: str = "/") -> dict:
        """Controlla lo spazio disponibile sulla microSD o sul file system."""
        try:
            total, used, free = shutil.disk_usage(path)
            total_gb = total / (2**30)
            used_gb = used / (2**30)
            free_gb = free / (2**30)
            percentage = (used / total) * 100
            
            return {
                "total": f"{total_gb:.1f} GB",
                "used": f"{used_gb:.1f} GB",
                "free": f"{free_gb:.1f} GB",
                "percent": f"{percentage:.1f}%"
            }
        except Exception as e:
            logger.error(f"Errore lettura disco: {e}")
            return {"total": "N/D", "used": "N/D", "free": "N/D", "percent": "0%"}

    def get_system_report(self) -> str:
        """Genera un report testuale formattato in Markdown pronto per Telegram."""
        temp = self.get_cpu_temperature()
        mem = self.get_memory_usage()
        disk = self.get_disk_usage("/")

        report = (
            f"🖥️ **System Monitor — Raspberry Pi Zero**\n\n"
            f"🌡️ **Temperatura CPU:** {temp}\n"
            f"🧠 **RAM Usata:** {mem['used']} / {mem['total']} ({mem['percent']})\n"
            f"💾 **MicroSD (Root):** {disk['used']} usati su {disk['total']} ({disk['free']} liberi - {disk['percent']})"
        )
        return report
