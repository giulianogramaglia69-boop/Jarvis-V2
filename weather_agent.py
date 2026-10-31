import logging
import requests

logger = logging.getLogger(__name__)

class WeatherAgent:
    def __init__(self):
        # Coordinate geografiche di Agrigento
        self.lat = 37.3115
        self.lon = 13.5765
        self.url = f"https://api.open-meteo.com/v1/forecast?latitude={self.lat}&longitude={self.lon}&current=temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,wind_speed_10m"

    def get_agrigento_weather(self) -> str:
        """Scarica i dati meteo aggiornati per Agrigento e restituisce una stringa formattata in Markdown."""
        try:
            response = requests.get(self.url, timeout=10)
            if response.status_code != 200:
                logger.error(f"Errore API Open-Meteo: Status {response.status_code}")
                return "❌ Impossibile recuperare i dati meteo al momento."

            data = response.json().get("current", {})
            temp = data.get("temperature_2m")
            feels_like = data.get("apparent_temperature")
            humidity = data.get("relative_humidity_2m")
            wind_speed = data.get("wind_speed_10m")
            weather_code = data.get("weather_code")

            # Tabella di conversione codici WMO meteo
            weather_descriptions = {
                0: "Cielo sereno ☀️",
                1: "Principalmente sereno 🌤️",
                2: "Parzialmente nuvoloso ⛅",
                3: "Coperto ☁️",
                45: "Nebbia 🌫️",
                48: "Nebbia con brina ❄️",
                51: "Pioviggine leggera 🌧️",
                53: "Pioviggine moderata 🌧️",
                55: "Pioviggine densa 🌧️",
                61: "Pioggia debole 🌧️",
                63: "Pioggia moderata 🌧️",
                65: "Pioggia forte 🌧️ torrentizia",
                71: "Neve debole 🌨️",
                80: "Rovesci di pioggia 🌦️",
                95: "Temporale ⚡"
            }
            
            condition = weather_descriptions.get(weather_code, "Variabile 🌦️")

            report = (
                f"🌤️ **Meteo ad Agrigento**\n\n"
                f"🌡️ **Temperatura:** {temp}°C (Percepita: {feels_like}°C)\n"
                f"💧 **Umidità:** {humidity}%\n"
                f"💨 **Vento:** {wind_speed} km/h\n"
                f"☁️ **Condizioni:** {condition}"
            )
            return report

        except Exception as e:
            logger.error(f"Eccezione durante la richiesta meteo: {e}")
            return "❌ Errore di connessione al servizio meteo."
