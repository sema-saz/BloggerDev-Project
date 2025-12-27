import tkinter as tk
import pyodbc

# MSSQL bağlantı ayarları
server = 'SORA\\SQLEXPRESS'
database = 'TEST'
connection = pyodbc.connect(
    f'DRIVER={{ODBC Driver 17 for SQL Server}};'
    f'SERVER={server};'
    f'DATABASE={database};'
    f'Trusted_Connection=yes;'
)

# Fonksiyon: Kaydet butonuna basılınca çalışacak
def kaydet():
    firstname = entry_firstname.get()
    lastname = entry_lastname.get()
    email = entry_email.get()

    cursor = connection.cursor()
    cursor.execute(
        "INSERT INTO Customers (FirstName, LastName, Email) VALUES (?, ?, ?)",
        (firstname, lastname, email)
    )
    connection.commit()
    label_message.config(text="Müşteri başarıyla kaydedildi! 🎉")

# Tkinter penceresi
pencere = tk.Tk()
pencere.title("Müşteri Ekleme Formu")
pencere.geometry("400x300")

# İsim
label_firstname = tk.Label(pencere, text="İsim:")
label_firstname.pack()
entry_firstname = tk.Entry(pencere)
entry_firstname.pack()

# Soyisim
label_lastname = tk.Label(pencere, text="Soyisim:")
label_lastname.pack()
entry_lastname = tk.Entry(pencere)
entry_lastname.pack()

# Email
label_email = tk.Label(pencere, text="E-posta:")
label_email.pack()
entry_email = tk.Entry(pencere)
entry_email.pack()

# Kaydet Butonu
button_save = tk.Button(pencere, text="Kaydet", command=kaydet)
button_save.pack(pady=10)

# Mesaj Alanı
label_message = tk.Label(pencere, text="")
label_message.pack()

pencere.mainloop()
