import tkinter as tk
from tkinter import ttk, messagebox
import pyodbc
from datetime import datetime

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

# ============================================
# İSTATİSTİK FONKSİYONLARI
# ============================================

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

def get_all_categories():
    """Tüm kategorileri getirir (Combobox için)"""
    try:
        cursor.execute("SELECT categories_id, categories_name FROM dbo.Categories ORDER BY categories_name")
        return cursor.fetchall()
    except Exception as e:
        print(f"Kategoriler alınamadı: {e}")
        return []

def get_all_users():
    """Tüm kullanıcıları getirir (Combobox için)"""
    try:
        cursor.execute("SELECT users_id, users_name FROM dbo.Users ORDER BY users_name")
        return cursor.fetchall()
    except Exception as e:
        print(f"Kullanıcılar alınamadı: {e}")
        return []

def get_all_tags():
    """Tüm etiketleri getirir"""
    try:
        cursor.execute("SELECT tags_id, tag_name FROM dbo.Tags ORDER BY tag_name")
        return cursor.fetchall()
    except Exception as e:
        print(f"Etiketler alınamadı: {e}")
        return []

def get_post_tags(post_id):
    """Bir yazının etiketlerini getirir"""
    try:
        cursor.execute("""
            SELECT t.tags_id, t.tag_name
            FROM dbo.Tags t
            INNER JOIN dbo.Post_Tags pt ON t.tags_id = pt.tags_id
            WHERE pt.post_id = ?
            ORDER BY t.tag_name
        """, (post_id,))
        return cursor.fetchall()
    except Exception as e:
        print(f"Yazı etiketleri alınamadı: {e}")
        return []

def get_total_tags():
    """Toplam etiket sayısını getirir"""
    try:
        cursor.execute("SELECT COUNT(*) FROM dbo.Tags")
        result = cursor.fetchone()
        return result[0] if result else 0
    except Exception as e:
        print(f"Etiket sayısı alınamadı: {e}")
        return 0

# ============================================
# DASHBOARD YENİLEME
# ============================================

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

# ============================================
# YAZI YÖNETİMİ (CRUD)
# ============================================

def open_posts_window():
    posts_win = tk.Toplevel(root)
    posts_win.title("Yazı Yönetimi")
    posts_win.geometry("1000x600")
    posts_win.configure(bg="#f0f0f0")
    
    title_frame = tk.Frame(posts_win, bg="#2ecc71", height=50)
    title_frame.pack(fill="x")
    tk.Label(title_frame, text="📝 Yazı Yönetimi", font=("Arial", 16, "bold"), 
             bg="#2ecc71", fg="white").pack(pady=10)
    
    main = tk.Frame(posts_win, bg="#f0f0f0", padx=20, pady=20)
    main.pack(fill="both", expand=True)
    
    # Bilgi etiketi
    info_label = tk.Label(main, text="💡 Detay görüntülemek için yazıya çift tıklayın", 
                          font=("Arial", 9, "italic"), bg="#f0f0f0", fg="#7f8c8d")
    info_label.pack(anchor="w")
    
    # Yazı listesi
    list_frame = tk.LabelFrame(main, text="Tüm Yazılar", font=("Arial", 11, "bold"), 
                               bg="#f0f0f0", padx=10, pady=10)
    list_frame.pack(fill="both", expand=True)
    
    columns = ("ID", "Başlık", "Yazar", "Kategori", "Tarih")
    posts_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=15)
    
    posts_tree.heading("ID", text="ID")
    posts_tree.heading("Başlık", text="Başlık")
    posts_tree.heading("Yazar", text="Yazar")
    posts_tree.heading("Kategori", text="Kategori")
    posts_tree.heading("Tarih", text="Tarih")
    
    posts_tree.column("ID", width=50)
    posts_tree.column("Başlık", width=350)
    posts_tree.column("Yazar", width=150)
    posts_tree.column("Kategori", width=150)
    posts_tree.column("Tarih", width=100)
    
    scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=posts_tree.yview)
    posts_tree.configure(yscrollcommand=scrollbar.set)
    posts_tree.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")
    
    def load_posts():
        """Yazıları yükle"""
        posts_tree.delete(*posts_tree.get_children())
        try:
            cursor.execute("""
                SELECT p.post_id, p.post_title, u.users_name, c.categories_name, p.post_date
                FROM dbo.Post p
                LEFT JOIN dbo.Categories c ON p.categories_id = c.categories_id
                LEFT JOIN dbo.Users u ON p.users_id = u.users_id
                ORDER BY p.post_date DESC
            """)
            for post in cursor.fetchall():
                posts_tree.insert("", "end", values=(
                    post[0],
                    post[1][:50] + "..." if post[1] and len(post[1]) > 50 else post[1],
                    post[2] if post[2] else "Belirtilmemiş",
                    post[3] if post[3] else "Kategorisiz",
                    post[4].strftime("%d/%m/%Y") if post[4] else "-"
                ))
        except Exception as e:
            messagebox.showerror("Hata", f"Yazılar yüklenemedi: {e}")
    
    # İlk yükleme
    load_posts()
    
    # ---- YAZI DETAY GÖRÜNTÜLEME (Çift Tıklama) ----
    def show_post_detail(event):
        selected = posts_tree.selection()
        if not selected:
            return
        
        item = posts_tree.item(selected[0])
        post_id = item['values'][0]
        
        # Yazı detaylarını getir
        try:
            cursor.execute("""
                SELECT p.post_id, p.post_title, p.post_content, p.post_date,
                       u.users_name, c.categories_name
                FROM dbo.Post p
                LEFT JOIN dbo.Categories c ON p.categories_id = c.categories_id
                LEFT JOIN dbo.Users u ON p.users_id = u.users_id
                WHERE p.post_id = ?
            """, (post_id,))
            post_data = cursor.fetchone()
            if not post_data:
                messagebox.showerror("Hata", "Yazı bulunamadı!")
                return
        except Exception as e:
            messagebox.showerror("Hata", f"Veri alınamadı: {e}")
            return
        
        # Yazının etiketlerini getir
        post_tags = get_post_tags(post_id)
        tags_text = ", ".join([tag[1] for tag in post_tags]) if post_tags else "Etiket yok"
        
        # Detay penceresi
        detail_win = tk.Toplevel(posts_win)
        detail_win.title(f"Yazı Detayı - {post_data[1][:30]}...")
        detail_win.geometry("700x550")
        detail_win.configure(bg="#f0f0f0")
        
        # Başlık
        header = tk.Frame(detail_win, bg="#2ecc71", height=50)
        header.pack(fill="x")
        tk.Label(header, text="📄 Yazı Detayı", font=("Arial", 16, "bold"),
                 bg="#2ecc71", fg="white").pack(pady=12)
        
        # İçerik
        content_frame = tk.Frame(detail_win, bg="#f0f0f0", padx=20, pady=20)
        content_frame.pack(fill="both", expand=True)
        
        # Bilgi kartı
        info_card = tk.LabelFrame(content_frame, text="Yazı Bilgileri", font=("Arial", 10, "bold"),
                                   bg="white", padx=15, pady=10)
        info_card.pack(fill="x", pady=(0, 15))
        
        # Başlık
        tk.Label(info_card, text="Başlık:", font=("Arial", 10, "bold"), bg="white").grid(row=0, column=0, sticky="w", pady=2)
        tk.Label(info_card, text=post_data[1] if post_data[1] else "-", font=("Arial", 10), bg="white", wraplength=500, justify="left").grid(row=0, column=1, sticky="w", padx=(10,0), pady=2)
        
        # Yazar
        tk.Label(info_card, text="Yazar:", font=("Arial", 10, "bold"), bg="white").grid(row=1, column=0, sticky="w", pady=2)
        tk.Label(info_card, text=post_data[4] if post_data[4] else "Belirtilmemiş", font=("Arial", 10), bg="white").grid(row=1, column=1, sticky="w", padx=(10,0), pady=2)
        
        # Kategori
        tk.Label(info_card, text="Kategori:", font=("Arial", 10, "bold"), bg="white").grid(row=2, column=0, sticky="w", pady=2)
        tk.Label(info_card, text=post_data[5] if post_data[5] else "Kategorisiz", font=("Arial", 10), bg="white").grid(row=2, column=1, sticky="w", padx=(10,0), pady=2)
        
        # Tarih
        tk.Label(info_card, text="Tarih:", font=("Arial", 10, "bold"), bg="white").grid(row=3, column=0, sticky="w", pady=2)
        date_str = post_data[3].strftime("%d/%m/%Y %H:%M") if post_data[3] else "-"
        tk.Label(info_card, text=date_str, font=("Arial", 10), bg="white").grid(row=3, column=1, sticky="w", padx=(10,0), pady=2)
        
        # Etiketler
        tk.Label(info_card, text="Etiketler:", font=("Arial", 10, "bold"), bg="white").grid(row=4, column=0, sticky="w", pady=2)
        tags_label = tk.Label(info_card, text=tags_text, font=("Arial", 10), bg="white", fg="#3498db", wraplength=500, justify="left")
        tags_label.grid(row=4, column=1, sticky="w", padx=(10,0), pady=2)
        
        # İçerik
        content_card = tk.LabelFrame(content_frame, text="İçerik", font=("Arial", 10, "bold"),
                                      bg="white", padx=10, pady=10)
        content_card.pack(fill="both", expand=True)
        
        content_text = tk.Text(content_card, font=("Arial", 10), wrap="word", height=12)
        content_text.insert("1.0", post_data[2] if post_data[2] else "İçerik yok")
        content_text.config(state="disabled")  # Salt okunur
        
        content_scroll = ttk.Scrollbar(content_card, orient="vertical", command=content_text.yview)
        content_text.configure(yscrollcommand=content_scroll.set)
        content_text.pack(side="left", fill="both", expand=True)
        content_scroll.pack(side="right", fill="y")
        
        # Kapat butonu
        tk.Button(content_frame, text="❌ Kapat", bg="#95a5a6", fg="white",
                  font=("Arial", 11), padx=20, pady=5, command=detail_win.destroy).pack(pady=(15, 0))
    
    # Çift tıklama event'i bağla
    posts_tree.bind("<Double-1>", show_post_detail)
    
    # ---- YAZI EKLEME ----
    def add_post():
        add_win = tk.Toplevel(posts_win)
        add_win.title("Yeni Yazı Ekle")
        add_win.geometry("500x520")
        add_win.configure(bg="#f0f0f0")
        add_win.grab_set()  # Modal pencere
        
        # Başlık
        header = tk.Frame(add_win, bg="#2ecc71", height=40)
        header.pack(fill="x")
        tk.Label(header, text="➕ Yeni Yazı Ekle", font=("Arial", 14, "bold"),
                 bg="#2ecc71", fg="white").pack(pady=8)
        
        # Form
        form = tk.Frame(add_win, bg="#f0f0f0", padx=20, pady=20)
        form.pack(fill="both", expand=True)
        
        # Başlık alanı
        tk.Label(form, text="Başlık:", font=("Arial", 11), bg="#f0f0f0").pack(anchor="w")
        entry_title = tk.Entry(form, font=("Arial", 11), width=50)
        entry_title.pack(fill="x", pady=(0, 10))
        
        # İçerik alanı
        tk.Label(form, text="İçerik:", font=("Arial", 11), bg="#f0f0f0").pack(anchor="w")
        text_content = tk.Text(form, font=("Arial", 10), height=8, width=50)
        text_content.pack(fill="both", expand=True, pady=(0, 10))
        
        # Yazar seçimi
        tk.Label(form, text="Yazar:", font=("Arial", 11), bg="#f0f0f0").pack(anchor="w")
        users = get_all_users()
        user_names = ["Yazar Seçin..."] + [user[1] for user in users]
        user_var = tk.StringVar(value="Yazar Seçin...")
        combo_user = ttk.Combobox(form, textvariable=user_var, values=user_names, 
                                   state="readonly", font=("Arial", 11))
        combo_user.pack(fill="x", pady=(0, 10))
        
        # Kategori seçimi
        tk.Label(form, text="Kategori:", font=("Arial", 11), bg="#f0f0f0").pack(anchor="w")
        categories = get_all_categories()
        category_names = ["Kategori Seçin..."] + [cat[1] for cat in categories]
        category_var = tk.StringVar(value="Kategori Seçin...")
        combo_category = ttk.Combobox(form, textvariable=category_var, values=category_names, 
                                       state="readonly", font=("Arial", 11))
        combo_category.pack(fill="x", pady=(0, 15))
        
        def save_post():
            title = entry_title.get().strip()
            content = text_content.get("1.0", tk.END).strip()
            selected_user = user_var.get()
            selected_category = category_var.get()
            
            # Validasyon
            if not title:
                messagebox.showwarning("Uyarı", "Başlık boş bırakılamaz!", parent=add_win)
                return
            if not content:
                messagebox.showwarning("Uyarı", "İçerik boş bırakılamaz!", parent=add_win)
                return
            if selected_user == "Yazar Seçin...":
                messagebox.showwarning("Uyarı", "Lütfen bir yazar seçin!", parent=add_win)
                return
            if selected_category == "Kategori Seçin...":
                messagebox.showwarning("Uyarı", "Lütfen bir kategori seçin!", parent=add_win)
                return
            
            # ID'leri bul
            user_id = None
            for user in users:
                if user[1] == selected_user:
                    user_id = user[0]
                    break
            
            category_id = None
            for cat in categories:
                if cat[1] == selected_category:
                    category_id = cat[0]
                    break
            
            try:
                cursor.execute("""
                    INSERT INTO dbo.Post (post_title, post_content, users_id, categories_id, post_date)
                    VALUES (?, ?, ?, ?, ?)
                """, (title, content, user_id, category_id, datetime.now()))
                connection.commit()
                messagebox.showinfo("Başarılı", "Yazı başarıyla eklendi!", parent=add_win)
                add_win.destroy()
                load_posts()
            except Exception as e:
                messagebox.showerror("Hata", f"Yazı eklenirken hata oluştu: {e}", parent=add_win)
        
        # Butonlar
        btn_frame = tk.Frame(form, bg="#f0f0f0")
        btn_frame.pack(fill="x", pady=(10, 0))
        
        tk.Button(btn_frame, text="💾 Kaydet", bg="#2ecc71", fg="white",
                  font=("Arial", 11), padx=20, pady=5, command=save_post).pack(side="left", padx=5)
        tk.Button(btn_frame, text="❌ İptal", bg="#95a5a6", fg="white",
                  font=("Arial", 11), padx=20, pady=5, command=add_win.destroy).pack(side="left", padx=5)
    
    # ---- YAZI DÜZENLEME ----
    def edit_post():
        selected = posts_tree.selection()
        if not selected:
            messagebox.showwarning("Uyarı", "Lütfen düzenlemek için bir yazı seçin!")
            return
        
        item = posts_tree.item(selected[0])
        post_id = item['values'][0]
        
        # Mevcut veriyi getir
        try:
            cursor.execute("""
                SELECT post_id, post_title, post_content, categories_id, users_id
                FROM dbo.Post WHERE post_id = ?
            """, (post_id,))
            post_data = cursor.fetchone()
            if not post_data:
                messagebox.showerror("Hata", "Yazı bulunamadı!")
                return
        except Exception as e:
            messagebox.showerror("Hata", f"Veri alınamadı: {e}")
            return
        
        edit_win = tk.Toplevel(posts_win)
        edit_win.title("Yazı Düzenle")
        edit_win.geometry("500x520")
        edit_win.configure(bg="#f0f0f0")
        edit_win.grab_set()
        
        # Başlık
        header = tk.Frame(edit_win, bg="#3498db", height=40)
        header.pack(fill="x")
        tk.Label(header, text="✏️ Yazı Düzenle", font=("Arial", 14, "bold"),
                 bg="#3498db", fg="white").pack(pady=8)
        
        # Form
        form = tk.Frame(edit_win, bg="#f0f0f0", padx=20, pady=20)
        form.pack(fill="both", expand=True)
        
        # Başlık alanı
        tk.Label(form, text="Başlık:", font=("Arial", 11), bg="#f0f0f0").pack(anchor="w")
        entry_title = tk.Entry(form, font=("Arial", 11), width=50)
        entry_title.insert(0, post_data[1] if post_data[1] else "")
        entry_title.pack(fill="x", pady=(0, 10))
        
        # İçerik alanı
        tk.Label(form, text="İçerik:", font=("Arial", 11), bg="#f0f0f0").pack(anchor="w")
        text_content = tk.Text(form, font=("Arial", 10), height=8, width=50)
        text_content.insert("1.0", post_data[2] if post_data[2] else "")
        text_content.pack(fill="both", expand=True, pady=(0, 10))
        
        # Yazar seçimi
        tk.Label(form, text="Yazar:", font=("Arial", 11), bg="#f0f0f0").pack(anchor="w")
        users = get_all_users()
        user_names = [user[1] for user in users]
        
        # Mevcut yazarı bul
        current_user = ""
        for user in users:
            if user[0] == post_data[4]:
                current_user = user[1]
                break
        
        user_var = tk.StringVar(value=current_user if current_user else user_names[0] if user_names else "")
        combo_user = ttk.Combobox(form, textvariable=user_var, values=user_names, 
                                   state="readonly", font=("Arial", 11))
        combo_user.pack(fill="x", pady=(0, 10))
        
        # Kategori seçimi
        tk.Label(form, text="Kategori:", font=("Arial", 11), bg="#f0f0f0").pack(anchor="w")
        categories = get_all_categories()
        category_names = [cat[1] for cat in categories]
        
        # Mevcut kategoriyi bul
        current_category = ""
        for cat in categories:
            if cat[0] == post_data[3]:
                current_category = cat[1]
                break
        
        category_var = tk.StringVar(value=current_category if current_category else category_names[0] if category_names else "")
        combo_category = ttk.Combobox(form, textvariable=category_var, values=category_names, 
                                       state="readonly", font=("Arial", 11))
        combo_category.pack(fill="x", pady=(0, 15))
        
        def update_post():
            title = entry_title.get().strip()
            content = text_content.get("1.0", tk.END).strip()
            selected_user = user_var.get()
            selected_category = category_var.get()
            
            if not title:
                messagebox.showwarning("Uyarı", "Başlık boş bırakılamaz!", parent=edit_win)
                return
            
            # ID'leri bul
            user_id = None
            for user in users:
                if user[1] == selected_user:
                    user_id = user[0]
                    break
            
            category_id = None
            for cat in categories:
                if cat[1] == selected_category:
                    category_id = cat[0]
                    break
            
            try:
                cursor.execute("""
                    UPDATE dbo.Post 
                    SET post_title = ?, post_content = ?, users_id = ?, categories_id = ?
                    WHERE post_id = ?
                """, (title, content, user_id, category_id, post_id))
                connection.commit()
                messagebox.showinfo("Başarılı", "Yazı başarıyla güncellendi!", parent=edit_win)
                edit_win.destroy()
                load_posts()
            except Exception as e:
                messagebox.showerror("Hata", f"Yazı güncellenirken hata oluştu: {e}", parent=edit_win)
        
        # Butonlar
        btn_frame = tk.Frame(form, bg="#f0f0f0")
        btn_frame.pack(fill="x", pady=(10, 0))
        
        tk.Button(btn_frame, text="💾 Güncelle", bg="#3498db", fg="white",
                  font=("Arial", 11), padx=20, pady=5, command=update_post).pack(side="left", padx=5)
        tk.Button(btn_frame, text="❌ İptal", bg="#95a5a6", fg="white",
                  font=("Arial", 11), padx=20, pady=5, command=edit_win.destroy).pack(side="left", padx=5)
    
    # ---- YAZI SİLME ----
    def delete_post():
        selected = posts_tree.selection()
        if not selected:
            messagebox.showwarning("Uyarı", "Lütfen silmek için bir yazı seçin!")
            return
        
        item = posts_tree.item(selected[0])
        post_id = item['values'][0]
        post_title = item['values'][1]
        
        # Yazıya ait yorum sayısını kontrol et
        try:
            cursor.execute("SELECT COUNT(*) FROM dbo.Comments WHERE post_id = ?", (post_id,))
            comment_count = cursor.fetchone()[0]
        except:
            comment_count = 0
        
        # Onay mesajını yorum durumuna göre ayarla
        if comment_count > 0:
            confirm = messagebox.askyesno("Onay", 
                f"'{post_title}' başlıklı yazıyı silmek istediğinizden emin misiniz?\n\n"
                f"⚠️ Bu yazıya ait {comment_count} yorum da silinecektir!\n\n"
                "Bu işlem geri alınamaz!",
                icon='warning')
        else:
            confirm = messagebox.askyesno("Onay", 
                f"'{post_title}' başlıklı yazıyı silmek istediğinizden emin misiniz?\n\nBu işlem geri alınamaz!",
                icon='warning')
        
        if confirm:
            try:
                # Önce yazıya ait etiket ilişkilerini sil
                cursor.execute("DELETE FROM dbo.Post_Tags WHERE post_id = ?", (post_id,))
                # Sonra yazıya ait yorumları sil
                cursor.execute("DELETE FROM dbo.Comments WHERE post_id = ?", (post_id,))
                # En son yazıyı sil
                cursor.execute("DELETE FROM dbo.Post WHERE post_id = ?", (post_id,))
                connection.commit()
                
                if comment_count > 0:
                    messagebox.showinfo("Başarılı", f"Yazı ve {comment_count} yorum başarıyla silindi!")
                else:
                    messagebox.showinfo("Başarılı", "Yazı başarıyla silindi!")
                load_posts()
            except Exception as e:
                connection.rollback()
                messagebox.showerror("Hata", f"Yazı silinirken hata oluştu: {e}")
    
    # Butonlar
    btn_frame = tk.Frame(main, bg="#f0f0f0")
    btn_frame.pack(fill="x", pady=(10, 0))
    
    tk.Button(btn_frame, text="➕ Yeni Yazı", bg="#2ecc71", fg="white", 
              font=("Arial", 10), padx=15, pady=5, command=add_post).pack(side="left", padx=5)
    tk.Button(btn_frame, text="✏️ Düzenle", bg="#3498db", fg="white", 
              font=("Arial", 10), padx=15, pady=5, command=edit_post).pack(side="left", padx=5)
    tk.Button(btn_frame, text="🗑️ Sil", bg="#e74c3c", fg="white", 
              font=("Arial", 10), padx=15, pady=5, command=delete_post).pack(side="left", padx=5)
    tk.Button(btn_frame, text="🔄 Yenile", bg="#95a5a6", fg="white", 
              font=("Arial", 10), padx=15, pady=5, command=load_posts).pack(side="left", padx=5)

# ============================================
# KATEGORİ YÖNETİMİ (CRUD)
# ============================================

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
    
    def load_categories():
        """Kategorileri yükle"""
        cat_tree.delete(*cat_tree.get_children())
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
    
    # İlk yükleme
    load_categories()
    
    # ---- KATEGORİ EKLEME ----
    def add_category():
        add_win = tk.Toplevel(cat_win)
        add_win.title("Yeni Kategori Ekle")
        add_win.geometry("400x250")
        add_win.configure(bg="#f0f0f0")
        add_win.grab_set()
        
        # Başlık
        header = tk.Frame(add_win, bg="#2ecc71", height=40)
        header.pack(fill="x")
        tk.Label(header, text="➕ Yeni Kategori Ekle", font=("Arial", 14, "bold"),
                 bg="#2ecc71", fg="white").pack(pady=8)
        
        # Form
        form = tk.Frame(add_win, bg="#f0f0f0", padx=20, pady=20)
        form.pack(fill="both", expand=True)
        
        # Kategori adı
        tk.Label(form, text="Kategori Adı:", font=("Arial", 11), bg="#f0f0f0").pack(anchor="w")
        entry_name = tk.Entry(form, font=("Arial", 11), width=40)
        entry_name.pack(fill="x", pady=(0, 15))
        
        # Kategori tipi
        tk.Label(form, text="Kategori Tipi:", font=("Arial", 11), bg="#f0f0f0").pack(anchor="w")
        entry_type = tk.Entry(form, font=("Arial", 11), width=40)
        entry_type.pack(fill="x", pady=(0, 15))
        
        def save_category():
            name = entry_name.get().strip()
            cat_type = entry_type.get().strip()
            
            if not name:
                messagebox.showwarning("Uyarı", "Kategori adı boş bırakılamaz!", parent=add_win)
                return
            
            try:
                cursor.execute("""
                    INSERT INTO dbo.Categories (categories_name, categories_type)
                    VALUES (?, ?)
                """, (name, cat_type if cat_type else None))
                connection.commit()
                messagebox.showinfo("Başarılı", "Kategori başarıyla eklendi!", parent=add_win)
                add_win.destroy()
                load_categories()
            except Exception as e:
                messagebox.showerror("Hata", f"Kategori eklenirken hata oluştu: {e}", parent=add_win)
        
        # Butonlar
        btn_frame = tk.Frame(form, bg="#f0f0f0")
        btn_frame.pack(fill="x", pady=(10, 0))
        
        tk.Button(btn_frame, text="💾 Kaydet", bg="#2ecc71", fg="white",
                  font=("Arial", 11), padx=20, pady=5, command=save_category).pack(side="left", padx=5)
        tk.Button(btn_frame, text="❌ İptal", bg="#95a5a6", fg="white",
                  font=("Arial", 11), padx=20, pady=5, command=add_win.destroy).pack(side="left", padx=5)
    
    # ---- KATEGORİ DÜZENLEME ----
    def edit_category():
        selected = cat_tree.selection()
        if not selected:
            messagebox.showwarning("Uyarı", "Lütfen düzenlemek için bir kategori seçin!")
            return
        
        item = cat_tree.item(selected[0])
        cat_id = item['values'][0]
        
        # Mevcut veriyi getir
        try:
            cursor.execute("""
                SELECT categories_id, categories_name, categories_type
                FROM dbo.Categories WHERE categories_id = ?
            """, (cat_id,))
            cat_data = cursor.fetchone()
            if not cat_data:
                messagebox.showerror("Hata", "Kategori bulunamadı!")
                return
        except Exception as e:
            messagebox.showerror("Hata", f"Veri alınamadı: {e}")
            return
        
        edit_win = tk.Toplevel(cat_win)
        edit_win.title("Kategori Düzenle")
        edit_win.geometry("400x250")
        edit_win.configure(bg="#f0f0f0")
        edit_win.grab_set()
        
        # Başlık
        header = tk.Frame(edit_win, bg="#3498db", height=40)
        header.pack(fill="x")
        tk.Label(header, text="✏️ Kategori Düzenle", font=("Arial", 14, "bold"),
                 bg="#3498db", fg="white").pack(pady=8)
        
        # Form
        form = tk.Frame(edit_win, bg="#f0f0f0", padx=20, pady=20)
        form.pack(fill="both", expand=True)
        
        # Kategori adı
        tk.Label(form, text="Kategori Adı:", font=("Arial", 11), bg="#f0f0f0").pack(anchor="w")
        entry_name = tk.Entry(form, font=("Arial", 11), width=40)
        entry_name.insert(0, cat_data[1] if cat_data[1] else "")
        entry_name.pack(fill="x", pady=(0, 15))
        
        # Kategori tipi
        tk.Label(form, text="Kategori Tipi:", font=("Arial", 11), bg="#f0f0f0").pack(anchor="w")
        entry_type = tk.Entry(form, font=("Arial", 11), width=40)
        entry_type.insert(0, cat_data[2] if cat_data[2] else "")
        entry_type.pack(fill="x", pady=(0, 15))
        
        def update_category():
            name = entry_name.get().strip()
            cat_type = entry_type.get().strip()
            
            if not name:
                messagebox.showwarning("Uyarı", "Kategori adı boş bırakılamaz!", parent=edit_win)
                return
            
            try:
                cursor.execute("""
                    UPDATE dbo.Categories 
                    SET categories_name = ?, categories_type = ?
                    WHERE categories_id = ?
                """, (name, cat_type if cat_type else None, cat_id))
                connection.commit()
                messagebox.showinfo("Başarılı", "Kategori başarıyla güncellendi!", parent=edit_win)
                edit_win.destroy()
                load_categories()
            except Exception as e:
                messagebox.showerror("Hata", f"Kategori güncellenirken hata oluştu: {e}", parent=edit_win)
        
        # Butonlar
        btn_frame = tk.Frame(form, bg="#f0f0f0")
        btn_frame.pack(fill="x", pady=(10, 0))
        
        tk.Button(btn_frame, text="💾 Güncelle", bg="#3498db", fg="white",
                  font=("Arial", 11), padx=20, pady=5, command=update_category).pack(side="left", padx=5)
        tk.Button(btn_frame, text="❌ İptal", bg="#95a5a6", fg="white",
                  font=("Arial", 11), padx=20, pady=5, command=edit_win.destroy).pack(side="left", padx=5)
    
    # ---- KATEGORİ SİLME ----
    def delete_category():
        selected = cat_tree.selection()
        if not selected:
            messagebox.showwarning("Uyarı", "Lütfen silmek için bir kategori seçin!")
            return
        
        item = cat_tree.item(selected[0])
        cat_id = item['values'][0]
        cat_name = item['values'][1]
        post_count = item['values'][3]
        
        # Kategoriye ait yazı var mı kontrol et
        if post_count > 0:
            messagebox.showwarning("Uyarı", 
                f"'{cat_name}' kategorisine ait {post_count} yazı bulunmaktadır.\n\n"
                "Önce bu yazıları başka bir kategoriye taşıyın veya silin!")
            return
        
        confirm = messagebox.askyesno("Onay", 
            f"'{cat_name}' kategorisini silmek istediğinizden emin misiniz?\n\nBu işlem geri alınamaz!",
            icon='warning')
        
        if confirm:
            try:
                cursor.execute("DELETE FROM dbo.Categories WHERE categories_id = ?", (cat_id,))
                connection.commit()
                messagebox.showinfo("Başarılı", "Kategori başarıyla silindi!")
                load_categories()
            except Exception as e:
                messagebox.showerror("Hata", f"Kategori silinirken hata oluştu: {e}")
    
    # Butonlar
    btn_frame = tk.Frame(main, bg="#f0f0f0")
    btn_frame.pack(fill="x", pady=(10, 0))
    
    tk.Button(btn_frame, text="➕ Yeni Kategori", bg="#2ecc71", fg="white", 
              font=("Arial", 10), padx=15, pady=5, command=add_category).pack(side="left", padx=5)
    tk.Button(btn_frame, text="✏️ Düzenle", bg="#3498db", fg="white", 
              font=("Arial", 10), padx=15, pady=5, command=edit_category).pack(side="left", padx=5)
    tk.Button(btn_frame, text="🗑️ Sil", bg="#e74c3c", fg="white", 
              font=("Arial", 10), padx=15, pady=5, command=delete_category).pack(side="left", padx=5)
    tk.Button(btn_frame, text="🔄 Yenile", bg="#95a5a6", fg="white", 
              font=("Arial", 10), padx=15, pady=5, command=load_categories).pack(side="left", padx=5)

# ============================================
# ETİKET YÖNETİMİ (CRUD)
# ============================================

def open_tags_window():
    tags_win = tk.Toplevel(root)
    tags_win.title("Etiket Yönetimi")
    tags_win.geometry("700x500")
    tags_win.configure(bg="#f0f0f0")
    
    title_frame = tk.Frame(tags_win, bg="#f39c12", height=50)
    title_frame.pack(fill="x")
    tk.Label(title_frame, text="🔖 Etiket Yönetimi", font=("Arial", 16, "bold"), 
             bg="#f39c12", fg="white").pack(pady=10)
    
    main = tk.Frame(tags_win, bg="#f0f0f0", padx=20, pady=20)
    main.pack(fill="both", expand=True)
    
    # Etiket listesi
    list_frame = tk.LabelFrame(main, text="Tüm Etiketler", font=("Arial", 11, "bold"), 
                               bg="#f0f0f0", padx=10, pady=10)
    list_frame.pack(fill="both", expand=True)
    
    columns = ("ID", "Etiket Adı", "Kullanım Sayısı")
    tags_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=12)
    
    tags_tree.heading("ID", text="ID")
    tags_tree.heading("Etiket Adı", text="Etiket Adı")
    tags_tree.heading("Kullanım Sayısı", text="Kullanım Sayısı")
    
    tags_tree.column("ID", width=50)
    tags_tree.column("Etiket Adı", width=300)
    tags_tree.column("Kullanım Sayısı", width=150)
    
    scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=tags_tree.yview)
    tags_tree.configure(yscrollcommand=scrollbar.set)
    tags_tree.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")
    
    def load_tags():
        """Etiketleri yükle"""
        tags_tree.delete(*tags_tree.get_children())
        try:
            cursor.execute("""
                SELECT t.tags_id, t.tag_name, COUNT(pt.post_id) as UsageCount
                FROM dbo.Tags t
                LEFT JOIN dbo.Post_Tags pt ON t.tags_id = pt.tags_id
                GROUP BY t.tags_id, t.tag_name
                ORDER BY t.tag_name
            """)
            for tag in cursor.fetchall():
                tags_tree.insert("", "end", values=(tag[0], tag[1], tag[2]))
        except Exception as e:
            messagebox.showerror("Hata", f"Etiketler yüklenemedi: {e}")
    
    # İlk yükleme
    load_tags()
    
    # ---- ETİKET EKLEME ----
    def add_tag():
        add_win = tk.Toplevel(tags_win)
        add_win.title("Yeni Etiket Ekle")
        add_win.geometry("400x180")
        add_win.configure(bg="#f0f0f0")
        add_win.grab_set()
        
        # Başlık
        header = tk.Frame(add_win, bg="#2ecc71", height=40)
        header.pack(fill="x")
        tk.Label(header, text="➕ Yeni Etiket Ekle", font=("Arial", 14, "bold"),
                 bg="#2ecc71", fg="white").pack(pady=8)
        
        # Form
        form = tk.Frame(add_win, bg="#f0f0f0", padx=20, pady=20)
        form.pack(fill="both", expand=True)
        
        # Etiket adı
        tk.Label(form, text="Etiket Adı:", font=("Arial", 11), bg="#f0f0f0").pack(anchor="w")
        entry_name = tk.Entry(form, font=("Arial", 11), width=40)
        entry_name.pack(fill="x", pady=(0, 15))
        
        def save_tag():
            name = entry_name.get().strip()
            
            if not name:
                messagebox.showwarning("Uyarı", "Etiket adı boş bırakılamaz!", parent=add_win)
                return
            
            try:
                cursor.execute("INSERT INTO dbo.Tags (tag_name) VALUES (?)", (name,))
                connection.commit()
                messagebox.showinfo("Başarılı", "Etiket başarıyla eklendi!", parent=add_win)
                add_win.destroy()
                load_tags()
            except Exception as e:
                messagebox.showerror("Hata", f"Etiket eklenirken hata oluştu: {e}", parent=add_win)
        
        # Butonlar
        btn_frame = tk.Frame(form, bg="#f0f0f0")
        btn_frame.pack(fill="x", pady=(10, 0))
        
        tk.Button(btn_frame, text="💾 Kaydet", bg="#2ecc71", fg="white",
                  font=("Arial", 11), padx=20, pady=5, command=save_tag).pack(side="left", padx=5)
        tk.Button(btn_frame, text="❌ İptal", bg="#95a5a6", fg="white",
                  font=("Arial", 11), padx=20, pady=5, command=add_win.destroy).pack(side="left", padx=5)
    
    # ---- ETİKET DÜZENLEME ----
    def edit_tag():
        selected = tags_tree.selection()
        if not selected:
            messagebox.showwarning("Uyarı", "Lütfen düzenlemek için bir etiket seçin!")
            return
        
        item = tags_tree.item(selected[0])
        tag_id = item['values'][0]
        tag_name = item['values'][1]
        
        edit_win = tk.Toplevel(tags_win)
        edit_win.title("Etiket Düzenle")
        edit_win.geometry("400x180")
        edit_win.configure(bg="#f0f0f0")
        edit_win.grab_set()
        
        # Başlık
        header = tk.Frame(edit_win, bg="#3498db", height=40)
        header.pack(fill="x")
        tk.Label(header, text="✏️ Etiket Düzenle", font=("Arial", 14, "bold"),
                 bg="#3498db", fg="white").pack(pady=8)
        
        # Form
        form = tk.Frame(edit_win, bg="#f0f0f0", padx=20, pady=20)
        form.pack(fill="both", expand=True)
        
        # Etiket adı
        tk.Label(form, text="Etiket Adı:", font=("Arial", 11), bg="#f0f0f0").pack(anchor="w")
        entry_name = tk.Entry(form, font=("Arial", 11), width=40)
        entry_name.insert(0, tag_name)
        entry_name.pack(fill="x", pady=(0, 15))
        
        def update_tag():
            name = entry_name.get().strip()
            
            if not name:
                messagebox.showwarning("Uyarı", "Etiket adı boş bırakılamaz!", parent=edit_win)
                return
            
            try:
                cursor.execute("UPDATE dbo.Tags SET tag_name = ? WHERE tags_id = ?", (name, tag_id))
                connection.commit()
                messagebox.showinfo("Başarılı", "Etiket başarıyla güncellendi!", parent=edit_win)
                edit_win.destroy()
                load_tags()
            except Exception as e:
                messagebox.showerror("Hata", f"Etiket güncellenirken hata oluştu: {e}", parent=edit_win)
        
        # Butonlar
        btn_frame = tk.Frame(form, bg="#f0f0f0")
        btn_frame.pack(fill="x", pady=(10, 0))
        
        tk.Button(btn_frame, text="💾 Güncelle", bg="#3498db", fg="white",
                  font=("Arial", 11), padx=20, pady=5, command=update_tag).pack(side="left", padx=5)
        tk.Button(btn_frame, text="❌ İptal", bg="#95a5a6", fg="white",
                  font=("Arial", 11), padx=20, pady=5, command=edit_win.destroy).pack(side="left", padx=5)
    
    # ---- ETİKET SİLME ----
    def delete_tag():
        selected = tags_tree.selection()
        if not selected:
            messagebox.showwarning("Uyarı", "Lütfen silmek için bir etiket seçin!")
            return
        
        item = tags_tree.item(selected[0])
        tag_id = item['values'][0]
        tag_name = item['values'][1]
        usage_count = item['values'][2]
        
        if usage_count > 0:
            confirm = messagebox.askyesno("Onay", 
                f"'{tag_name}' etiketi {usage_count} yazıda kullanılıyor.\n\n"
                "Etiketi silmek, bu yazılardan da kaldırılmasına neden olacaktır.\n\n"
                "Devam etmek istiyor musunuz?",
                icon='warning')
        else:
            confirm = messagebox.askyesno("Onay", 
                f"'{tag_name}' etiketini silmek istediğinizden emin misiniz?\n\nBu işlem geri alınamaz!",
                icon='warning')
        
        if confirm:
            try:
                # Önce Post_Tags tablosundan ilişkileri sil
                cursor.execute("DELETE FROM dbo.Post_Tags WHERE tags_id = ?", (tag_id,))
                # Sonra etiketi sil
                cursor.execute("DELETE FROM dbo.Tags WHERE tags_id = ?", (tag_id,))
                connection.commit()
                messagebox.showinfo("Başarılı", "Etiket başarıyla silindi!")
                load_tags()
            except Exception as e:
                connection.rollback()
                messagebox.showerror("Hata", f"Etiket silinirken hata oluştu: {e}")
    
    # Butonlar
    btn_frame = tk.Frame(main, bg="#f0f0f0")
    btn_frame.pack(fill="x", pady=(10, 0))
    
    tk.Button(btn_frame, text="➕ Yeni Etiket", bg="#2ecc71", fg="white", 
              font=("Arial", 10), padx=15, pady=5, command=add_tag).pack(side="left", padx=5)
    tk.Button(btn_frame, text="✏️ Düzenle", bg="#3498db", fg="white", 
              font=("Arial", 10), padx=15, pady=5, command=edit_tag).pack(side="left", padx=5)
    tk.Button(btn_frame, text="🗑️ Sil", bg="#e74c3c", fg="white", 
              font=("Arial", 10), padx=15, pady=5, command=delete_tag).pack(side="left", padx=5)
    tk.Button(btn_frame, text="🔄 Yenile", bg="#95a5a6", fg="white", 
              font=("Arial", 10), padx=15, pady=5, command=load_tags).pack(side="left", padx=5)

# ============================================
# KULLANICI YÖNETİMİ (CRUD)
# ============================================

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
    
    # Arama çubuğu
    search_frame = tk.Frame(main, bg="#f0f0f0")
    search_frame.pack(fill="x", pady=(0, 10))
    
    tk.Label(search_frame, text="🔍 Ara:", font=("Arial", 11), bg="#f0f0f0").pack(side="left")
    search_var = tk.StringVar()
    search_entry = tk.Entry(search_frame, textvariable=search_var, font=("Arial", 11), width=30)
    search_entry.pack(side="left", padx=(5, 10))
    
    # Arama kriteri seçimi
    tk.Label(search_frame, text="Kriter:", font=("Arial", 10), bg="#f0f0f0").pack(side="left")
    search_criteria = tk.StringVar(value="Tümü")
    criteria_combo = ttk.Combobox(search_frame, textvariable=search_criteria, 
                                   values=["Tümü", "Ad", "Email", "Adres"], 
                                   state="readonly", width=10, font=("Arial", 10))
    criteria_combo.pack(side="left", padx=5)
    
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
    
    def load_users(search_text="", criteria="Tümü"):
        """Kullanıcıları yükle (arama destekli)"""
        users_tree.delete(*users_tree.get_children())
        try:
            if search_text:
                search_pattern = f"%{search_text}%"
                if criteria == "Ad":
                    cursor.execute("""
                        SELECT users_id, users_name, users_email, users_address
                        FROM dbo.Users
                        WHERE users_name LIKE ?
                        ORDER BY users_name
                    """, (search_pattern,))
                elif criteria == "Email":
                    cursor.execute("""
                        SELECT users_id, users_name, users_email, users_address
                        FROM dbo.Users
                        WHERE users_email LIKE ?
                        ORDER BY users_name
                    """, (search_pattern,))
                elif criteria == "Adres":
                    cursor.execute("""
                        SELECT users_id, users_name, users_email, users_address
                        FROM dbo.Users
                        WHERE users_address LIKE ?
                        ORDER BY users_name
                    """, (search_pattern,))
                else:  # Tümü
                    cursor.execute("""
                        SELECT users_id, users_name, users_email, users_address
                        FROM dbo.Users
                        WHERE users_name LIKE ? OR users_email LIKE ? OR users_address LIKE ?
                        ORDER BY users_name
                    """, (search_pattern, search_pattern, search_pattern))
            else:
                cursor.execute("""
                    SELECT users_id, users_name, users_email, users_address
                    FROM dbo.Users
                    ORDER BY users_name
                """)
            
            results = cursor.fetchall()
            for user in results:
                users_tree.insert("", "end", values=(
                    user[0],
                    user[1],
                    user[2],
                    user[3] if user[3] else "-"
                ))
            
            # Sonuç sayısını güncelle
            list_frame.config(text=f"Tüm Kullanıcılar ({len(results)} kayıt)")
            
        except Exception as e:
            messagebox.showerror("Hata", f"Kullanıcılar yüklenemedi: {e}")
    
    def do_search(*args):
        """Arama yap"""
        load_users(search_var.get().strip(), search_criteria.get())
    
    # Arama butonları ve event binding
    tk.Button(search_frame, text="Ara", bg="#3498db", fg="white",
              font=("Arial", 10), padx=10, command=do_search).pack(side="left", padx=5)
    tk.Button(search_frame, text="Temizle", bg="#95a5a6", fg="white",
              font=("Arial", 10), padx=10, 
              command=lambda: [search_var.set(""), load_users()]).pack(side="left", padx=5)
    
    # Enter tuşu ile arama
    search_entry.bind("<Return>", do_search)
    
    # İlk yükleme
    load_users()
    
    # ---- KULLANICI EKLEME ----
    def add_user():
        add_win = tk.Toplevel(users_win)
        add_win.title("Yeni Kullanıcı Ekle")
        add_win.geometry("450x300")
        add_win.configure(bg="#f0f0f0")
        add_win.grab_set()
        
        # Başlık
        header = tk.Frame(add_win, bg="#2ecc71", height=40)
        header.pack(fill="x")
        tk.Label(header, text="➕ Yeni Kullanıcı Ekle", font=("Arial", 14, "bold"),
                 bg="#2ecc71", fg="white").pack(pady=8)
        
        # Form
        form = tk.Frame(add_win, bg="#f0f0f0", padx=20, pady=20)
        form.pack(fill="both", expand=True)
        
        # Ad
        tk.Label(form, text="Kullanıcı Adı:", font=("Arial", 11), bg="#f0f0f0").pack(anchor="w")
        entry_name = tk.Entry(form, font=("Arial", 11), width=45)
        entry_name.pack(fill="x", pady=(0, 10))
        
        # Email
        tk.Label(form, text="Email:", font=("Arial", 11), bg="#f0f0f0").pack(anchor="w")
        entry_email = tk.Entry(form, font=("Arial", 11), width=45)
        entry_email.pack(fill="x", pady=(0, 10))
        
        # Adres
        tk.Label(form, text="Adres:", font=("Arial", 11), bg="#f0f0f0").pack(anchor="w")
        entry_address = tk.Entry(form, font=("Arial", 11), width=45)
        entry_address.pack(fill="x", pady=(0, 15))
        
        def save_user():
            name = entry_name.get().strip()
            email = entry_email.get().strip()
            address = entry_address.get().strip()
            
            if not name:
                messagebox.showwarning("Uyarı", "Kullanıcı adı boş bırakılamaz!", parent=add_win)
                return
            if not email:
                messagebox.showwarning("Uyarı", "Email boş bırakılamaz!", parent=add_win)
                return
            
            # Basit email validasyonu
            if "@" not in email or "." not in email:
                messagebox.showwarning("Uyarı", "Geçerli bir email adresi girin!", parent=add_win)
                return
            
            try:
                cursor.execute("""
                    INSERT INTO dbo.Users (users_name, users_email, users_address)
                    VALUES (?, ?, ?)
                """, (name, email, address if address else None))
                connection.commit()
                messagebox.showinfo("Başarılı", "Kullanıcı başarıyla eklendi!", parent=add_win)
                add_win.destroy()
                load_users()
            except Exception as e:
                messagebox.showerror("Hata", f"Kullanıcı eklenirken hata oluştu: {e}", parent=add_win)
        
        # Butonlar
        btn_frame = tk.Frame(form, bg="#f0f0f0")
        btn_frame.pack(fill="x", pady=(10, 0))
        
        tk.Button(btn_frame, text="💾 Kaydet", bg="#2ecc71", fg="white",
                  font=("Arial", 11), padx=20, pady=5, command=save_user).pack(side="left", padx=5)
        tk.Button(btn_frame, text="❌ İptal", bg="#95a5a6", fg="white",
                  font=("Arial", 11), padx=20, pady=5, command=add_win.destroy).pack(side="left", padx=5)
    
    # ---- KULLANICI DÜZENLEME ----
    def edit_user():
        selected = users_tree.selection()
        if not selected:
            messagebox.showwarning("Uyarı", "Lütfen düzenlemek için bir kullanıcı seçin!")
            return
        
        item = users_tree.item(selected[0])
        user_id = item['values'][0]
        
        # Mevcut veriyi getir
        try:
            cursor.execute("""
                SELECT users_id, users_name, users_email, users_address
                FROM dbo.Users WHERE users_id = ?
            """, (user_id,))
            user_data = cursor.fetchone()
            if not user_data:
                messagebox.showerror("Hata", "Kullanıcı bulunamadı!")
                return
        except Exception as e:
            messagebox.showerror("Hata", f"Veri alınamadı: {e}")
            return
        
        edit_win = tk.Toplevel(users_win)
        edit_win.title("Kullanıcı Düzenle")
        edit_win.geometry("450x300")
        edit_win.configure(bg="#f0f0f0")
        edit_win.grab_set()
        
        # Başlık
        header = tk.Frame(edit_win, bg="#3498db", height=40)
        header.pack(fill="x")
        tk.Label(header, text="✏️ Kullanıcı Düzenle", font=("Arial", 14, "bold"),
                 bg="#3498db", fg="white").pack(pady=8)
        
        # Form
        form = tk.Frame(edit_win, bg="#f0f0f0", padx=20, pady=20)
        form.pack(fill="both", expand=True)
        
        # Ad
        tk.Label(form, text="Kullanıcı Adı:", font=("Arial", 11), bg="#f0f0f0").pack(anchor="w")
        entry_name = tk.Entry(form, font=("Arial", 11), width=45)
        entry_name.insert(0, user_data[1] if user_data[1] else "")
        entry_name.pack(fill="x", pady=(0, 10))
        
        # Email
        tk.Label(form, text="Email:", font=("Arial", 11), bg="#f0f0f0").pack(anchor="w")
        entry_email = tk.Entry(form, font=("Arial", 11), width=45)
        entry_email.insert(0, user_data[2] if user_data[2] else "")
        entry_email.pack(fill="x", pady=(0, 10))
        
        # Adres
        tk.Label(form, text="Adres:", font=("Arial", 11), bg="#f0f0f0").pack(anchor="w")
        entry_address = tk.Entry(form, font=("Arial", 11), width=45)
        entry_address.insert(0, user_data[3] if user_data[3] else "")
        entry_address.pack(fill="x", pady=(0, 15))
        
        def update_user():
            name = entry_name.get().strip()
            email = entry_email.get().strip()
            address = entry_address.get().strip()
            
            if not name:
                messagebox.showwarning("Uyarı", "Kullanıcı adı boş bırakılamaz!", parent=edit_win)
                return
            if not email:
                messagebox.showwarning("Uyarı", "Email boş bırakılamaz!", parent=edit_win)
                return
            if "@" not in email or "." not in email:
                messagebox.showwarning("Uyarı", "Geçerli bir email adresi girin!", parent=edit_win)
                return
            
            try:
                cursor.execute("""
                    UPDATE dbo.Users 
                    SET users_name = ?, users_email = ?, users_address = ?
                    WHERE users_id = ?
                """, (name, email, address if address else None, user_id))
                connection.commit()
                messagebox.showinfo("Başarılı", "Kullanıcı başarıyla güncellendi!", parent=edit_win)
                edit_win.destroy()
                load_users()
            except Exception as e:
                messagebox.showerror("Hata", f"Kullanıcı güncellenirken hata oluştu: {e}", parent=edit_win)
        
        # Butonlar
        btn_frame = tk.Frame(form, bg="#f0f0f0")
        btn_frame.pack(fill="x", pady=(10, 0))
        
        tk.Button(btn_frame, text="💾 Güncelle", bg="#3498db", fg="white",
                  font=("Arial", 11), padx=20, pady=5, command=update_user).pack(side="left", padx=5)
        tk.Button(btn_frame, text="❌ İptal", bg="#95a5a6", fg="white",
                  font=("Arial", 11), padx=20, pady=5, command=edit_win.destroy).pack(side="left", padx=5)
    
    # ---- KULLANICI SİLME ----
    def delete_user():
        selected = users_tree.selection()
        if not selected:
            messagebox.showwarning("Uyarı", "Lütfen silmek için bir kullanıcı seçin!")
            return
        
        item = users_tree.item(selected[0])
        user_id = item['values'][0]
        user_name = item['values'][1]
        
        # Kullanıcıya ait yazı sayısını kontrol et
        try:
            cursor.execute("SELECT COUNT(*) FROM dbo.Post WHERE users_id = ?", (user_id,))
            post_count = cursor.fetchone()[0]
        except:
            post_count = 0
        
        # Eğer kullanıcının yazıları varsa silmeye izin verme
        if post_count > 0:
            messagebox.showwarning("Uyarı", 
                f"'{user_name}' kullanıcısına ait {post_count} yazı bulunmaktadır.\n\n"
                "Önce bu yazıları başka bir kullanıcıya atayın veya silin!")
            return
        
        # Kullanıcıya ait yorum sayısını kontrol et
        try:
            cursor.execute("SELECT COUNT(*) FROM dbo.Comments WHERE user_id = ?", (user_id,))
            comment_count = cursor.fetchone()[0]
        except:
            comment_count = 0
        
        # Onay mesajını yorum durumuna göre ayarla
        if comment_count > 0:
            confirm = messagebox.askyesno("Onay", 
                f"'{user_name}' kullanıcısını silmek istediğinizden emin misiniz?\n\n"
                f"⚠️ Bu kullanıcıya ait {comment_count} yorum da silinecektir!\n\n"
                "Bu işlem geri alınamaz!",
                icon='warning')
        else:
            confirm = messagebox.askyesno("Onay", 
                f"'{user_name}' kullanıcısını silmek istediğinizden emin misiniz?\n\nBu işlem geri alınamaz!",
                icon='warning')
        
        if confirm:
            try:
                # Önce kullanıcıya ait yorumları sil
                cursor.execute("DELETE FROM dbo.Comments WHERE user_id = ?", (user_id,))
                # Sonra kullanıcıyı sil
                cursor.execute("DELETE FROM dbo.Users WHERE users_id = ?", (user_id,))
                connection.commit()
                
                if comment_count > 0:
                    messagebox.showinfo("Başarılı", f"Kullanıcı ve {comment_count} yorum başarıyla silindi!")
                else:
                    messagebox.showinfo("Başarılı", "Kullanıcı başarıyla silindi!")
                load_users()
            except Exception as e:
                connection.rollback()
                messagebox.showerror("Hata", f"Kullanıcı silinirken hata oluştu: {e}")
    
    # Butonlar
    btn_frame = tk.Frame(main, bg="#f0f0f0")
    btn_frame.pack(fill="x", pady=(10, 0))
    
    tk.Button(btn_frame, text="➕ Yeni Kullanıcı", bg="#2ecc71", fg="white", 
              font=("Arial", 10), padx=15, pady=5, command=add_user).pack(side="left", padx=5)
    tk.Button(btn_frame, text="✏️ Düzenle", bg="#3498db", fg="white", 
              font=("Arial", 10), padx=15, pady=5, command=edit_user).pack(side="left", padx=5)
    tk.Button(btn_frame, text="🗑️ Sil", bg="#e74c3c", fg="white", 
              font=("Arial", 10), padx=15, pady=5, command=delete_user).pack(side="left", padx=5)
    tk.Button(btn_frame, text="🔄 Yenile", bg="#95a5a6", fg="white", 
              font=("Arial", 10), padx=15, pady=5, command=load_users).pack(side="left", padx=5)

# ============================================
# ANA PENCERE
# ============================================

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

btn_tags = tk.Button(button_frame, text="🔖 Etiketler", font=("Arial", 11), 
                     bg="#f39c12", fg="white", padx=20, pady=8, 
                     cursor="hand2", command=open_tags_window)
btn_tags.pack(side="left", padx=5)

btn_users = tk.Button(button_frame, text="👥 Kullanıcılar", font=("Arial", 11), 
                      bg="#9b59b6", fg="white", padx=20, pady=8, 
                      cursor="hand2", command=open_users_window)
btn_users.pack(side="left", padx=5)

root.mainloop()

connection.close()
