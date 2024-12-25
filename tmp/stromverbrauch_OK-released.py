#####################################################################################################
#                   S T R O M V E R B R A U C H  U N D  K O S T E N                                 #
#                                                                                                   #
# Das Programm überwacht in Echtzeit den Stromverbrauch von CPU und GPU,                            #
# berechnet die Kosten basierend auf dem aktuellen Strompreis und stellt diese Daten                #
# in einer übersichtlichen grafischen Darstellung dar.                                              #
# Korrekturen:                                                                                      #
#    jn 14.12.2024                                                                                  #
#    Die Gesamtkosten werden jetzt korrekt für die Zeit seit der letzten Aktualisierung berechnet.  #
#    Die Ausgabe der Gesamtkosten sollte realistische Werte anzeigen.                               #
#    Das Problem ist, dass dies die gesamte Zeit seit dem Start verwendet wurde, was dazu führt,    #
#    dass die Kosten immer weiter anstiegen, obwohl nur die Differenz zur letzten                   #
#    Messung relevant ist.                                                                          #
#                                                                                                   #
#    Jetzt mit Fenstertitel 14.12.2024 08:41                                                        #
#                                                                                                   #
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
last_log_time = start_time

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
        '0': [
            ' ●●● ',
            '●   ●',
            '●   ●',
            '●   ●',
            ' ●●● '
        ],
        '1': [
            '  ●  ',
            ' ●●  ',
            '  ●  ',
            '  ●  ',
            ' ●●● '
        ],
        '2': [
            ' ●●● ',
            '    ●',
            ' ●●● ',
            '●    ',
            ' ●●● '
        ],
        '3': [
            ' ●●● ',
            '    ●',
            ' ●●● ',
            '    ●',
            ' ●●● '
        ],
        '4': [
            '●   ●',
            '●   ●',
            ' ●●● ',
            '    ●',
            '    ●'
        ],
        '5': [
            ' ●●● ',
            '●    ',
            ' ●●● ',
            '    ●',
            ' ●●● '
        ],
        '6': [
            ' ●●● ',
            '●    ',
            ' ●●● ',
            '●   ●',
            ' ●●● '
        ],
        '7': [
            ' ●●● ',
            '    ●',
            '    ●',
            '    ●',
            '    ●'
        ],
        '8': [
            ' ●●● ',
            '●   ●',
            ' ●●● ',
            '●   ●',
            ' ●●● '
        ],
        '9': [
            ' ●●● ',
            '●   ●',
            ' ●●● ',
            '    ●',
            ' ●●● '
        ],
        '.': [
            '     ',
            '     ',
            '     ',
            '     ',
            '  ●  '
        ],
        '€': [
            ' ●●● ',
            '●    ',
            '●●● ',
            '●    ',
            ' ●●● '
        ],
        'w': [
            '      ',
            '      ',
            '● ● ●',
            ' ●●● ',
            ' ● ● '
        ]
    }
    lines = [''] * 5
    for digit in number:
        if digit not in digits:
            digit = ' '  # Fallback für unbekannte Zeichen
        for i in range(5):
            lines[i] += digits[digit][i].ljust(7)  # Einheitliche Breite
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
    global peak_power, total_power_consumption, last_update_time, total_cost_since_start, last_log_time

    current_time = time.time()
    elapsed_time = current_time - last_update_time

    power = get_system_power()

    history.append(power)
    power_readings.append(power)
    if len(history) > 15:
        history.pop(0)
    if len(power_readings) > 60:
        power_readings.pop(0)

    avg_power = mean(power_readings)

    if power:
        peak_power = max(peak_power, power)
        energy_consumed = (power / 1000) * (elapsed_time / 3600)
        total_power_consumption += energy_consumed * 1000
        cost_since_last_update = calculate_cost(power, elapsed_time)
        total_cost_since_start += cost_since_last_update

        # Prüfen, ob 15 Minuten seit der letzten Protokollierung vergangen sind
        if current_time - last_log_time >= 900:  # 900 Sekunden = 15 Minuten
            # Logge die Gesamtkosten der aktuellen Sitzung sowie weitere relevante Werte
            logging.info(f"Gesamtkosten der Sitzung: {total_cost_since_start:.3f} Euro | "
                         f"Aktueller Verbrauch: {power:.2f} Watt | "
                         f"Laufzeit: {format_duration(current_time - start_time)} | "
                         f"Aktueller Strompreis: {current_price:.3f} €/kWh")
            last_log_time = current_time  # Aktualisiere den Zeitpunkt der letzten Protokollierung

        output = "".join(Fore.GREEN + line + "\n" for line in big_digits(f"{total_cost_since_start:.3f}€"))
        output += f"\n{Fore.YELLOW}Zeit:  {format_duration(current_time - start_time)}"
        # output += f"\n{Fore.YELLOW}Aktueller Verbrauch: {power:.2f} W\n"
        average_symbol = "ø"
        output += f"\n{Fore.YELLOW}Watt:  {power:.2f} {average_symbol} {avg_power:.2f}\n"
        output += f"{Fore.YELLOW + Style.NORMAL}Preis: {current_price:.3f} EUR/kWh {Fore.LIGHTBLACK_EX + Style.DIM}\nQuelle:{price_provider}\n\n"
        peak_and_unit = f"{math.ceil(peak_power):.0f}w"
        peak_output = f"{Fore.RED + Style.DIM} Spitzenwert\n"
        peak_output += f"{Style.RESET_ALL}"
        peak_output += "".join(Fore.RED + line + "\n" for line in big_digits(peak_and_unit))
        output += f"{Style.RESET_ALL}"

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
    set_window_title("S t r o m v e r b r a u c h")
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
