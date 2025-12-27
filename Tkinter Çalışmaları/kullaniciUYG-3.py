import tkinter as tk
from tkinter import messagebox
import pyodbc

# Bağlantı oluştur
def connect_db():
    return pyodbc.connect(
        'DRIVER={ODBC Driver 17 for SQL Server};'
        'SERVER=SORA\\SQLEXPRESS;'
        'DATABASE=PROJE;'
        'Trusted_Connection=yes;'
    )

# kisiler tablosunun var olup olmadığını kontrol et ve yoksa oluştur
def tablo_olustur():
    conn = connect_db()
    cursor = conn.cursor()
    
    cursor.execute(''' 
    IF NOT EXISTS (SELECT * FROM sysobjects WHERE name = 'kisiler' AND xtype = 'U')
    BEGIN
        CREATE TABLE kisiler (
            id INT PRIMARY KEY IDENTITY(1,1),
            ad VARCHAR(100),
            soyad VARCHAR(100),
            telefon VARCHAR(15),
            email VARCHAR(100),
            adres VARCHAR(255)
        )
    END
    ''')
    conn.commit()
    conn.close()

# Kullanıcıyı eklemek için fonksiyon
def veri_ekle():
    ad = ad_entry.get()
    soyad = soyad_entry.get()
    telefon = telefon_entry.get()
    email = email_entry.get()

    # Veri kontrolü (Basit doğrulama)
    if ad.strip() == "" or soyad.strip() == "" or telefon.strip() == "" or email.strip() == "":
        messagebox.showerror("Hata", "Lütfen tüm alanları doldurun!")
        return

    conn = connect_db()
    cursor = conn.cursor()

    # Veritabanına veri ekleme
    cursor.execute(''' 
    INSERT INTO kisiler (ad, soyad, telefon, email) 
    VALUES (?, ?, ?, ?) 
    ''', (ad, soyad, telefon, email))

    conn.commit()
    conn.close()

    # Başarı mesajı
    messagebox.showinfo("Başarı", "Kişi başarıyla eklendi!")

    # Giriş kutularını temizle
    ad_entry.delete(0, tk.END)
    soyad_entry.delete(0, tk.END)
    telefon_entry.delete(0, tk.END)
    email_entry.delete(0, tk.END)

# Tkinter penceresini oluştur
root = tk.Tk()
root.title("Kişi Ekleme Formu")
root.geometry("300x400")

# Etiketler
etiket_ad = tk.Label(root, text="Ad:")
etiket_ad.pack()
ad_entry = tk.Entry(root)
ad_entry.pack()

etiket_soyad = tk.Label(root, text="Soyad:")
etiket_soyad.pack()
soyad_entry = tk.Entry(root)
soyad_entry.pack()

etiket_telefon = tk.Label(root, text="Telefon:")
etiket_telefon.pack()
telefon_entry = tk.Entry(root)
telefon_entry.pack()

etiket_email = tk.Label(root, text="E-posta:")
etiket_email.pack()
email_entry = tk.Entry(root)
email_entry.pack()

# Ekleme butonu
ekle_buton = tk.Button(root, text="Kişi Ekle", command=veri_ekle)
ekle_buton.pack(pady=10)

# Tabloyu kontrol et ve oluştur
tablo_olustur()

# Pencereyi çalıştır
root.mainloop()
