import requests

def get_meteo() -> str:
    """Recupera le previsioni meteo attuali tramite Open-Meteo."""
    # Coordinate di Agrigento (puoi cambiarle se ti sposti)
    lat, lon = 37.3111, 13.5765
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,weather_code"

    # Tabella codici meteo WMO semplificata
    weather_descriptions = {
        0: "Cielo sereno ☀️",
        1: "Prevalentemente sereno 🌤️",
        2: "Parzialmente nuvoloso ⛅",
        3: "Nuvoloso ☁️",
        45: "Nebbia 🌫️",
        51: "Pioviggine leggera 🌧️",
        61: "Pioggia 🌧️",
        95: "Temporale ⛈️"
    }

    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            current = data.get("current", {})
            temp = current.get("temperature_2m")
            humidity = current.get("relative_humidity_2m")
            code = current.get("weather_code", 0)
            
            desc = weather_descriptions.get(code, "Condizioni variabili 🌦️")
            
            return (
                f"🌡️ **Meteo ad Agrigento:**\n"
                f"- Situazione: {desc}\n"
                f"- Temperatura: {temp}°C\n"
                f"- Umidità: {humidity}%"
            )
        else:
            return "⚠️ Impossibile recuperare i dati meteo al momento."
    except Exception as e:
        print(f"[Meteo Error] {e}")
        return "⚠️ Errore di connessione al servizio meteo."
