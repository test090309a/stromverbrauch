#include <iostream>
#include <iomanip>
#include <chrono>
#include <thread>
#include <cmath>
#include <ctime>

using namespace std;
using namespace std::chrono;

// Simulierte Werte (ersetze durch echte Messwerte, falls verfügbar)
double get_system_power() {
    // Beispiel: zufälliger Verbrauch zwischen 20 und 80 Watt
    return 20.0 + (rand() % 60);
}

// Hilfsfunktion für Zeitformatierung
string format_duration(int seconds) {
    int h = seconds / 3600;
    int m = (seconds % 3600) / 60;
    int s = seconds % 60;
    char buf[16];
    snprintf(buf, sizeof(buf), "%02d:%02d:%02d", h, m, s);
    return string(buf);
}

// Kostenberechnung nach Vorgabe
double calculate_total_cost(double total_consumption_kwh, double price_per_kwh, double grundgebuehr, int months) {
    return (total_consumption_kwh * price_per_kwh) + (grundgebuehr * months);
}

int main() {
    // Parameter
    const double GRUNDGEBUEHR = 3.50; // Euro pro Monat
    double price_per_kwh = 0.33;      // Beispielpreis, kann dynamisch gesetzt werden
    double total_power_consumption = 0.0; // in Wh
    double peak_power = 0.0;
    auto start_time = steady_clock::now();

    cout << "Stromverbrauch und Kosten Monitor (C++)\n";
    cout << "----------------------------------------\n";
    cout << "Druecken Sie Strg+C zum Beenden.\n\n";

    while (true) {
        double power = get_system_power(); // in Watt
        peak_power = max(peak_power, power);

        // Zeit seit Start
        auto now = steady_clock::now();
        int elapsed_seconds = duration_cast<seconds>(now - start_time).count();

        // Verbrauch seit letzter Sekunde (Wh)
        total_power_consumption += power / 3600.0;

        // Verbrauch in kWh
        double total_consumption_kwh = total_power_consumption / 1000.0;

        // Monate seit Start (mindestens 1)
        int months = max(1, elapsed_seconds / (30 * 24 * 3600));

        // Gesamtkosten inkl. Grundgebühr
        double total_cost = calculate_total_cost(total_consumption_kwh, price_per_kwh, GRUNDGEBUEHR, months);

        // Anzeige
        system("cls"); // Bildschirm löschen (Windows)
        cout << fixed << setprecision(3);
        cout << "Gesamtkosten: " << total_cost << " Euro\n";
        cout << "Gesamtverbrauch: " << total_consumption_kwh << " kWh\n";
        cout << "Aktueller Verbrauch: " << power << " Watt\n";
        cout << "Spitzenwert: " << peak_power << " Watt\n";
        cout << "Preis pro kWh: " << price_per_kwh << " Euro\n";
        cout << "Grundgebuehr: " << GRUNDGEBUEHR << " Euro/Monat\n";
        cout << "Monate: " << months << "\n";
        cout << "Laufzeit: " << format_duration(elapsed_seconds) << "\n";

        this_thread::sleep_for(seconds(1));
    }

    return 0;
}