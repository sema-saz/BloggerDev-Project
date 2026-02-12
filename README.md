# BloggerDev - Web & Admin Management System

Bu proje, bir Python Flask web uygulaması ve buna bağlı bir Tkinter admin panelinden oluşan tam kapsamlı bir blog yönetim sistemidir.

## 🛠️ Teknik Altyapı
* **Web Framework:** Flask
* **Veritabanı:** MS SQL Server (yerel sunucuda pyodbc bağlantısı ile)
* **Admin Paneli:** Tkinter (Masaüstü uygulaması)
* **Kütüphaneler:** Tüm bağımlılıklar `requirements.txt` dosyasında listelenmiştir.

## 📁 Proje Yapısı
* `app.py`: Ana web sunucusu dosyası.
* `templates/`: HTML arayüz dosyaları.
* `static/`: CSS ve statik dosyalar.
* `BloggerDev-AdminPaneli/`: Admin yönetim paneli kodları.
* `requirements.txt`: Gerekli kütüphaneler listesi.

## 🚀 Kurulum
1. Gerekli paketleri yükleyin:
   ```bash
   pip install -r requirements.txt
2. SQL Server bağlantı bilgisini app.py içinde düzenleyin.
3. Sunucuyu başlatın:
python app.py
