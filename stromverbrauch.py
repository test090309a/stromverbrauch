# STROMVERBRAUCH MONITOR
# Zeigt den aktuellen Stromverbrauch und die Kosten in Echtzeit an.
# Version 1.3 vom 12.09.2025
# J.N. aka DFT aka i2u5h
# Ich will den Strompreis im Auge behalten.

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
import msvcrt  # Nur für Windows-Tastatureingaben
from big_digits import big_digits

# Initialisierung
init()
pynvml.nvmlInit()
log_file = os.path.join(tempfile.gettempdir(), "stromverbrauch.log")
logging.basicConfig(filename=log_file, level=logging.INFO,
                   format="%(asctime)s %(levelname)s: %(message)s")

# Globale Variablen
current_price = 0.33  # Default
price_provider = "Unbekannt"
total_power_consumption = 0.0  # in Wh
total_cost = 0.0
peak_power = 0.0
start_time = time.time()
last_update_time = start_time
last_log_time = start_time
GRUNDGEBUEHR = 3.50  # Euro/Monat

def play_start_sound():
    try:
        import winsound
        winsound.Beep(1000, 200)
        winsound.Beep(1500, 200)
        winsound.Beep(2000, 300)
    except ImportError:
        print("Startton nicht verfügbar.")

def set_window_title(title: str):
    if os.name == "nt":
        try:
            ctypes.windll.kernel32.SetConsoleTitleW(title)
        except Exception:
            pass

def get_current_price():
    global current_price, price_provider
    try:
        response = requests.get("https://apis.smartenergy.at/market/v1/price", timeout=5)
        response.raise_for_status()
        data = response.json()
        now = datetime.now()
        current_price_data = next(
            (item for item in data["data"]
             if datetime.fromisoformat(item["date"]).replace(tzinfo=None) <= now <
                datetime.fromisoformat(item["date"]).replace(tzinfo=None) + timedelta(minutes=15)),
            None
        )
        if current_price_data:
            current_price = (current_price_data["value"] + 1.44) / 100
            price_provider = "smartENERGY"
        else:
            raise ValueError("Kein gültiger Preis gefunden.")
    except Exception as e:
        logging.warning(f"Preis nicht abrufbar, Fallback: {e}")
        current_price = 0.33
        price_provider = "EPEX"
    return current_price

def update_price_periodically():
    while True:
        get_current_price()
        time.sleep(900)

threading.Thread(target=update_price_periodically, daemon=True).start()

def get_system_power():
    try:
        handle = pynvml.nvmlDeviceGetHandleByIndex(0)
        gpu_power = pynvml.nvmlDeviceGetPowerUsage(handle) / 1000
        cpu_usage = psutil.cpu_percent()
        cpu_power = (cpu_usage / 100) * 65
        return cpu_power + gpu_power
    except Exception as e:
        logging.warning(f"Systempower Fehler: {e}")
        return 0.0

def calculate_cost(power_watt, duration_seconds):
    energy_consumed = (power_watt / 1000) * (duration_seconds / 3600)
    return energy_consumed * current_price

def format_duration(seconds):
    return str(timedelta(seconds=int(seconds)))

def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def print_power():
    global peak_power, total_power_consumption, last_update_time, total_cost
    global last_log_time

    current_time = time.time()
    elapsed_time = current_time - last_update_time
    power = get_system_power()

    if power > 0:
        peak_power = max(peak_power, power)
        energy_consumed_wh = (power / 1000) * (elapsed_time / 3600) * 1000
        total_power_consumption += energy_consumed_wh
        total_cost += calculate_cost(power, elapsed_time)

        months = max(1, int((current_time - start_time) / (30 * 24 * 3600)))
        total_cost_with_base = total_cost + (GRUNDGEBUEHR * months)

        if current_time - last_log_time >= 900:
            logging.info(f"Kosten: {total_cost_with_base:.3f} Euro | Verbrauch: {power:.2f} W | Dauer: {format_duration(current_time - start_time)} | Preis: {current_price:.3f} €/kWh")
            last_log_time = current_time

        sys.stdout.write("\033[H\033[J")  # clear screen

        # PREIS oben, dann dunkelgrüne Zahl
        print(Style.NORMAL + Fore.GREEN + "    Aktueller Preis in €/kWh")
        price_str = f"{current_price:.2f}"  # Zwei Nachkommastellen.
        price_digits = ''.join([c for c in price_str if c.isdigit() or c == '.'])
        for line in big_digits(price_digits):
            print(Style.NORMAL + Fore.GREEN + line)
        # print(Style.NORMAL + Fore.GREEN + " EUR/kWh\n")
        # Peak als große Zahl
        peak_number = f"{math.ceil(peak_power):.0f}"
        print(Fore.RED + "    Spitzenwert in Watt: ")
        for line in big_digits(peak_number):
            print(Fore.RED + line)
        # print(Fore.RED + " W")
        
        
        # Quelle GANZ unten
        print("" + Style.DIM + Fore.LIGHTBLACK_EX + f"    {price_provider}, DTF 2025")

        last_update_time = current_time
    else:
        print("    Keine Daten verfügbar.")

def main():
    sys.stdout.write("\033[H\033[J")
    print("\033[?25l", end="")  # Cursor ausblenden
    get_current_price()
    set_window_title("Stromverbrauch Monitor")
    play_start_sound()

    clear_screen()
    print(Fore.CYAN + "Stromverbrauch und Kosten Monitor gestartet!")
    print(Fore.YELLOW + f"Logfile gespeichert unter: {log_file}")

    try:
        while True:
            print_power()
            time.sleep(1)
    except KeyboardInterrupt:
        print("\033[?25h", end="")  # Cursor wieder anzeigen
        print("\nProgramm beendet.")
    finally:
        pynvml.nvmlShutdown()

if __name__ == "__main__":
    main()
