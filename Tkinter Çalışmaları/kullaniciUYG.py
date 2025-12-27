import tkinter as tk

def hosgeldin():
    isim = adi.get()
    if isim.strip() == "":
        mesaj.config(text="Lütfen isminizi girin!", fg="red")
    else:
        mesaj.config(text=f"Hoş geldin! {isim}", fg="green")

ekran = tk.Tk()
ekran.title("Kullanıcıdan isim alma")
ekran.geometry("500x200")

etiket = tk.Label(ekran, text="Adınızı giriniz:", font=("Arial", 10))
etiket.pack()

adi = tk.Entry(ekran, font=("Arial", 10))
adi.pack(padx=50, pady=50)

buton = tk.Button(ekran, text="Kaydet", command=hosgeldin)
buton.pack(pady=10)

mesaj = tk.Label(ekran, text="", font=("Arial", 12))
mesaj.pack()

ekran.mainloop()







