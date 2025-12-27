import tkinter as tk
#ANA PENCEREYİ OLUŞTURMA
pencere=tk.Tk()
pencere.title("İlk Tkinter deneyimim!")
pencere.geometry("300x150") #genişlik x yükseklik

#ETİKET(LABEL)
etiket=tk.Label(pencere, text="Merhaba dostlar bu bir Tkinter GUI penceresidir.", font=("Arial", 10))
etiket.pack(pady=10, padx=10)
def butona_tiklandi():
    etiket.config(text="Butona bastın!")
#BUTON
buton=tk.Button(pencere, text="BASMA", command=butona_tiklandi)
buton.pack(pady=10)

#PENCEREYİ ÇALIŞTIRMA   
pencere.mainloop()