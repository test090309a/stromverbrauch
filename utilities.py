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
def big_digits(number):
    # Beispielhafte Implementierung, die eine große Darstellung einer Zahl zurückgibt
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
    return [str(number)]

def format_duration(seconds):
    # Formatiert eine Zeitdauer in Stunden, Minuten und Sekunden
    # hours = seconds // 3600
    # minutes = (seconds % 3600) // 60
    # seconds = seconds % 60
    # return f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"
    return str(timedelta(seconds=int(seconds)))

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

def calculate_cost(power, duration_seconds):
    # Berechnet die Kosten basierend auf dem Stromverbrauch und der verstrichenen Zeit
    # price_per_kwh = 0.30  # Beispielhafter Preis pro kWh
    # energy_consumed = (power / 1000) * (elapsed_time / 3600)  # Energie in kWh
    # return energy_consumed * price_per_kwh
    energy_consumed = (power / 1000) * (duration_seconds / 3600)
    return energy_consumed * current_price if current_price else 0

def get_system_power():
    # Beispielhafte Implementierung, die den aktuellen Stromverbrauch des Systems zurückgibt
    # return 100  # Beispielwert in Watt
    # energy_consumed = (power / 1000) * (duration_seconds / 3600)
    # return energy_consumed * current_price if current_price else 0
    # Initialisierung
    init()
    pynvml.nvmlInit()
    
    try:
        handle = pynvml.nvmlDeviceGetHandleByIndex(0)
        gpu_power = pynvml.nvmlDeviceGetPowerUsage(handle) / 1000
        cpu_usage = psutil.cpu_percent()
        cpu_power = (cpu_usage / 100) * 65
        return cpu_power + gpu_power
    except Exception as e:
        logging.warning(f"Fehler beim Abrufen des Stromverbrauchs: {e}")
        return 0    

def get_current_price():
    # Beispielhafte Implementierung, die den aktuellen Strompreis zurückgibt
    return 0.30  # Beispielwert in Euro pro kWh

price_provider = "Beispielanbieter"