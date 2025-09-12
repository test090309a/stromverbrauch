#####################################################################################################
#                   S T R O M V E R B R A U C H  U N D  K O S T E N                                 #
#                                                                                                   #
# Dieses Programm überwacht in Echtzeit den Stromverbrauch von CPU und GPU,                          #
# berechnet die Kosten basierend auf dem aktuellen Strompreis und stellt diese Daten                #
# in einer übersichtlichen grafischen Darstellung dar.                                              #
#                                                                                                   #
# Korrekturen:                                                                                      #
#    jn 14.12.2024                                                                                  #
#    Die Gesamtkosten werden jetzt korrekt für die Zeit seit der letzten Aktualisierung berechnet.  #
#    Die Ausgabe der Gesamtkosten zeigt nun realistische Werte an.                                  #
#    Es wurde das Problem behoben, dass die Kosten seit dem Start weiteranstiegen.                   #
#                                                                                                   #
#    Fenstertitel wurde aktualisiert am 14.12.2024 08:41                                            #
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
import winsound
import math

# Funktion zum Abspielen eines Starttons
def play_start_sound():
    winsound.Beep(1000, 200)
    winsound.Beep(1500, 200)
    winsound.Beep(2000, 300)

# Funktion zum Setzen des Fenstertitels
def set_window_title(title):
    if os.name == 'nt':
        ctypes.windll.kernel32.SetConsoleTitleW(title)

# Pfad zur Logdatei im temporären Verzeichnis
log_file = os.path.join(tempfile.gettempdir(), 'stromverbrauch.log')
# Konfiguration des Logging-Moduls
logging.basicConfig(filename=log_file, level=logging.INFO, format='%(asctime)s %(message)s')

# Initialisierung von colorama für farbige Ausgabe im Terminal
init()
# Initialisierung von pynvml für NVIDIA-GPU-Monitoring
pynvml.nvmlInit()

# Globale Variablen für Historie, Leistungsdaten, Startzeit, etc.
history = []
power_readings = []

current_price = None
epex_spot_price = None
smartenergy_price = None
price_source = "Nicht initialisiert"
price_provider = "Nicht initialisiert"

start_time = time.time()
last_update_time = start_time

peak_power = 0
total_power_consumption = 0
total_cost_since_start = 0

# Funktion zum Abrufen des aktuellen Strompreises von einer API
def get_current_price():
    global current_price, price_source, epex_spot_price, smartenergy_price, price_provider
    try:
        response = requests.get("https://apis.smartenergy.at/market/v1/price")
        if response.status_code == 200:
            data = response.json()
            now = datetime.now()
            # Suche des aktuellen Preises basierend auf der aktuellen Zeit
            current_price_data = next((item for item in data['data'] if datetime.fromisoformat(item['date']).replace(tzinfo=None) <= now < datetime.fromisoformat(item['date']).replace(tzinfo=None) + timedelta(minutes=15)), None)
            if current_price_data:
                epex_spot_price = current_price_data['value'] / 100
                smartenergy_price = (current_price_data['value'] + 1.44) / 100
                current_price = smartenergy_price
                price_source = "API"
                price_provider = "smartENERGY"
            else:
                current_price = 0.33
                epex_spot_price = 0.3156
                smartenergy_price = 0.33
                price_source = "Standard"
                price_provider = "EPEX"
        else:
            current_price = 0.33
            epex_spot_price = 0.3156
            smartenergy_price = 0.33
            price_source = "Standard"
            price_provider = "EPEX"
    except Exception as e:
        current_price = 0.33
        epex_spot_price = 0.3156
        smartenergy_price = 0.33
        price_source = "Standard"
        price_provider = "EPEX"
    return current_price

# Funktion zur periodischen Aktualisierung des Strompreises
def update_price_periodically():
    while True:
        get_current_price()
        time.sleep(900)  # Aktualisierung alle 15 Minuten

# Start eines separaten Threads für die Preisaktualisierung
price_thread = threading.Thread(target=update_price_periodically, daemon=True)
price_thread.start()

# Funktion zur Darstellung großer Ziffern in ASCII-Art
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
        '8': [' ●●●●● ', "●     ●", "●     ●", " ●●●● ", "●     ●", "●     ●", " ●●●●"],
        '9': [' ●●●●●', "●     ●", "●     ●", " ●●●● ", "      ●", "●     ●", " ●●●●"],
        '.': ['       ', '       ', '       ', '       ', '       ', '   ●   ', '       '],
        '€': [' ●●● ', '● ', '●●●● ', '● ', ' ●●● ', ' ', ' '],
        'W': ['●   ●', '●   ●', ' ●●● ', ' ● ● ', '', ' ', ' ']
    }
    lines = [''] * 7
    for digit in number:
        for i in range(7):
            lines[i] += digits.get(digit, [' '] * 7)[i] + ' '
    return lines

# Funktion zum Abrufen des aktuellen Systemstromverbrauchs (CPU + GPU)
def get_system_power():
    try:
        handle = pynvml.nvmlDeviceGetHandleByIndex(0)
        gpu_power = pynvml.nvmlDeviceGetPowerUsage(handle) / 1000  # Umrechnen in Watt
        cpu_usage = psutil.cpu_percent()
        cpu_max_power = 65  # Annahme der maximalen CPU-Leistung in Watt
        cpu_power = (cpu_usage / 100) * cpu_max_power
        system_power = cpu_power + gpu_power
        return system_power
    except:
        return None

# Funktion zum Berechnen der Kosten basierend auf Leistung und Dauer
def calculate_cost(power, duration_seconds):
    global current_price
    if current_price is None:
        get_current_price()
    energy_consumed = (power / 1000) * (duration_seconds / 3600)  # Umrechnen in kWh
    cost = energy_consumed * current_price
    return cost

# Funktion zum Berechnen der Gesamtkosten basierend auf Gesamtleistung
def calculate_total_cost(total_consumption):
    global current_price
    if current_price is None:
        get_current_price()
    return total_consumption * current_price

# Funktion zum Formatieren einer Dauer in einer lesbaren Form
def format_duration(seconds):
    return str(timedelta(seconds=int(seconds)))

# Funktion zum Schreiben von Daten in die Logdatei
def log_data(duration, total_consumption, peak_power):
    logging.info(f"{datetime.now()}, Dauer: {duration}, Gesamtverbrauch: {total_consumption:.2f} Wh, Spitzenwert: {peak_power:.2f} Watt, Kosten: {total_cost_since_start:.2f} Euro")

# Funktion zum Erstellen eines Balkendiagramms der Leistungsdaten
def draw_power_chart(history):
    if not history:
        return ''
    max_power = max(history)
    min_power = min(history)
    range_power = max_power - min_power if max_power != min_power else 1
    barchart_height = 5
    chart = []
    for zeile in range(barchart_height, 0, -1):
        threshold = min_power + (range_power * (zeile - 1) / barchart_height)
        line = ''
        for power in history:
            if power >= threshold:
                line += f' {Fore.RED + Style.NORMAL}\u25CF{Style.RESET_ALL} '
            else:
                line += ' '
        chart.append(line)
    return '\n'.join(chart)

# Hauptfunktion zum Ausgeben von Leistungsdaten und Kosten
def print_power():
    global peak_power, total_power_consumption, power_readings, total_cost_since_start, current_price, price_source, price_provider, last_update_time

    current_time = time.time()
    elapsed_time = current_time - last_update_time

    power = get_system_power()
    if power is not None:
        peak_power = max(peak_power, power)
        energy_consumed = (power / 1000) * (elapsed_time / 3600)
        total_power_consumption += energy_consumed * 1000
        cost_since_last_update = calculate_cost(power, elapsed_time)
        total_cost_since_start += cost_since_last_update
        total_cost = calculate_total_cost(total_power_consumption / 1000)  # Umrechnung in kWh
        last_update_time = current_time

        history.append(power)
        power_readings.append(power)
        if len(history) > 15:
            history.pop(0)
        if len(power_readings) > 60:
            power_readings.pop(0)

        avg_power = mean(power_readings)

        output = ""
        for line in big_digits(f"{total_cost:.2f}€"):
            output += Fore.GREEN + Style.BRIGHT + line + "\n"
        cost_per_hour = calculate_cost(power, 3600)
        output += f"\n{Fore.LIGHTBLACK_EX + Style.DIM}Laufzeit: {format_duration(current_time - start_time)}\n"
        output += f"Aktueller Stromverbrauch: {power:.2f} Watt\n"
        output += f"{Fore.YELLOW + Style.NORMAL}Verwendeter Preis: {current_price:.5f} EUR/kWh {Fore.YELLOW + Style.DIM}\n(Quelle: {price_provider})\n\n"

        chart = draw_power_chart(history)
        output += f"{Style.RESET_ALL}"

        sys.stdout.write("\033[H\033[J")  # Terminal-Bildschirm löschen
        sys.stdout.write(output)
        sys.stdout.flush()

        if int(current_time - start_time) % 300 == 0:
            log_data(format_duration(current_time - start_time), total_power_consumption, peak_power)
    else:
        sys.stdout.write(f"{Fore.YELLOW}Stromverbrauch konnte nicht abgerufen werden.{Style.RESET_ALL}\n")
        sys.stdout.flush()

# Hauptfunktion des Skripts
def main():
    global current_price
    get_current_price()
    set_window_title(" Stromverbrauch")
    play_start_sound()
    try:
        os.system('cls' if os.name == 'nt' else 'clear')
        while True:
            print_power()
            time.sleep(1)
    except KeyboardInterrupt:
        print(f"{Style.RESET_ALL}\nProgramm beendet.")
        log_data(format_duration(time.time() - start_time), total_power_consumption, peak_power)
    finally:
        pynvml.nvmlShutdown()

if __name__ == "__main__":
    main()