#####################################################################################################
# S T R O M V E R B R A U C H U N D K O S T E N #
# #
# Das Programm überwacht in Echtzeit den Stromverbrauch von CPU und GPU, #
# berechnet die Kosten basierend auf dem aktuellen Strompreis und stellt diese Daten #
# in einer übersichtlichen grafischen Darstellung dar. #
# Korrekturen: #
# jn 14.12.2024 #
# Die Gesamtkosten werden jetzt korrekt für die Zeit seit der letzten Aktualisierung berechnet. #
# Die Ausgabe der Gesamtkosten sollte realistische Werte anzeigen. #
# Das Problem ist, dass dies die gesamte Zeit seit dem Start verwendet wurde, was dazu führt, #
# dass die Kosten immer weiter anstiegen, obwohl nur die Differenz zur letzten #
# Messung relevant ist. #
# #
# Jetzt mit Fenstertitel 14.12.2024 08:41 #
# #
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
import msvcrt # Hinzugefügt: Import des msvcrt-Moduls für Windows-Tastatureingaben
from big_digits import * # Alle Klassen aus big_digits.py importieren. from mein_modul import meine_funktion, MeineKlasse

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
last_avg_update_time = time.time() # Zeitpunkt der letzten Durchschnittsaktualisierung
avg_power = 0 # Initialisierung des Durchschnitts

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
# Die Funktion wurde in die Datei big_digits.py ausgelagert.

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
    global last_log_time, power_readings, last_avg_update_time, avg_power
    current_time = time.time()
    elapsed_time = current_time - last_update_time
    power = get_system_power()
    history.append(power)
    power_readings.append(power)
    if len(history) > 15:
        history.pop(0)

    # Aktualisiere den Durchschnitt nur alle 5 Minuten
    if current_time - last_avg_update_time >= 300: # 300 Sekunden = 5 Minuten
        avg_power = mean(power_readings) # Berechne den neuen Durchschnitt
        power_readings.clear() # Leere die Liste für die nächsten 5 Minuten
        last_avg_update_time = current_time # Aktualisiere den Zeitpunkt der letzten Durchschnittsaktualisierung

    if power:
        peak_power = max(peak_power, power)
        energy_consumed = (power / 1000) * (elapsed_time / 3600)
        total_power_consumption += energy_consumed * 1000
        cost_since_last_update = calculate_cost(power, elapsed_time)
        total_cost_since_start += cost_since_last_update

        # Prüfen, ob 15 Minuten seit der letzten Protokollierung vergangen sind
        if current_time - last_log_time >= 900: # 900 Sekunden = 15 Minuten
            # Logge die Gesamtkosten der aktuellen Sitzung sowie weitere relevante Werte
            logging.info(f"Gesamtkosten der Sitzung: {total_cost_since_start:.3f} Euro | "
                         f"Aktueller Verbrauch: {power:.2f} Watt | "
                         f"Laufzeit: {format_duration(current_time - start_time)} | "
                         f"Aktueller Strompreis: {current_price:.3f} €/kWh")
            last_log_time = current_time # Aktualisiere den Zeitpunkt der letzten Protokollierung

        # Einrücken der big_digits-Ausgabe um 4 Leerzeichen
        big_digits_output = big_digits(f"{total_cost_since_start:.3f}€")
        output = "" + "".join(Fore.GREEN + line + "\n" for line in big_digits_output)
        output += f"\n    {Fore.YELLOW}Zeit: {format_duration(current_time - start_time)}"
        output += f"\n    {Fore.YELLOW}Watt: {power:.2f} ø {avg_power:.2f}\n"
        output += f"    {Fore.YELLOW + Style.NORMAL}Preis: {current_price:.3f} EUR/kWh {Fore.LIGHTBLACK_EX + Style.DIM}\n    Quelle:{price_provider}\n\n"

        peak_and_unit = f"{math.ceil(peak_power):.0f}w"
        peak_output = "" + f"{Fore.RED + Style.DIM}    Spitzenwert\n"
        peak_output += f"{Style.RESET_ALL}"
        peak_output += "" + "".join(Fore.RED + line + "\n" for line in big_digits(peak_and_unit))

        # Bildschirm löschen und Ausgabe schreiben
        sys.stdout.write("\033[H\033[J") # Cursor an den Anfang des Bildschirms setzen und Bildschirm löschen
        sys.stdout.write(output)
        sys.stdout.write(peak_output)
        sys.stdout.flush()

        last_update_time = current_time
    else:
        print("    Daten konnten nicht abgerufen werden.")

# Funktion, um den Bildschirm zu löschen
def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

# Hauptfunktion
def main():
    sys.stdout.write("\033[H\033[J")
    print('\033[?25l', end="") # Den Cursor ausblenden.
    get_current_price()
    set_window_title("S t r o m v e r b r a u c h")
    play_start_sound()

    # Erster Willkommensbildschirm: Logo
    print(Fore.CYAN + r"""
    _______________________________________
            ________________
           | __ \__ __| ____|
           | | | | | | | |__
           | | | | | | | __|
           | |__| || | | |
           |_____/ |_| |_|
           _ ___         ________  
          (_)__ \ __  __/ ____/ /_ 
         / /__/ // / / /___ \/ __ \
        / // __// /_/ /___/ / / / /
       /_//____/\____/_____/_/ /_/ 
    _______________________________________
    """)

    # Pause von 5 Sekunden oder Weiter mit Leertaste
    # print(Fore.RESET + "\n    Drücken Sie die Leertaste, um sofort fortzufahren.")
    start_time = time.time()
    remaining_time = 2 # Startwert für den Countdown

    while remaining_time > 0:
        if msvcrt.kbhit(): # Überprüfen, ob eine Taste gedrückt wurde
            key = msvcrt.getch().decode('utf-8') # Gedrückte Taste lesen
            if key == ' ': # Leertaste gedrückt
                break

        # Countdown anzeigen
        # sys.stdout.write(Fore.RED + f"\r                                          {remaining_time}")
        sys.stdout.flush()

        # Warte 1 Sekunde
        time.sleep(1)
        remaining_time -= 1

    print("\n") # Neue Zeile nach dem Countdown

    # Zweiter Willkommensbildschirm: Logfile-Info
    clear_screen()
    print("\n")
    print(Fore.RED + r"       Stromverbrauch und Kosten Monitor")
    print(Fore.RED + r"""    _______________________________________""")
    print(Fore.YELLOW + "\n    Wichtiger Hinweis:")
    print(Fore.YELLOW + f"    Es wird ein Logfile wird gespeichert.")
    # print(Fore.YELLOW + f"    \033]8;;file://{log_file}\033\\{log_file}\033]8;;\033\\")
    print(Fore.YELLOW + f"    \033]8;;file://{log_file}\033\\               L I N K               \033]8;;\033\\")
    print(Fore.YELLOW + "    (Strg + Klick, um den Pfad zu öffnen)\n")

    # Pause von 5 Sekunden oder Weiter mit Leertaste
    print(Fore.RESET + "              Leertaste, um fortzufahren.")
    start_time = time.time()
    remaining_time = 9 # Startwert für den Countdown

    while remaining_time > 0:
        if msvcrt.kbhit(): # Überprüfen, ob eine Taste gedrückt wurde
            key = msvcrt.getch().decode('utf-8') # Gedrückte Taste lesen
            if key == ' ': # Leertaste gedrückt
                break

        # Countdown anzeigen
        sys.stdout.write(f"\r                              {remaining_time} Sekunden")
        sys.stdout.flush()

        # Warte 1 Sekunde
        time.sleep(1)
        remaining_time -= 1

    print("\n") # Neue Zeile nach dem Countdown

    try:
        while True:
            print_power()
            time.sleep(1)
    except KeyboardInterrupt:
        print('\033[?25h', end="") # Den Cursor wieder anzeigen.
        print("    Programm beendet.")
    finally:
        pynvml.nvmlShutdown()

if __name__ == "__main__":
    main()