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
        text_content = tk.Text(form, font=("Arial", 10), height=6, width=50)
        text_content.pack(fill="both", expand=True, pady=(0, 10))
        
        # Yazar seçimi - arama destekli
        tk.Label(form, text="Yazar:", font=("Arial", 11), bg="#f0f0f0").pack(anchor="w")
        users = get_all_users()
        user_dict = {user[1]: user[0] for user in users}
        user_names = list(user_dict.keys())
        
        user_frame = tk.Frame(form, bg="#f0f0f0")
        user_frame.pack(fill="x", pady=(0, 5))
        
        selected_user_var = tk.StringVar(value="")
        user_entry = tk.Entry(user_frame, textvariable=selected_user_var, font=("Arial", 11), width=40)
        user_entry.pack(side="left", fill="x", expand=True)
        
        # Listbox yazar entry'nin hemen altında
        user_listbox_frame = tk.Frame(form, bg="#f0f0f0")
        user_listbox = tk.Listbox(user_listbox_frame, font=("Arial", 10), height=4, exportselection=False)
        user_scrollbar = ttk.Scrollbar(user_listbox_frame, orient="vertical", command=user_listbox.yview)
        user_listbox.configure(yscrollcommand=user_scrollbar.set)
        
        for name in user_names:
            user_listbox.insert(tk.END, name)
        
        def filter_users(*args):
            search = selected_user_var.get().lower()
            user_listbox.delete(0, tk.END)
            
            if search:
                # Önce başlayanlar, sonra içerenler
                starts_with = [name for name in user_names if name.lower().startswith(search)]
                contains = [name for name in user_names if search in name.lower() and not name.lower().startswith(search)]
                filtered = starts_with + contains
            else:
                filtered = user_names
            
            for name in filtered:
                user_listbox.insert(tk.END, name)
            
            if user_listbox.size() > 0 and search:
                user_listbox_frame.pack(fill="x", pady=(0, 5), before=category_label)
                user_listbox.pack(side="left", fill="both", expand=True)
                user_scrollbar.pack(side="right", fill="y")
            else:
                user_listbox_frame.pack_forget()
        
        def select_user(event):
            if user_listbox.curselection():
                selected_user_var.set(user_listbox.get(user_listbox.curselection()))
                user_listbox_frame.pack_forget()
        
        selected_user_var.trace("w", filter_users)
        user_listbox.bind("<<ListboxSelect>>", select_user)
        user_listbox.bind("<Double-1>", select_user)
        
        # Kategori seçimi
        category_label = tk.Label(form, text="Kategori:", font=("Arial", 11), bg="#f0f0f0")
        category_label.pack(anchor="w")
        categories = get_all_categories()
        category_names = [cat[1] for cat in categories]
        category_var = tk.StringVar()
        combo_category = ttk.Combobox(form, textvariable=category_var, values=category_names, 
                                       state="readonly", font=("Arial", 11))
        combo_category.pack(fill="x", pady=(0, 15))
        
        def save_post():
            title = entry_title.get().strip()
            content = text_content.get("1.0", tk.END).strip()
            selected_user = selected_user_var.get().strip()
            selected_category = category_var.get().strip()
            
            # Validasyon
            if not title:
                messagebox.showwarning("Uyarı", "Başlık boş bırakılamaz!", parent=add_win)
                return
            if not content:
                messagebox.showwarning("Uyarı", "İçerik boş bırakılamaz!", parent=add_win)
                return
            if not selected_user or selected_user not in user_names:
                messagebox.showwarning("Uyarı", "Lütfen listeden bir yazar seçin!", parent=add_win)
                return
            if not selected_category or selected_category not in category_names:
                messagebox.showwarning("Uyarı", "Lütfen listeden bir kategori seçin!", parent=add_win)
                return
            
            # ID'leri bul
            user_id = user_dict.get(selected_user)
            
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
        edit_win.geometry("500x580")
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
        text_content = tk.Text(form, font=("Arial", 10), height=6, width=50)
        text_content.insert("1.0", post_data[2] if post_data[2] else "")
        text_content.pack(fill="both", expand=True, pady=(0, 10))
        
        # Yazar seçimi - arama destekli
        tk.Label(form, text="Yazar:", font=("Arial", 11), bg="#f0f0f0").pack(anchor="w")
        users = get_all_users()
        user_dict = {user[1]: user[0] for user in users}
        user_names = list(user_dict.keys())
        
        # Mevcut yazarı bul
        current_user = ""
        for user in users:
            if user[0] == post_data[4]:
                current_user = user[1]
                break
        
        user_frame = tk.Frame(form, bg="#f0f0f0")
        user_frame.pack(fill="x", pady=(0, 5))
        
        selected_user_var = tk.StringVar(value=current_user)
        user_entry = tk.Entry(user_frame, textvariable=selected_user_var, font=("Arial", 11), width=40)
        user_entry.pack(side="left", fill="x", expand=True)
        
        # Listbox yazar entry'nin hemen altında
        user_listbox_frame = tk.Frame(form, bg="#f0f0f0")
        user_listbox = tk.Listbox(user_listbox_frame, font=("Arial", 10), height=4, exportselection=False)
        user_scrollbar = ttk.Scrollbar(user_listbox_frame, orient="vertical", command=user_listbox.yview)
        user_listbox.configure(yscrollcommand=user_scrollbar.set)
        
        for name in user_names:
            user_listbox.insert(tk.END, name)
        
        def filter_users(*args):
            search = selected_user_var.get().lower()
            user_listbox.delete(0, tk.END)
            
            if search:
                # Önce başlayanlar, sonra içerenler
                starts_with = [name for name in user_names if name.lower().startswith(search)]
                contains = [name for name in user_names if search in name.lower() and not name.lower().startswith(search)]
                filtered = starts_with + contains
            else:
                filtered = user_names
            
            for name in filtered:
                user_listbox.insert(tk.END, name)
            
            # Sadece arama yaparken ve mevcut değerden farklıysa göster
            if user_listbox.size() > 0 and search and search != current_user.lower():
                user_listbox_frame.pack(fill="x", pady=(0, 5), before=category_label)
                user_listbox.pack(side="left", fill="both", expand=True)
                user_scrollbar.pack(side="right", fill="y")
            else:
                user_listbox_frame.pack_forget()
        
        def select_user(event):
            if user_listbox.curselection():
                selected_user_var.set(user_listbox.get(user_listbox.curselection()))
                user_listbox_frame.pack_forget()
        
        selected_user_var.trace("w", filter_users)
        user_listbox.bind("<<ListboxSelect>>", select_user)
        user_listbox.bind("<Double-1>", select_user)
        
        # Kategori seçimi
        category_label = tk.Label(form, text="Kategori:", font=("Arial", 11), bg="#f0f0f0")
        category_label.pack(anchor="w")
        categories = get_all_categories()
        category_names = [cat[1] for cat in categories]
        
        # Mevcut kategoriyi bul
        current_category = ""
        for cat in categories:
            if cat[0] == post_data[3]:
                current_category = cat[1]
                break
        
        category_var = tk.StringVar(value=current_category if current_category else "")
        combo_category = ttk.Combobox(form, textvariable=category_var, values=category_names, 
                                       state="readonly", font=("Arial", 11))
        combo_category.pack(fill="x", pady=(0, 15))
        
        def update_post():
            title = entry_title.get().strip()
            content = text_content.get("1.0", tk.END).strip()
            selected_user = selected_user_var.get().strip()
            selected_category = category_var.get().strip()
            
            if not title:
                messagebox.showwarning("Uyarı", "Başlık boş bırakılamaz!", parent=edit_win)
                return
            
            if not selected_user or selected_user not in user_names:
                messagebox.showwarning("Uyarı", "Lütfen listeden bir yazar seçin!", parent=edit_win)
                return
            
            if not selected_category or selected_category not in category_names:
                messagebox.showwarning("Uyarı", "Lütfen listeden bir kategori seçin!", parent=edit_win)
                return
            
            # ID'leri bul
            user_id = user_dict.get(selected_user)
            
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
# YORUM YÖNETİMİ (CRUD)
# ============================================

def open_comments_window():
    comments_win = tk.Toplevel(root)
    comments_win.title("Yorum Yönetimi")
    comments_win.geometry("1000x600")
    comments_win.configure(bg="#f0f0f0")
    
    title_frame = tk.Frame(comments_win, bg="#1abc9c", height=50)
    title_frame.pack(fill="x")
    tk.Label(title_frame, text="💬 Yorum Yönetimi", font=("Arial", 16, "bold"), 
             bg="#1abc9c", fg="white").pack(pady=10)
    
    main = tk.Frame(comments_win, bg="#f0f0f0", padx=20, pady=20)
    main.pack(fill="both", expand=True)
    
    # Filtre çubuğu
    filter_frame = tk.Frame(main, bg="#f0f0f0")
    filter_frame.pack(fill="x", pady=(0, 10))
    
    tk.Label(filter_frame, text="📝 Yazıya Göre Filtrele:", font=("Arial", 10), bg="#f0f0f0").pack(side="left")
    
    # Yazı listesini getir
    posts_list = []
    try:
        cursor.execute("SELECT post_id, post_title FROM dbo.Post ORDER BY post_title")
        posts_list = cursor.fetchall()
    except:
        pass
    
    post_names = ["Tüm Yorumlar"] + [f"{p[0]} - {p[1][:40]}..." if len(p[1]) > 40 else f"{p[0]} - {p[1]}" for p in posts_list]
    filter_var = tk.StringVar(value="Tüm Yorumlar")
    filter_combo = ttk.Combobox(filter_frame, textvariable=filter_var, values=post_names, 
                                 state="readonly", width=50, font=("Arial", 10))
    filter_combo.pack(side="left", padx=(5, 10))
    
    # Yorum listesi
    list_frame = tk.LabelFrame(main, text="Tüm Yorumlar", font=("Arial", 11, "bold"), 
                               bg="#f0f0f0", padx=10, pady=10)
    list_frame.pack(fill="both", expand=True)
    
    columns = ("ID", "Yazı", "Kullanıcı", "Yorum", "Tarih")
    comments_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=15)
    
    comments_tree.heading("ID", text="ID")
    comments_tree.heading("Yazı", text="Yazı Başlığı")
    comments_tree.heading("Kullanıcı", text="Kullanıcı")
    comments_tree.heading("Yorum", text="Yorum İçeriği")
    comments_tree.heading("Tarih", text="Tarih")
    
    comments_tree.column("ID", width=50)
    comments_tree.column("Yazı", width=200)
    comments_tree.column("Kullanıcı", width=120)
    comments_tree.column("Yorum", width=350)
    comments_tree.column("Tarih", width=100)
    
    scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=comments_tree.yview)
    comments_tree.configure(yscrollcommand=scrollbar.set)
    comments_tree.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")
    
    def load_comments(post_filter=None):
        """Yorumları yükle"""
        comments_tree.delete(*comments_tree.get_children())
        try:
            if post_filter and post_filter != "Tüm Yorumlar":
                # Post ID'yi çıkar
                post_id = int(post_filter.split(" - ")[0])
                cursor.execute("""
                    SELECT c.comment_id, p.post_title, u.users_name, c.comment_content, c.comment_date
                    FROM dbo.Comments c
                    LEFT JOIN dbo.Post p ON c.post_id = p.post_id
                    LEFT JOIN dbo.Users u ON c.user_id = u.users_id
                    WHERE c.post_id = ?
                    ORDER BY c.comment_date DESC
                """, (post_id,))
            else:
                cursor.execute("""
                    SELECT c.comment_id, p.post_title, u.users_name, c.comment_content, c.comment_date
                    FROM dbo.Comments c
                    LEFT JOIN dbo.Post p ON c.post_id = p.post_id
                    LEFT JOIN dbo.Users u ON c.user_id = u.users_id
                    ORDER BY c.comment_date DESC
                """)
            
            results = cursor.fetchall()
            for comment in results:
                comment_text = comment[3][:50] + "..." if comment[3] and len(comment[3]) > 50 else comment[3]
                comments_tree.insert("", "end", values=(
                    comment[0],
                    comment[1][:30] + "..." if comment[1] and len(comment[1]) > 30 else comment[1] or "Silinmiş Yazı",
                    comment[2] if comment[2] else "Anonim",
                    comment_text if comment_text else "-",
                    comment[4].strftime("%d/%m/%Y") if comment[4] else "-"
                ))
            
            list_frame.config(text=f"Yorumlar ({len(results)} kayıt)")
            
        except Exception as e:
            messagebox.showerror("Hata", f"Yorumlar yüklenemedi: {e}")
    
    def on_filter_change(event):
        load_comments(filter_var.get())
    
    filter_combo.bind("<<ComboboxSelected>>", on_filter_change)
    
    # Filtre butonu
    tk.Button(filter_frame, text="🔍 Filtrele", bg="#3498db", fg="white",
              font=("Arial", 10), padx=10, command=lambda: load_comments(filter_var.get())).pack(side="left", padx=5)
    tk.Button(filter_frame, text="🔄 Tümünü Göster", bg="#95a5a6", fg="white",
              font=("Arial", 10), padx=10, 
              command=lambda: [filter_var.set("Tüm Yorumlar"), load_comments()]).pack(side="left", padx=5)
    
    # İlk yükleme
    load_comments()
    
    # ---- YORUM DETAY GÖRÜNTÜLEME (Çift Tıklama) ----
    def show_comment_detail(event):
        selected = comments_tree.selection()
        if not selected:
            return
        
        item = comments_tree.item(selected[0])
        comment_id = item['values'][0]
        
        # Yorum detaylarını getir
        try:
            cursor.execute("""
                SELECT c.comment_id, c.comment_content, c.comment_date,
                       p.post_title, u.users_name
                FROM dbo.Comments c
                LEFT JOIN dbo.Post p ON c.post_id = p.post_id
                LEFT JOIN dbo.Users u ON c.user_id = u.users_id
                WHERE c.comment_id = ?
            """, (comment_id,))
            comment_data = cursor.fetchone()
            if not comment_data:
                messagebox.showerror("Hata", "Yorum bulunamadı!")
                return
        except Exception as e:
            messagebox.showerror("Hata", f"Veri alınamadı: {e}")
            return
        
        # Detay penceresi
        detail_win = tk.Toplevel(comments_win)
        detail_win.title("Yorum Detayı")
        detail_win.geometry("500x400")
        detail_win.configure(bg="#f0f0f0")
        
        # Başlık
        header = tk.Frame(detail_win, bg="#1abc9c", height=40)
        header.pack(fill="x")
        tk.Label(header, text="💬 Yorum Detayı", font=("Arial", 14, "bold"),
                 bg="#1abc9c", fg="white").pack(pady=8)
        
        # İçerik
        content_frame = tk.Frame(detail_win, bg="#f0f0f0", padx=20, pady=20)
        content_frame.pack(fill="both", expand=True)
        
        # Bilgi kartı
        info_card = tk.LabelFrame(content_frame, text="Yorum Bilgileri", font=("Arial", 10, "bold"),
                                   bg="white", padx=15, pady=10)
        info_card.pack(fill="x", pady=(0, 15))
        
        # Yazı
        tk.Label(info_card, text="Yazı:", font=("Arial", 10, "bold"), bg="white").grid(row=0, column=0, sticky="w", pady=2)
        tk.Label(info_card, text=comment_data[3] if comment_data[3] else "Silinmiş Yazı", 
                 font=("Arial", 10), bg="white", wraplength=350, justify="left").grid(row=0, column=1, sticky="w", padx=(10,0), pady=2)
        
        # Kullanıcı
        tk.Label(info_card, text="Yazan:", font=("Arial", 10, "bold"), bg="white").grid(row=1, column=0, sticky="w", pady=2)
        tk.Label(info_card, text=comment_data[4] if comment_data[4] else "Anonim", 
                 font=("Arial", 10), bg="white").grid(row=1, column=1, sticky="w", padx=(10,0), pady=2)
        
        # Tarih
        tk.Label(info_card, text="Tarih:", font=("Arial", 10, "bold"), bg="white").grid(row=2, column=0, sticky="w", pady=2)
        date_str = comment_data[2].strftime("%d/%m/%Y %H:%M") if comment_data[2] else "-"
        tk.Label(info_card, text=date_str, font=("Arial", 10), bg="white").grid(row=2, column=1, sticky="w", padx=(10,0), pady=2)
        
        # Yorum içeriği
        content_card = tk.LabelFrame(content_frame, text="Yorum İçeriği", font=("Arial", 10, "bold"),
                                      bg="white", padx=10, pady=10)
        content_card.pack(fill="both", expand=True)
        
        content_text = tk.Text(content_card, font=("Arial", 10), wrap="word", height=8)
        content_text.insert("1.0", comment_data[1] if comment_data[1] else "İçerik yok")
        content_text.config(state="disabled")
        
        content_scroll = ttk.Scrollbar(content_card, orient="vertical", command=content_text.yview)
        content_text.configure(yscrollcommand=content_scroll.set)
        content_text.pack(side="left", fill="both", expand=True)
        content_scroll.pack(side="right", fill="y")
        
        # Kapat butonu
        tk.Button(content_frame, text="❌ Kapat", bg="#95a5a6", fg="white",
                  font=("Arial", 11), padx=20, pady=5, command=detail_win.destroy).pack(pady=(15, 0))
    
    # Çift tıklama event'i bağla
    comments_tree.bind("<Double-1>", show_comment_detail)
    
    # ---- YORUM EKLEME ----
    def add_comment():
        add_win = tk.Toplevel(comments_win)
        add_win.title("Yeni Yorum Ekle")
        add_win.geometry("500x400")
        add_win.configure(bg="#f0f0f0")
        add_win.grab_set()
        
        # Başlık
        header = tk.Frame(add_win, bg="#2ecc71", height=40)
        header.pack(fill="x")
        tk.Label(header, text="➕ Yeni Yorum Ekle", font=("Arial", 14, "bold"),
                 bg="#2ecc71", fg="white").pack(pady=8)
        
        # Form
        form = tk.Frame(add_win, bg="#f0f0f0", padx=20, pady=20)
        form.pack(fill="both", expand=True)
        
        # Yazı seçimi
        tk.Label(form, text="Yazı:", font=("Arial", 11), bg="#f0f0f0").pack(anchor="w")
        posts = []
        try:
            cursor.execute("SELECT post_id, post_title FROM dbo.Post ORDER BY post_title")
            posts = cursor.fetchall()
        except:
            pass
        post_names = ["Yazı Seçin..."] + [f"{p[0]} - {p[1][:40]}..." if len(p[1]) > 40 else f"{p[0]} - {p[1]}" for p in posts]
        post_var = tk.StringVar(value="Yazı Seçin...")
        combo_post = ttk.Combobox(form, textvariable=post_var, values=post_names, 
                                   state="readonly", font=("Arial", 10), width=55)
        combo_post.pack(fill="x", pady=(0, 10))
        
        # Kullanıcı seçimi
        tk.Label(form, text="Kullanıcı:", font=("Arial", 11), bg="#f0f0f0").pack(anchor="w")
        users = get_all_users()
        user_names = ["Kullanıcı Seçin..."] + [user[1] for user in users]
        user_var = tk.StringVar(value="Kullanıcı Seçin...")
        combo_user = ttk.Combobox(form, textvariable=user_var, values=user_names, 
                                   state="readonly", font=("Arial", 10), width=55)
        combo_user.pack(fill="x", pady=(0, 10))
        
        # Yorum içeriği
        tk.Label(form, text="Yorum:", font=("Arial", 11), bg="#f0f0f0").pack(anchor="w")
        text_content = tk.Text(form, font=("Arial", 10), height=8, width=55)
        text_content.pack(fill="both", expand=True, pady=(0, 10))
        
        def save_comment():
            selected_post = post_var.get()
            selected_user = user_var.get()
            content = text_content.get("1.0", tk.END).strip()
            
            if selected_post == "Yazı Seçin...":
                messagebox.showwarning("Uyarı", "Lütfen bir yazı seçin!", parent=add_win)
                return
            if selected_user == "Kullanıcı Seçin...":
                messagebox.showwarning("Uyarı", "Lütfen bir kullanıcı seçin!", parent=add_win)
                return
            if not content:
                messagebox.showwarning("Uyarı", "Yorum içeriği boş bırakılamaz!", parent=add_win)
                return
            
            # ID'leri bul
            post_id = int(selected_post.split(" - ")[0])
            
            user_id = None
            for user in users:
                if user[1] == selected_user:
                    user_id = user[0]
                    break
            
            try:
                cursor.execute("""
                    INSERT INTO dbo.Comments (post_id, user_id, comment_content, comment_date)
                    VALUES (?, ?, ?, ?)
                """, (post_id, user_id, content, datetime.now()))
                connection.commit()
                messagebox.showinfo("Başarılı", "Yorum başarıyla eklendi!", parent=add_win)
                add_win.destroy()
                load_comments(filter_var.get())
            except Exception as e:
                messagebox.showerror("Hata", f"Yorum eklenirken hata oluştu: {e}", parent=add_win)
        
        # Butonlar
        btn_frame = tk.Frame(form, bg="#f0f0f0")
        btn_frame.pack(fill="x", pady=(10, 0))
        
        tk.Button(btn_frame, text="💾 Kaydet", bg="#2ecc71", fg="white",
                  font=("Arial", 11), padx=20, pady=5, command=save_comment).pack(side="left", padx=5)
        tk.Button(btn_frame, text="❌ İptal", bg="#95a5a6", fg="white",
                  font=("Arial", 11), padx=20, pady=5, command=add_win.destroy).pack(side="left", padx=5)
    
    # ---- YORUM SİLME ----
    def delete_comment():
        selected = comments_tree.selection()
        if not selected:
            messagebox.showwarning("Uyarı", "Lütfen silmek için bir yorum seçin!")
            return
        
        item = comments_tree.item(selected[0])
        comment_id = item['values'][0]
        comment_preview = item['values'][3]
        
        confirm = messagebox.askyesno("Onay", 
            f"Bu yorumu silmek istediğinizden emin misiniz?\n\n"
            f"Yorum: \"{comment_preview}\"\n\n"
            "Bu işlem geri alınamaz!",
            icon='warning')
        
        if confirm:
            try:
                cursor.execute("DELETE FROM dbo.Comments WHERE comment_id = ?", (comment_id,))
                connection.commit()
                messagebox.showinfo("Başarılı", "Yorum başarıyla silindi!")
                load_comments(filter_var.get())
            except Exception as e:
                messagebox.showerror("Hata", f"Yorum silinirken hata oluştu: {e}")
    
    # Butonlar
    btn_frame = tk.Frame(main, bg="#f0f0f0")
    btn_frame.pack(fill="x", pady=(10, 0))
    
    tk.Button(btn_frame, text="➕ Yeni Yorum", bg="#2ecc71", fg="white", 
              font=("Arial", 10), padx=15, pady=5, command=add_comment).pack(side="left", padx=5)
    tk.Button(btn_frame, text="🗑️ Sil", bg="#e74c3c", fg="white", 
              font=("Arial", 10), padx=15, pady=5, command=delete_comment).pack(side="left", padx=5)
    tk.Button(btn_frame, text="🔄 Yenile", bg="#95a5a6", fg="white", 
              font=("Arial", 10), padx=15, pady=5, command=lambda: load_comments(filter_var.get())).pack(side="left", padx=5)

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
        add_win.geometry("450x350")
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
        
        # Şifre
        tk.Label(form, text="Şifre:", font=("Arial", 11), bg="#f0f0f0").pack(anchor="w")
        entry_password = tk.Entry(form, font=("Arial", 11), width=45, show="*")
        entry_password.pack(fill="x", pady=(0, 10))
        
        # Adres
        tk.Label(form, text="Adres:", font=("Arial", 11), bg="#f0f0f0").pack(anchor="w")
        entry_address = tk.Entry(form, font=("Arial", 11), width=45)
        entry_address.pack(fill="x", pady=(0, 15))
        
        def save_user():
            name = entry_name.get().strip()
            email = entry_email.get().strip()
            password = entry_password.get().strip()
            address = entry_address.get().strip()
            
            if not name:
                messagebox.showwarning("Uyarı", "Kullanıcı adı boş bırakılamaz!", parent=add_win)
                return
            if not email:
                messagebox.showwarning("Uyarı", "Email boş bırakılamaz!", parent=add_win)
                return
            if not password:
                messagebox.showwarning("Uyarı", "Şifre boş bırakılamaz!", parent=add_win)
                return
            
            # Basit email validasyonu
            if "@" not in email or "." not in email:
                messagebox.showwarning("Uyarı", "Geçerli bir email adresi girin!", parent=add_win)
                return
            
            try:
                cursor.execute("""
                    INSERT INTO dbo.Users (users_name, users_email, users_password, users_address)
                    VALUES (?, ?, ?, ?)
                """, (name, email, password, address if address else None))
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
                SELECT users_id, users_name, users_email, users_password, users_address
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
        edit_win.geometry("450x380")
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
        
        # Şifre
        tk.Label(form, text="Şifre (değiştirmek için yeni şifre girin):", font=("Arial", 11), bg="#f0f0f0").pack(anchor="w")
        entry_password = tk.Entry(form, font=("Arial", 11), width=45, show="*")
        entry_password.insert(0, user_data[3] if user_data[3] else "")
        entry_password.pack(fill="x", pady=(0, 10))
        
        # Adres
        tk.Label(form, text="Adres:", font=("Arial", 11), bg="#f0f0f0").pack(anchor="w")
        entry_address = tk.Entry(form, font=("Arial", 11), width=45)
        entry_address.insert(0, user_data[4] if user_data[4] else "")
        entry_address.pack(fill="x", pady=(0, 15))
        
        def update_user():
            name = entry_name.get().strip()
            email = entry_email.get().strip()
            password = entry_password.get().strip()
            address = entry_address.get().strip()
            
            if not name:
                messagebox.showwarning("Uyarı", "Kullanıcı adı boş bırakılamaz!", parent=edit_win)
                return
            if not email:
                messagebox.showwarning("Uyarı", "Email boş bırakılamaz!", parent=edit_win)
                return
            if not password:
                messagebox.showwarning("Uyarı", "Şifre boş bırakılamaz!", parent=edit_win)
                return
            if "@" not in email or "." not in email:
                messagebox.showwarning("Uyarı", "Geçerli bir email adresi girin!", parent=edit_win)
                return
            
            try:
                cursor.execute("""
                    UPDATE dbo.Users 
                    SET users_name = ?, users_email = ?, users_password = ?, users_address = ?
                    WHERE users_id = ?
                """, (name, email, password, address if address else None, user_id))
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

btn_comments = tk.Button(button_frame, text="💬 Yorumlar", font=("Arial", 11), 
                         bg="#1abc9c", fg="white", padx=20, pady=8, 
                         cursor="hand2", command=open_comments_window)
btn_comments.pack(side="left", padx=5)

btn_users = tk.Button(button_frame, text="👥 Kullanıcılar", font=("Arial", 11), 
                      bg="#9b59b6", fg="white", padx=20, pady=8, 
                      cursor="hand2", command=open_users_window)
btn_users.pack(side="left", padx=5)

root.mainloop()

connection.close()