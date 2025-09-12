#####################################################################################################
#                   S T R O M V E R B R A U C H  U N D  K O S T E N                                 #
#                                                                                                   #
# Das Programm überwacht in Echtzeit den Stromverbrauch von CPU und GPU,                            #
# berechnet die Kosten basierend auf dem aktuellen Strompreis und stellt diese Daten                #
# in einer übersichtlichen grafischen Darstellung dar.                                              #
#####################################################################################################

# Import der benötigten Bibliotheken
import subprocess
import time
import os
from colorama import init, Fore, Style
import sys
import pynvml
import psutil
from datetime import datetime, timedelta
import requests
import threading
from statistics import mean
import logging
import tempfile
import ctypes
import math

# Funktion für den Startton
def play_start_sound():
    try:
        import winsound
        winsound.Beep(1000, 200)
        winsound.Beep(1500, 200)
        winsound.Beep(2000, 300)
    except ImportError:
        print("Startton nicht verfügbar auf diesem System.")

# Funktion, um den Fenstertitel zu setzen
def set_window_title(title):
    if os.name == 'nt':
        ctypes.windll.kernel32.SetConsoleTitleW(title)

# Initialisierung
init()
pynvml.nvmlInit()

# Globale Variablen
log_file = os.path.join(tempfile.gettempdir(), 'stromverbrauch.log')
logging.basicConfig(filename=log_file, level=logging.INFO, format='%(asctime)s %(message)s')

history = []
power_readings = []

current_price = None
price_source = "Nicht initialisiert"
price_provider = "Nicht initialisiert"

total_power_consumption = 0
total_cost_since_start = 0
peak_power = 0
start_time = time.time()
last_update_time = start_time

# Funktion, um den aktuellen Strompreis von einer API zu erhalten
def get_current_price():
    global current_price, price_source, price_provider
    try:
        response = requests.get("https://apis.smartenergy.at/market/v1/price")
        if response.status_code == 200:
            data = response.json()
            now = datetime.now()
            current_price_data = next((item for item in data['data'] if datetime.fromisoformat(item['date']).replace(tzinfo=None) <= now < datetime.fromisoformat(item['date']).replace(tzinfo=None) + timedelta(minutes=15)), None)
            if current_price_data:
                epex_spot_price = current_price_data['value'] / 100
                current_price = (current_price_data['value'] + 1.44) / 100
                price_source = "API"
                price_provider = "smartENERGY"
            else:
                raise ValueError("Kein gültiger Preis gefunden.")
        else:
            raise ConnectionError(f"Fehler beim Abrufen: {response.status_code}")
    except Exception as e:
        current_price = 0.33
        price_source = "Standard"
        price_provider = "EPEX"
        logging.error(f"Fehler beim Abrufen des Strompreises: {e}")
    return current_price

# Periodische Aktualisierung des Strompreises
def update_price_periodically():
    while True:
        get_current_price()
        time.sleep(900)

threading.Thread(target=update_price_periodically, daemon=True).start()

# Funktion zur Anzeige großer Ziffern in ASCII-Art
def big_digits(number):
    digits = {
        '0': ['  ●●●  ', ' ●   ● ', '●     ●', '●     ●', '●     ●', ' ●   ● ', '  ●●●  '],
        '1': ['   ●   ', '  ●●   ', '   ●   ', '   ●   ', '   ●   ', '   ●   ', ' ●●●●● '],
        '2': [' ●●●●● ', '●     ●', '      ●', ' ●●●●● ', '●      ', '●      ', '●●●●●●'],
        '3': [' ●●●●● ', '●     ●', '      ●', ' ●●●●● ', '      ●', '●     ●', ' ●●●●● '],
        '4': ['●     ●', '●     ●', '●     ●', '●●●●●●●', '      ●', '      ●', '      ●'],
        '5': ['●●●●●●', '●      ', '●      ', '●●●●●●', '      ●', '●     ●', ' ●●●●●'],
        '6': [' ●●●●●', "●      ", "●      ", "●●●●●● ", "●     ●", "●     ●", " ●●●●●"],
        '7': ['●●●●●●', "     ● ", "    ●  ", "   ●   ", "   ●   ", "  ●    ", "  ●    "],
        '8': [' ●●●●● ', "●     ●", "●     ●", " ●●●●● ", "●     ●", "●     ●", " ●●●●"],
        '9': [' ●●●●●', "●     ●", "●     ●", " ●●●● ", "      ●", "●     ●", " ●●●●"],
        '.': ['       ', '       ', '       ', '       ', '       ', '   ●   ', '       '],
        '€': ['  ●●● ', ' ●    ', '●●●●  ', ' ●    ', '  ●●● ', '      ', '      '],
        'w': ['●     ●', ' ● ● ● ', '  ● ●  ', '       ', '       ', '       ', '       ']
    }
    lines = [''] * 7
    for digit in number:
        if digit not in digits:
            digit = ' '  # Fallback für unbekannte Zeichen
        for i in range(7):
            lines[i] += digits[digit][i].ljust(8)  # Einheitliche Breite
    return lines

# Funktion, um den Stromverbrauch des Systems zu messen
def get_system_power():
    try:
        handle = pynvml.nvmlDeviceGetHandleByIndex(0)
        gpu_power = pynvml.nvmlDeviceGetPowerUsage(handle) / 1000
        cpu_usage = psutil.cpu_percent()
        cpu_power = (cpu_usage / 100) * 65
        return cpu_power + gpu_power
    except Exception as e:
        logging.warning(f"Fehler beim Abrufen des Stromverbrauchs: {e}")
        return 0

# Funktion, um Kosten basierend auf Verbrauch und Dauer zu berechnen
def calculate_cost(power, duration_seconds):
    energy_consumed = (power / 1000) * (duration_seconds / 3600)
    return energy_consumed * current_price if current_price else 0

# Funktion, um die Gesamtkosten zu berechnen
def calculate_total_cost(total_consumption):
    return total_consumption * current_price if current_price else 0

# Funktion zur Formatierung der Laufzeit
def format_duration(seconds):
    return str(timedelta(seconds=int(seconds)))

# Funktion, um Leistungsdaten und Kosten auszugeben
def print_power():
    global peak_power, total_power_consumption, last_update_time, total_cost_since_start

    current_time = time.time()
    elapsed_time = current_time - last_update_time

    power = get_system_power()
    if power:
        peak_power = max(peak_power, power)
        energy_consumed = (power / 1000) * (elapsed_time / 3600)
        total_power_consumption += energy_consumed * 1000
        cost_since_last_update = calculate_cost(power, elapsed_time)
        total_cost_since_start += cost_since_last_update

        output = "".join(Fore.GREEN + line + "\n" for line in big_digits(f"{total_cost_since_start:.2f}€"))
        output += f"\n{Fore.YELLOW}Aktueller Verbrauch: {power:.2f} W\n"
        output += f"Spitzenwert: {peak_power:.2f} W\n"
        output += f"Gesamtkosten: {total_cost_since_start:.2f} €\n"

        # Ausgabe des Spitzenwertes in Rot mit kleinem "w" direkt daneben
        peak_and_unit = f"{math.ceil(peak_power):.0f}w"
        peak_output = "".join(Fore.RED + line + "\n" for line in big_digits(peak_and_unit))
        peak_output += f"{Fore.RED}Spitzenwert\n"

        sys.stdout.write("\033[H\033[J")
        sys.stdout.write(output)
        sys.stdout.write(peak_output)
        sys.stdout.flush()

        last_update_time = current_time
    else:
        print("Daten konnten nicht abgerufen werden.")

# Hauptfunktion
def main():
    get_current_price()
    set_window_title("Stromverbrauch und Kosten")
    play_start_sound()
    try:
        while True:
            print_power()
            time.sleep(1)
    except KeyboardInterrupt:
        print("Programm beendet.")
    finally:
        pynvml.nvmlShutdown()

if __name__ == "__main__":
    main()
