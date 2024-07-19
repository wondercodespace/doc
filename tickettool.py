import os
import sys
import subprocess
import random
import string
import bcrypt

# Prüfen und Installieren der notwendigen Pakete (Dies ist nicht zverlässig! Bitte zuvor manuell in der CMD Konsole instalieren -> pip install [bib name])
def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

try:
    from PIL import Image, ImageDraw, ImageFont
    import csv
    import tkinter as tk
    from tkinter import messagebox, filedialog, simpledialog
except ImportError as e:
    missing_package = str(e).split()[-1]
    install(missing_package)
    from PIL import Image, ImageDraw, ImageFont
    import csv
    import tkinter as tk
    from tkinter import messagebox, filedialog, simpledialog

# Sicherheitskonzept
def verify_password(password, hashed):
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def verify_access():
    username = simpledialog.askstring("Benutzername", "Geben Sie Ihren Benutzernamen ein:")
    password = simpledialog.askstring("Passwort", "Geben Sie Ihr Passwort ein:", show='*')

    with open('users.csv', mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row['Benutzername'] == username and verify_password(password, row['Passwort']):
                if row['Berechtigung'] == 'admin':
                    return True
                else:
                    messagebox.showerror("Fehler", "Keine Administratorrechte.")
                    return False
        messagebox.showerror("Fehler", "Ungültiger Benutzername oder Passwort.")
        return False

def create_admin_account():
    username = "admin"
    password = simpledialog.askstring("Admin Passwort", "Geben Sie das Administrator-Passwort ein:", show='*')
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    with open('users.csv', mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Benutzername", "Passwort", "Berechtigung"])
        writer.writerow([username, hashed_password, "admin"])

    messagebox.showinfo("Erfolg", "Administrator-Konto erstellt. Bitte starten Sie das Programm neu.")

# Ticket Generator Funktionen
def generate_ticket_number():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

def create_ticket(ticket_number, details, logo_path, personalized, buyer_info=None):
    # Eventim-inspiriertes Ticket-Layout
    ticket_img = Image.new('RGB', (600, 300), color=(255, 255, 255))
    d = ImageDraw.Draw(ticket_img)
    font = ImageFont.truetype("arial.ttf", 16)

    # Hintergrundfarbe und Textfarbe
    bg_color = (255, 102, 0)  # Orange
    text_color = (0, 0, 0)    # Schwarz

    # Zeichne Hintergrund und Details
    d.rectangle([(0, 0), (600, 300)], fill=bg_color, outline=bg_color)
    d.text((30, 20), "Ticket", fill=(255, 255, 255), font=ImageFont.truetype("arial.ttf", 24))
    d.line([(30, 60), (570, 60)], fill=(255, 255, 255), width=2)

    # Ticketnummer und Details
    d.text((50, 100), f"Ticketnummer: {ticket_number}", fill=text_color, font=font)
    d.text((50, 140), f"Name: {details['Name']}", fill=text_color, font=font)
    d.text((50, 160), f"Datum: {details['Datum']}", fill=text_color, font=font)
    d.text((50, 180), f"Ort: {details['Ort']}", fill=text_color, font=font)
    d.text((50, 200), f"Preis: {details['Preis']}", fill=text_color, font=font)
    d.text((50, 220), f"Weitere Informationen: {details['Zusätzliche Informationen']}", fill=text_color, font=font)

    if personalized and buyer_info:
        d.text((50, 240), f"Käufer: {buyer_info['Name']}", fill=text_color, font=font)
        d.text((50, 260), "Bitte bringen Sie einen amtlichen Lichtbildausweis mit.", fill=text_color, font=font)

    # Logo hinzufügen
    if logo_path:
        logo = Image.open(logo_path)
        logo.thumbnail((100, 100))
        ticket_img.paste(logo, (450, 20))

    return ticket_img

def save_ticket(ticket_img, ticket_number):
    ticket_path = f"ticket_{ticket_number}.png"
    ticket_img.save(ticket_path)
    print_ticket(ticket_path)

def print_ticket(ticket_path):
    os.startfile(ticket_path, "print")

def generate_ticket():
    details = {
        "Name": entry_name.get(),
        "Datum": entry_date.get(),
        "Ort": entry_location.get(),
        "Preis": entry_price.get(),
        "Zusätzliche Informationen": entry_info.get()
    }

    ticket_number = generate_ticket_number()
    personalized = messagebox.askyesno("Personalisierung", "Soll das Ticket personalisiert sein?")
    buyer_info = None

    if personalized:
        buyer_info = {
            "Name": simpledialog.askstring("Käufer Name", "Geben Sie den Namen des Käufers ein:")
        }

    ticket_img = create_ticket(ticket_number, details, logo_path, personalized, buyer_info)

    with open('tickets.csv', mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([ticket_number, details['Name'], details['Datum'], details['Ort'], details['Preis'], details['Zusätzliche Informationen'], "valid", personalized, buyer_info['Name'] if buyer_info else ""])

    save_ticket(ticket_img, ticket_number)

def check_and_invalidate_ticket(ticket_number):
    updated_rows = []
    found = False
    with open('tickets.csv', mode='r') as file:
        reader = csv.reader(file)
        for row in reader:
            if row[0] == ticket_number:
                if row[6] == "valid":
                    if row[7] == "True":
                        buyer_name = simpledialog.askstring("Käufer Name", "Geben Sie den Namen des Käufers ein:")
                        if buyer_name != row[8]:
                            row[6] = "closed"
                            messagebox.showerror("Fehler", "Ungültige Käuferinformationen. Ticket gesperrt.")
                        else:
                            row[6] = "invalid"
                            messagebox.showinfo("Erfolg", "Ticket erfolgreich entwertet.")
                    else:
                        row[6] = "invalid"
                        messagebox.showinfo("Erfolg", "Ticket erfolgreich entwertet.")
                else:
                    messagebox.showerror("Fehler", "Ticket ist bereits entwertet oder gesperrt.")
                found = True
            updated_rows.append(row)

    if not found:
        messagebox.showerror("Fehler", f"Ticket {ticket_number} nicht gefunden.")
    else:
        with open('tickets.csv', mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerows(updated_rows)

def edit_tickets():
    if not verify_access():
        return

    edit_window = tk.Toplevel(root)
    edit_window.title("Tickets bearbeiten")

    with open('tickets.csv', mode='r') as file:
        reader = csv.reader(file)
        rows = list(reader)

    for i, row in enumerate(rows):
        for j, val in enumerate(row):
            entry = tk.Entry(edit_window, width=20)
            entry.grid(row=i, column=j)
            entry.insert(0, val)

    def save_changes():
        updated_rows = []
        for i in range(len(rows)):
            updated_row = [edit_window.grid_slaves(row=i, column=j)[0].get() for j in range(len(rows[0]))]
            updated_rows.append(updated_row)
        with open('tickets.csv', mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerows(updated_rows)
        edit_window.destroy()
        messagebox.showinfo("Erfolg", "Änderungen gespeichert.")

    save_button = tk.Button(edit_window, text="Speichern", command=save_changes)
    save_button.grid(row=len(rows), columnspan=len(rows[0]))

# Hauptfenster erstellen
root = tk.Tk()
root.title("Ticket-System")

# GUI-Elemente erstellen
tk.Label(root, text="Name").grid(row=0, column=0)
entry_name = tk.Entry(root)
entry_name.grid(row=0, column=1)

tk.Label(root, text="Datum").grid(row=1, column=0)
entry_date = tk.Entry(root)
entry_date.grid(row=1, column=1)

tk.Label(root, text="Ort").grid(row=2, column=0)
entry_location = tk.Entry(root)
entry_location.grid(row=2, column=1)

tk.Label(root, text="Preis").grid(row=3, column=0)
entry_price = tk.Entry(root)
entry_price.grid(row=3, column=1)

tk.Label(root, text="Zusätzliche Informationen").grid(row=4, column=0)
entry_info = tk.Entry(root)
entry_info.grid(row=4, column=1)

logo_path = ""
def upload_logo():
    global logo_path
    logo_path = filedialog.askopenfilename()
    if logo_path:
        logo_label.config(text=os.path.basename(logo_path))

tk.Label(root, text="Logo hochladen").grid(row=5, column=0)
logo_button = tk.Button(root, text="Hochladen", command=upload_logo)
logo_button.grid(row=5, column=1)
logo_label = tk.Label(root, text="")
logo_label.grid(row=5, column=2)

generate_button = tk.Button(root, text="Ticket erstellen", command=generate_ticket)
generate_button.grid(row=6, columnspan=2)

check_button = tk.Button(root, text="Ticket prüfen", command=lambda: check_and_invalidate_ticket(simpledialog.askstring("Ticketnummer", "Geben Sie die Ticketnummer ein:")))
check_button.grid(row=7, columnspan=2)

edit_button = tk.Button(root, text="Tickets bearbeiten", command=edit_tickets)
edit_button.grid(row=8, columnspan=2)

# Überprüfen, ob das Admin-Konto existiert
if not os.path.exists('users.csv') or not any(row['Benutzername'] == 'admin' for row in csv.DictReader(open('users.csv'))):
    create_admin_account()
    root.destroy()

root.mainloop()
