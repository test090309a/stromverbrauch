import time
import logging
import sys
import math
from statistics import mean
from colorama import Fore, Style
from utilities import big_digits, format_duration, calculate_cost, get_system_power, get_current_price, price_provider

# Initialisierung der Variablen
power_readings = []
total_power_consumption = 0
total_cost_since_start = 0
peak_power = 0
last_log_time = time.time()
last_update_time = time.time()
start_time = time.time()

while True:
    current_time = time.time()
    elapsed_time = current_time - last_update_time

    power = get_system_power()
    current_price = get_current_price()

    if power is not None:
        power_readings.append(power)
        if len(power_readings) > 10:
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
            output += f"\n{Fore.YELLOW}Laufzeit: {format_duration(current_time - start_time)}"
            # output += f"\n{Fore.YELLOW}Aktueller Verbrauch: {power:.2f} W\n"
            average_symbol = "x̄"
            output += f"\n{Fore.YELLOW}Jetzt: {power:.2f} W |  {avg_power:.2f} {average_symbol}\n"

            output += f"{Fore.YELLOW + Style.NORMAL}Verwendeter Preis: {current_price:.5f} EUR/kWh {Fore.YELLOW + Style.DIM}\n(Quelle: {price_provider})\n\n"

            peak_and_unit = f"{math.ceil(peak_power):.0f}w"
            peak_output = f"{Fore.RED + Style.DIM}Spitzenwert\n"
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

    time.sleep(1)