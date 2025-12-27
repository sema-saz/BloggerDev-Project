import tkinter as tk
from tkinter import ttk, messagebox
import pyodbc

# Veritabanı bağlantısı
server = 'SORA\\SQLEXPRESS'
database = 'BloggerDev'
connection = pyodbc.connect(
    f'DRIVER={{ODBC Driver 17 for SQL Server}};'
    f'SERVER={server};'
    f'DATABASE={database};'
    f'Trusted_Connection=yes;'
)

cursor = connection.cursor()

# Bağlantı testi
try:
    cursor.execute("SELECT DB_NAME()")
    print(f"Bağlanılan veritabanı: {cursor.fetchone()[0]}")
except Exception as e:
    print(f"Hata: {e}")

# İstatistik verilerini çeken fonksiyonlar
def get_total_posts():
    try:
        cursor.execute("SELECT COUNT(*) FROM dbo.Post")
        result = cursor.fetchone()
        return result[0] if result else 0
    except Exception as e:
        print(f"Post sayısı alınamadı: {e}")
        return 0

def get_total_users():
    try:
        cursor.execute("SELECT COUNT(*) FROM dbo.Users")
        result = cursor.fetchone()
        return result[0] if result else 0
    except Exception as e:
        print(f"Kullanıcı sayısı alınamadı: {e}")
        return 0

def get_total_comments():
    try:
        cursor.execute("SELECT COUNT(*) FROM dbo.Comments")
        result = cursor.fetchone()
        return result[0] if result else 0
    except Exception as e:
        print(f"Yorum sayısı alınamadı: {e}")
        return 0

def get_category_stats():
    try:
        cursor.execute("""
            SELECT TOP 5 c.categories_name, COUNT(p.post_id) as PostCount
            FROM dbo.Categories c
            LEFT JOIN dbo.Post p ON c.categories_id = p.categories_id
            GROUP BY c.categories_name
            ORDER BY PostCount DESC
        """)
        return cursor.fetchall()
    except Exception as e:
        print(f"Kategori istatistikleri alınamadı: {e}")
        return []

def get_recent_posts():
    try:
        cursor.execute("""
            SELECT TOP 5 p.post_title, c.categories_name as Category, p.post_date
            FROM dbo.Post p
            LEFT JOIN dbo.Categories c ON p.categories_id = c.categories_id
            ORDER BY p.post_date DESC
        """)
        return cursor.fetchall()
    except Exception as e:
        print(f"Son yazılar alınamadı: {e}")
        return []

def refresh_data():
    """Dashboard verilerini yeniler"""
    total_posts = get_total_posts()
    total_users = get_total_users()
    total_comments = get_total_comments()
    
    for widget in stats_inner.winfo_children():
        widget.destroy()
    
    create_stat_card(stats_inner, "Toplam Yazı", total_posts, 0)
    create_stat_card(stats_inner, "Kullanıcı", total_users, 1)
    create_stat_card(stats_inner, "Yorum", total_comments, 2)
    
    for widget in category_frame.winfo_children():
        widget.destroy()
    
    category_stats = get_category_stats()
    max_count = max([stat[1] for stat in category_stats]) if category_stats else 1
    
    for idx, (cat_name, count) in enumerate(category_stats, 1):
        cat_row = tk.Frame(category_frame, bg="#f0f0f0")
        cat_row.pack(fill="x", pady=2)
        
        label_text = f"{idx}. {cat_name}: {count} yazı"
        tk.Label(cat_row, text=label_text, font=("Arial", 10), 
                 bg="#f0f0f0", width=30, anchor="w").pack(side="left")
        
        bar_length = int((count / max_count) * 200) if max_count > 0 else 0
        canvas = tk.Canvas(cat_row, width=bar_length, height=20, bg="#3498db", highlightthickness=0)
        canvas.pack(side="left", padx=5)
    
    tree.delete(*tree.get_children())
    recent_posts = get_recent_posts()
    for post in recent_posts:
        title = post[0][:50] + "..." if post[0] and len(post[0]) > 50 else post[0]
        category = post[1] if post[1] else "Kategorisiz"
        date = post[2].strftime("%d/%m/%Y") if post[2] else "Tarih yok"
        tree.insert("", "end", values=(title, category, date))
    
    messagebox.showinfo("Yenileme", "Dashboard başarıyla yenilendi!")

# YAZILAR PENCERESI
def open_posts_window():
    posts_win = tk.Toplevel(root)
    posts_win.title("Yazı Yönetimi")
    posts_win.geometry("900x600")
    posts_win.configure(bg="#f0f0f0")
    
    title_frame = tk.Frame(posts_win, bg="#2ecc71", height=50)
    title_frame.pack(fill="x")
    tk.Label(title_frame, text="📝 Yazı Yönetimi", font=("Arial", 16, "bold"), 
             bg="#2ecc71", fg="white").pack(pady=10)
    
    main = tk.Frame(posts_win, bg="#f0f0f0", padx=20, pady=20)
    main.pack(fill="both", expand=True)
    
    # Yazı listesi
    list_frame = tk.LabelFrame(main, text="Tüm Yazılar", font=("Arial", 11, "bold"), 
                               bg="#f0f0f0", padx=10, pady=10)
    list_frame.pack(fill="both", expand=True)
    
    columns = ("ID", "Başlık", "Kategori", "Tarih")
    posts_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=15)
    
    posts_tree.heading("ID", text="ID")
    posts_tree.heading("Başlık", text="Başlık")
    posts_tree.heading("Kategori", text="Kategori")
    posts_tree.heading("Tarih", text="Tarih")
    
    posts_tree.column("ID", width=50)
    posts_tree.column("Başlık", width=400)
    posts_tree.column("Kategori", width=150)
    posts_tree.column("Tarih", width=100)
    
    scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=posts_tree.yview)
    posts_tree.configure(yscrollcommand=scrollbar.set)
    posts_tree.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")
    
    # Verileri yükle
    try:
        cursor.execute("""
            SELECT p.post_id, p.post_title, c.categories_name, p.post_date
            FROM dbo.Post p
            LEFT JOIN dbo.Categories c ON p.categories_id = c.categories_id
            ORDER BY p.post_date DESC
        """)
        for post in cursor.fetchall():
            posts_tree.insert("", "end", values=(
                post[0],
                post[1][:60] + "..." if len(post[1]) > 60 else post[1],
                post[2] if post[2] else "Kategorisiz",
                post[3].strftime("%d/%m/%Y") if post[3] else "-"
            ))
    except Exception as e:
        messagebox.showerror("Hata", f"Yazılar yüklenemedi: {e}")
    
    # Butonlar
    btn_frame = tk.Frame(main, bg="#f0f0f0")
    btn_frame.pack(fill="x", pady=(10, 0))
    
    tk.Button(btn_frame, text="➕ Yeni Yazı", bg="#2ecc71", fg="white", 
              font=("Arial", 10), padx=15, pady=5).pack(side="left", padx=5)
    tk.Button(btn_frame, text="✏️ Düzenle", bg="#3498db", fg="white", 
              font=("Arial", 10), padx=15, pady=5).pack(side="left", padx=5)
    tk.Button(btn_frame, text="🗑️ Sil", bg="#e74c3c", fg="white", 
              font=("Arial", 10), padx=15, pady=5).pack(side="left", padx=5)

# KATEGORİLER PENCERESI
def open_categories_window():
    cat_win = tk.Toplevel(root)
    cat_win.title("Kategori Yönetimi")
    cat_win.geometry("700x500")
    cat_win.configure(bg="#f0f0f0")
    
    title_frame = tk.Frame(cat_win, bg="#e74c3c", height=50)
    title_frame.pack(fill="x")
    tk.Label(title_frame, text="🏷️ Kategori Yönetimi", font=("Arial", 16, "bold"), 
             bg="#e74c3c", fg="white").pack(pady=10)
    
    main = tk.Frame(cat_win, bg="#f0f0f0", padx=20, pady=20)
    main.pack(fill="both", expand=True)
    
    # Kategori listesi
    list_frame = tk.LabelFrame(main, text="Tüm Kategoriler", font=("Arial", 11, "bold"), 
                               bg="#f0f0f0", padx=10, pady=10)
    list_frame.pack(fill="both", expand=True)
    
    columns = ("ID", "Kategori Adı", "Tip", "Yazı Sayısı")
    cat_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=12)
    
    cat_tree.heading("ID", text="ID")
    cat_tree.heading("Kategori Adı", text="Kategori Adı")
    cat_tree.heading("Tip", text="Tip")
    cat_tree.heading("Yazı Sayısı", text="Yazı Sayısı")
    
    cat_tree.column("ID", width=50)
    cat_tree.column("Kategori Adı", width=250)
    cat_tree.column("Tip", width=150)
    cat_tree.column("Yazı Sayısı", width=100)
    
    scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=cat_tree.yview)
    cat_tree.configure(yscrollcommand=scrollbar.set)
    cat_tree.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")
    
    # Verileri yükle
    try:
        cursor.execute("""
            SELECT c.categories_id, c.categories_name, c.categories_type, COUNT(p.post_id) as PostCount
            FROM dbo.Categories c
            LEFT JOIN dbo.Post p ON c.categories_id = p.categories_id
            GROUP BY c.categories_id, c.categories_name, c.categories_type
            ORDER BY c.categories_name
        """)
        for cat in cursor.fetchall():
            cat_tree.insert("", "end", values=(cat[0], cat[1], cat[2] if cat[2] else "-", cat[3]))
    except Exception as e:
        messagebox.showerror("Hata", f"Kategoriler yüklenemedi: {e}")
    
    # Butonlar
    btn_frame = tk.Frame(main, bg="#f0f0f0")
    btn_frame.pack(fill="x", pady=(10, 0))
    
    tk.Button(btn_frame, text="➕ Yeni Kategori", bg="#2ecc71", fg="white", 
              font=("Arial", 10), padx=15, pady=5).pack(side="left", padx=5)
    tk.Button(btn_frame, text="✏️ Düzenle", bg="#3498db", fg="white", 
              font=("Arial", 10), padx=15, pady=5).pack(side="left", padx=5)
    tk.Button(btn_frame, text="🗑️ Sil", bg="#e74c3c", fg="white", 
              font=("Arial", 10), padx=15, pady=5).pack(side="left", padx=5)

# KULLANICILAR PENCERESI
def open_users_window():
    users_win = tk.Toplevel(root)
    users_win.title("Kullanıcı Yönetimi")
    users_win.geometry("900x600")
    users_win.configure(bg="#f0f0f0")
    
    title_frame = tk.Frame(users_win, bg="#9b59b6", height=50)
    title_frame.pack(fill="x")
    tk.Label(title_frame, text="👥 Kullanıcı Yönetimi", font=("Arial", 16, "bold"), 
             bg="#9b59b6", fg="white").pack(pady=10)
    
    main = tk.Frame(users_win, bg="#f0f0f0", padx=20, pady=20)
    main.pack(fill="both", expand=True)
    
    # Kullanıcı listesi
    list_frame = tk.LabelFrame(main, text="Tüm Kullanıcılar", font=("Arial", 11, "bold"), 
                               bg="#f0f0f0", padx=10, pady=10)
    list_frame.pack(fill="both", expand=True)
    
    columns = ("ID", "Ad", "Email", "Adres")
    users_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=15)
    
    users_tree.heading("ID", text="ID")
    users_tree.heading("Ad", text="Kullanıcı Adı")
    users_tree.heading("Email", text="Email")
    users_tree.heading("Adres", text="Adres")
    
    users_tree.column("ID", width=50)
    users_tree.column("Ad", width=200)
    users_tree.column("Email", width=250)
    users_tree.column("Adres", width=300)
    
    scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=users_tree.yview)
    users_tree.configure(yscrollcommand=scrollbar.set)
    users_tree.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")
    
    # Verileri yükle
    try:
        cursor.execute("""
            SELECT users_id, users_name, users_email, users_address
            FROM dbo.Users
            ORDER BY users_name
        """)
        for user in cursor.fetchall():
            users_tree.insert("", "end", values=(
                user[0],
                user[1],
                user[2],
                user[3] if user[3] else "-"
            ))
    except Exception as e:
        messagebox.showerror("Hata", f"Kullanıcılar yüklenemedi: {e}")
    
    # Butonlar
    btn_frame = tk.Frame(main, bg="#f0f0f0")
    btn_frame.pack(fill="x", pady=(10, 0))
    
    tk.Button(btn_frame, text="➕ Yeni Kullanıcı", bg="#2ecc71", fg="white", 
              font=("Arial", 10), padx=15, pady=5).pack(side="left", padx=5)
    tk.Button(btn_frame, text="✏️ Düzenle", bg="#3498db", fg="white", 
              font=("Arial", 10), padx=15, pady=5).pack(side="left", padx=5)
    tk.Button(btn_frame, text="🗑️ Sil", bg="#e74c3c", fg="white", 
              font=("Arial", 10), padx=15, pady=5).pack(side="left", padx=5)

# Ana pencere
root = tk.Tk()
root.title("BloggerDev Yönetim Paneli")
root.geometry("800x600")
root.configure(bg="#f0f0f0")

# Başlık
title_frame = tk.Frame(root, bg="#2c3e50", height=60)
title_frame.pack(fill="x")
title_label = tk.Label(title_frame, text="📊 BloggerDev Yönetim Paneli", 
                       font=("Arial", 18, "bold"), bg="#2c3e50", fg="white")
title_label.pack(pady=15)

# Ana içerik frame
main_frame = tk.Frame(root, bg="#f0f0f0")
main_frame.pack(fill="both", expand=True, padx=20, pady=20)

# İstatistikler bölümü
stats_frame = tk.LabelFrame(main_frame, text="📊 İSTATİSTİKLER", 
                            font=("Arial", 12, "bold"), bg="#f0f0f0", padx=10, pady=10)
stats_frame.pack(fill="x", pady=(0, 15))

stats_inner = tk.Frame(stats_frame, bg="#f0f0f0")
stats_inner.pack()

# İstatistik kartları
def create_stat_card(parent, title, value, col):
    card = tk.Frame(parent, bg="white", relief="raised", borderwidth=2)
    card.grid(row=0, column=col, padx=10, pady=5, ipadx=20, ipady=10)
    
    tk.Label(card, text=str(value), font=("Arial", 24, "bold"), 
             bg="white", fg="#3498db").pack()
    tk.Label(card, text=title, font=("Arial", 10), 
             bg="white", fg="#7f8c8d").pack()

total_posts = get_total_posts()
total_users = get_total_users()
total_comments = get_total_comments()

create_stat_card(stats_inner, "Toplam Yazı", total_posts, 0)
create_stat_card(stats_inner, "Kullanıcı", total_users, 1)
create_stat_card(stats_inner, "Yorum", total_comments, 2)

# Popüler Kategoriler bölümü
category_frame = tk.LabelFrame(main_frame, text="🏆 EN POPÜLER KATEGORİLER", 
                               font=("Arial", 12, "bold"), bg="#f0f0f0", padx=10, pady=10)
category_frame.pack(fill="x", pady=(0, 15))

category_stats = get_category_stats()
max_count = max([stat[1] for stat in category_stats]) if category_stats else 1

for idx, (cat_name, count) in enumerate(category_stats, 1):
    cat_row = tk.Frame(category_frame, bg="#f0f0f0")
    cat_row.pack(fill="x", pady=2)
    
    label_text = f"{idx}. {cat_name}: {count} yazı"
    tk.Label(cat_row, text=label_text, font=("Arial", 10), 
             bg="#f0f0f0", width=30, anchor="w").pack(side="left")
    
    bar_length = int((count / max_count) * 200) if max_count > 0 else 0
    canvas = tk.Canvas(cat_row, width=bar_length, height=20, bg="#3498db", highlightthickness=0)
    canvas.pack(side="left", padx=5)

# Son Yazılar bölümü
posts_frame = tk.LabelFrame(main_frame, text="📝 SON YAZILAR", 
                            font=("Arial", 12, "bold"), bg="#f0f0f0", padx=10, pady=10)
posts_frame.pack(fill="both", expand=True, pady=(0, 15))

style = ttk.Style()
style.configure("Treeview", font=("Arial", 10), rowheight=25)
style.configure("Treeview.Heading", font=("Arial", 10, "bold"))

columns = ("Başlık", "Kategori", "Tarih")
tree = ttk.Treeview(posts_frame, columns=columns, show="headings", height=6)

tree.heading("Başlık", text="Başlık")
tree.heading("Kategori", text="Kategori")
tree.heading("Tarih", text="Tarih")

tree.column("Başlık", width=400)
tree.column("Kategori", width=150)
tree.column("Tarih", width=150)

scrollbar = ttk.Scrollbar(posts_frame, orient="vertical", command=tree.yview)
tree.configure(yscrollcommand=scrollbar.set)

tree.pack(side="left", fill="both", expand=True)
scrollbar.pack(side="right", fill="y")

recent_posts = get_recent_posts()
for post in recent_posts:
    title = post[0][:50] + "..." if post[0] and len(post[0]) > 50 else post[0]
    category = post[1] if post[1] else "Kategorisiz"
    date = post[2].strftime("%d/%m/%Y") if post[2] else "Tarih yok"
    tree.insert("", "end", values=(title, category, date))

# Alt butonlar
button_frame = tk.Frame(main_frame, bg="#f0f0f0")
button_frame.pack(fill="x")

btn_refresh = tk.Button(button_frame, text="🔄 Yenile", font=("Arial", 11), 
                        bg="#3498db", fg="white", padx=20, pady=8, 
                        cursor="hand2", command=refresh_data)
btn_refresh.pack(side="left", padx=5)

btn_posts = tk.Button(button_frame, text="📝 Yazılar", font=("Arial", 11), 
                      bg="#2ecc71", fg="white", padx=20, pady=8, 
                      cursor="hand2", command=open_posts_window)
btn_posts.pack(side="left", padx=5)

btn_categories = tk.Button(button_frame, text="🏷️ Kategoriler", font=("Arial", 11), 
                           bg="#e74c3c", fg="white", padx=20, pady=8, 
                           cursor="hand2", command=open_categories_window)
btn_categories.pack(side="left", padx=5)

btn_users = tk.Button(button_frame, text="👥 Kullanıcılar", font=("Arial", 11), 
                      bg="#9b59b6", fg="white", padx=20, pady=8, 
                      cursor="hand2", command=open_users_window)
btn_users.pack(side="left", padx=5)

root.mainloop()

connection.close()