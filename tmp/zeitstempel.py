import pywintypes
import win32file
import win32con
from datetime import datetime
import os
import sys
import ctypes
from tkinter import Tk, Button, Label, messagebox, filedialog, Entry, Frame
from tkcalendar import Calendar  # Für die Kalenderanzeige

def is_admin():
    """
    Überprüft, ob das Skript als Administrator ausgeführt wird.
    
    :return: True, wenn Administratorrechte vorhanden sind, sonst False
    """
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin():
    """
    Startet das Skript neu mit Administratorrechten.
    """
    if not is_admin():
        print("Das Skript wird neu gestartet, um Administratorrechte anzufordern...")
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        sys.exit()

def change_creation_time(file_path, new_time):
    """
    Ändert das Erstellungsdatum einer Datei.
    
    :param file_path: Pfad zur Datei
    :param new_time: Neues Erstellungsdatum als datetime-Objekt
    """
    try:
        # Überprüfe, ob die Datei existiert
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Die Datei '{file_path}' existiert nicht.")

        # Öffne die Datei
        handle = win32file.CreateFile(
            file_path,
            win32con.GENERIC_WRITE,
            win32con.FILE_SHARE_READ | win32con.FILE_SHARE_WRITE,
            None,
            win32con.OPEN_EXISTING,
            win32con.FILE_ATTRIBUTE_NORMAL,
            None
        )

        if handle == win32file.INVALID_HANDLE_VALUE:
            raise Exception("Datei konnte nicht geöffnet werden.")

        # Konvertiere die neue Zeit in eine Windows-FILETIME-Struktur
        new_time = pywintypes.Time(new_time)

        # Setze das neue Erstellungsdatum
        win32file.SetFileTime(handle, new_time, None, None)

        # Schließe die Datei
        win32file.CloseHandle(handle)

        messagebox.showinfo("Erfolg", f"Das Erstellungsdatum von '{file_path}' wurde erfolgreich geändert.")
    except Exception as e:
        messagebox.showerror("Fehler", f"Fehler beim Ändern des Erstellungsdatums: {e}")

def get_creation_time(file_path):
    """
    Gibt das Erstellungsdatum einer Datei zurück.
    
    :param file_path: Pfad zur Datei
    :return: Erstellungsdatum als datetime-Objekt
    """
    try:
        creation_time = os.path.getctime(file_path)
        return datetime.fromtimestamp(creation_time)
    except Exception as e:
        messagebox.showerror("Fehler", f"Fehler beim Abrufen des Erstellungsdatums: {e}")
        return None

def select_file():
    """
    Öffnet ein Dateiauswahlmenü und gibt den ausgewählten Dateipfad zurück.
    
    :return: Ausgewählter Dateipfad oder None, wenn keine Datei ausgewählt wurde
    """
    file_path = filedialog.askopenfilename(title="Wählen Sie eine Datei aus")
    return file_path

def select_date_time():
    """
    Öffnet ein Fenster zur Auswahl des Datums und der Uhrzeit.
    
    :return: Ausgewähltes Datum und Uhrzeit als datetime-Objekt oder None, wenn abgebrochen wurde
    """
    def on_submit():
        selected_date = cal.get_date()
        selected_time = time_entry.get()
        try:
            # Überprüfe, ob die Uhrzeit im Format HH:MM ist
            datetime.strptime(selected_time, "%H:%M")
            result = datetime.strptime(f"{selected_date} {selected_time}", "%Y-%m-%d %H:%M")
            date_time_window.destroy()
            nonlocal final_result
            final_result = result
        except ValueError:
            messagebox.showerror("Fehler", "Ungültiges Zeitformat. Bitte verwenden Sie 'HH:MM'.")

    date_time_window = Tk()
    date_time_window.title("Datum und Uhrzeit auswählen")
    date_time_window.geometry("400x300")  # Größeres Fenster

    # Kalender für Datumsauswahl
    cal = Calendar(date_time_window, selectmode="day", year=datetime.now().year, month=datetime.now().month, day=datetime.now().day)
    cal.pack(pady=10)

    # Uhrzeiteingabe
    time_frame = Frame(date_time_window)
    time_frame.pack(pady=10)

    Label(time_frame, text="Uhrzeit (HH:MM):").pack(side="left")
    time_entry = Entry(time_frame)
    time_entry.pack(side="left", padx=10)
    time_entry.insert(0, "00:00")  # Standardzeit

    # Bestätigungsbutton
    Button(date_time_window, text="Auswählen", command=on_submit).pack(pady=10)

    final_result = None
    date_time_window.mainloop()
    return final_result

def main_gui():
    """
    Haupt-GUI für das Skript.
    """
    def on_file_select():
        file_path = select_file()
        if file_path:
            file_label.config(text=file_path)

    def on_date_time_select():
        selected_date_time = select_date_time()
        if selected_date_time:
            date_time_label.config(text=selected_date_time.strftime("%Y-%m-%d %H:%M"))

    def on_submit():
        file_path = file_label.cget("text")
        selected_date_time = date_time_label.cget("text")

        if not file_path or file_path == "Keine Datei ausgewählt":
            messagebox.showwarning("Warnung", "Bitte wählen Sie eine Datei aus.")
            return

        if not selected_date_time or selected_date_time == "Kein Datum und keine Uhrzeit ausgewählt":
            messagebox.showwarning("Warnung", "Bitte wählen Sie ein Datum und eine Uhrzeit aus.")
            return

        # Konvertiere das ausgewählte Datum und die Uhrzeit in ein datetime-Objekt
        try:
            new_time = datetime.strptime(selected_date_time, "%Y-%m-%d %H:%M")
            # Ändere das Erstellungsdatum
            change_creation_time(file_path, new_time)
        except ValueError:
            messagebox.showerror("Fehler", "Ungültiges Datums- oder Zeitformat.")

    # Hauptfenster erstellen
    root = Tk()
    root.title("Erstellungsdatum ändern")
    root.geometry("500x300")  # Größeres Fenster

    # Dateiauswahl
    file_label = Label(root, text="Keine Datei ausgewählt", fg="blue")
    file_label.pack(pady=10)

    Button(root, text="Datei auswählen", command=on_file_select).pack(pady=10)

    # Datums- und Uhrzeiteingabe
    date_time_label = Label(root, text="Kein Datum und keine Uhrzeit ausgewählt", fg="blue")
    date_time_label.pack(pady=10)

    Button(root, text="Datum und Uhrzeit auswählen", command=on_date_time_select).pack(pady=10)

    # Bestätigungsbutton
    Button(root, text="Erstellungsdatum ändern", command=on_submit).pack(pady=20)

    # Starte die GUI
    root.mainloop()

def main():
    print("Willkommen zum Tool zum Ändern des Erstellungsdatums einer Datei.")

    # Überprüfe, ob das Skript als Administrator ausgeführt wird
    run_as_admin()

    # Starte die GUI
    main_gui()

if __name__ == "__main__":
    main()