from flask import Flask, render_template, request, redirect, url_for, flash, session
import pyodbc
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

app = Flask(__name__)
app.secret_key = 'bloggerdev-secret-key-2025'

# ============================================
# VERİTABANI BAĞLANTISI
# ============================================

def get_db():
    """Veritabanı bağlantısı oluşturur"""
    return pyodbc.connect(
        'DRIVER={ODBC Driver 17 for SQL Server};'
        'SERVER=SORA\\SQLEXPRESS;'
        'DATABASE=BloggerDev;'
        'Trusted_Connection=yes;'
    )

def rows_to_dicts(cursor, rows):
    """pyodbc Row nesnelerini dict listesine çevirir"""
    if rows is None:
        return []
    columns = [column[0] for column in cursor.description]
    if isinstance(rows, list):
        return [dict(zip(columns, row)) for row in rows]
    else:
        return dict(zip(columns, rows))

# ============================================
# GİRİŞ GEREKTİREN SAYFALAR İÇİN DECORATOR
# ============================================

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Bu sayfayı görüntülemek için giriş yapmalısınız.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# ============================================
# CONTEXT PROCESSOR - Tüm sayfalarda kullanıcı bilgisi
# ============================================

@app.context_processor
def inject_user():
    """Tüm template'lerde current_user ve categories erişilebilir olsun"""
    current_user = None
    categories = []
    
    if 'user_id' in session:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT users_id, users_name, users_email FROM dbo.Users WHERE users_id = ?", (session['user_id'],))
        row = cursor.fetchone()
        if row:
            current_user = rows_to_dicts(cursor, row)
        conn.close()
    
    # Kategorileri her sayfada göster
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT c.categories_id, c.categories_name, COUNT(p.post_id) as post_count
        FROM dbo.Categories c
        LEFT JOIN dbo.Post p ON c.categories_id = p.categories_id
        GROUP BY c.categories_id, c.categories_name
        ORDER BY c.categories_name
    """)
    categories = rows_to_dicts(cursor, cursor.fetchall())
    conn.close()
    
    return dict(current_user=current_user, categories=categories)

# ============================================
# ANA SAYFA
# ============================================

@app.route('/')
def index():
    """Ana sayfa - Son yazıları listeler"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Son 10 yazıyı getir
    cursor.execute("""
        SELECT p.post_id, p.post_title, p.post_content, p.post_date,
               u.users_name, c.categories_name
        FROM dbo.Post p
        LEFT JOIN dbo.Users u ON p.users_id = u.users_id
        LEFT JOIN dbo.Categories c ON p.categories_id = c.categories_id
        ORDER BY p.post_date DESC
    """)
    posts = rows_to_dicts(cursor, cursor.fetchall())
    
    conn.close()
    return render_template('index.html', posts=posts)

# ============================================
# GİRİŞ / KAYIT / ÇIKIŞ
# ============================================

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Giriş sayfası"""
    if 'user_id' in session:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        
        if not email or not password:
            flash('Email ve şifre gereklidir.', 'error')
            return render_template('login.html')
        
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT users_id, users_name, users_email, users_password FROM dbo.Users WHERE users_email = ?", (email,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            user = rows_to_dicts(cursor, row)
            # Şifre kontrolü (hashli veya düz metin)
            if user['users_password'] == password or (user['users_password'].startswith('pbkdf2:') and check_password_hash(user['users_password'], password)):
                session['user_id'] = user['users_id']
                session['user_name'] = user['users_name']
                flash(f'Hoş geldiniz, {user["users_name"]}!', 'success')
                return redirect(url_for('index'))
        
        flash('Email veya şifre hatalı.', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Kayıt sayfası"""
    if 'user_id' in session:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        password_confirm = request.form.get('password_confirm', '').strip()
        
        # Validasyonlar
        if not name or not email or not password:
            flash('Tüm alanları doldurunuz.', 'error')
            return render_template('register.html')
        
        if password != password_confirm:
            flash('Şifreler eşleşmiyor.', 'error')
            return render_template('register.html')
        
        if len(password) < 6:
            flash('Şifre en az 6 karakter olmalıdır.', 'error')
            return render_template('register.html')
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Email kontrolü
        cursor.execute("SELECT users_id FROM dbo.Users WHERE users_email = ?", (email,))
        if cursor.fetchone():
            conn.close()
            flash('Bu email adresi zaten kayıtlı.', 'error')
            return render_template('register.html')
        
        # Şifreyi hashle ve kullanıcıyı kaydet
        hashed_password = generate_password_hash(password)
        cursor.execute("""
            INSERT INTO dbo.Users (users_name, users_email, users_password, role_id)
            VALUES (?, ?, ?, 2)
        """, (name, email, hashed_password))
        conn.commit()
        
        # Yeni kullanıcının ID'sini al
        cursor.execute("SELECT users_id FROM dbo.Users WHERE users_email = ?", (email,))
        new_user = cursor.fetchone()
        conn.close()
        
        if new_user:
            session['user_id'] = new_user[0]
            session['user_name'] = name
            flash('Kayıt başarılı! Hoş geldiniz.', 'success')
            return redirect(url_for('index'))
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    """Çıkış yap"""
    session.clear()
    flash('Başarıyla çıkış yaptınız.', 'success')
    return redirect(url_for('index'))

# ============================================
# PROFİL SAYFASI
# ============================================

@app.route('/profile')
@login_required
def profile():
    """Kullanıcı profil sayfası"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Kullanıcı bilgileri
    cursor.execute("SELECT users_id, users_name, users_email, users_address FROM dbo.Users WHERE users_id = ?", (session['user_id'],))
    user = rows_to_dicts(cursor, cursor.fetchone())
    
    # Kullanıcının yazıları
    cursor.execute("""
        SELECT p.post_id, p.post_title, p.post_content, p.post_date, c.categories_name
        FROM dbo.Post p
        LEFT JOIN dbo.Categories c ON p.categories_id = c.categories_id
        WHERE p.users_id = ?
        ORDER BY p.post_date DESC
    """, (session['user_id'],))
    posts = rows_to_dicts(cursor, cursor.fetchall())
    
    # Takipçi sayısı
    cursor.execute("SELECT COUNT(*) FROM dbo.User_Follows WHERE following_id = ?", (session['user_id'],))
    followers_count = cursor.fetchone()[0]
    
    # Takip edilen sayısı
    cursor.execute("SELECT COUNT(*) FROM dbo.User_Follows WHERE follower_id = ?", (session['user_id'],))
    following_count = cursor.fetchone()[0]
    
    # Takip edilenler listesi
    cursor.execute("""
        SELECT u.users_id, u.users_name, u.users_email
        FROM dbo.Users u
        INNER JOIN dbo.User_Follows f ON u.users_id = f.following_id
        WHERE f.follower_id = ?
        ORDER BY f.follow_date DESC
    """, (session['user_id'],))
    following = rows_to_dicts(cursor, cursor.fetchall())
    
    conn.close()
    return render_template('profile.html', user=user, posts=posts, 
                          followers_count=followers_count, following_count=following_count,
                          following=following)

@app.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """Profil düzenleme"""
    conn = get_db()
    cursor = conn.cursor()
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        address = request.form.get('address', '').strip()
        
        if name:
            cursor.execute("""
                UPDATE dbo.Users SET users_name = ?, users_address = ? WHERE users_id = ?
            """, (name, address, session['user_id']))
            conn.commit()
            session['user_name'] = name
            flash('Profil güncellendi.', 'success')
        
        conn.close()
        return redirect(url_for('profile'))
    
    cursor.execute("SELECT users_id, users_name, users_email, users_address FROM dbo.Users WHERE users_id = ?", (session['user_id'],))
    user = rows_to_dicts(cursor, cursor.fetchone())
    conn.close()
    
    return render_template('edit_profile.html', user=user)

# ============================================
# TAKİP SİSTEMİ
# ============================================

@app.route('/follow/<int:user_id>', methods=['POST'])
@login_required
def follow_user(user_id):
    """Kullanıcıyı takip et"""
    if user_id == session['user_id']:
        flash('Kendinizi takip edemezsiniz.', 'error')
        return redirect(request.referrer or url_for('index'))
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Zaten takip ediyor mu kontrol et
    cursor.execute("""
        SELECT follow_id FROM dbo.User_Follows 
        WHERE follower_id = ? AND following_id = ?
    """, (session['user_id'], user_id))
    
    if cursor.fetchone():
        flash('Bu kullanıcıyı zaten takip ediyorsunuz.', 'info')
    else:
        cursor.execute("""
            INSERT INTO dbo.User_Follows (follower_id, following_id)
            VALUES (?, ?)
        """, (session['user_id'], user_id))
        conn.commit()
        flash('Takip edildi!', 'success')
    
    conn.close()
    return redirect(request.referrer or url_for('index'))

@app.route('/unfollow/<int:user_id>', methods=['POST'])
@login_required
def unfollow_user(user_id):
    """Takibi bırak"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        DELETE FROM dbo.User_Follows 
        WHERE follower_id = ? AND following_id = ?
    """, (session['user_id'], user_id))
    conn.commit()
    conn.close()
    
    flash('Takip bırakıldı.', 'success')
    return redirect(request.referrer or url_for('index'))

# ============================================
# YAZI DETAY SAYFASI
# ============================================

@app.route('/post/<int:post_id>')
def post_detail(post_id):
    """Yazı detay sayfası"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Yazıyı getir
    cursor.execute("""
        SELECT p.post_id, p.post_title, p.post_content, p.post_date,
               u.users_name, u.users_id, c.categories_name, c.categories_id
        FROM dbo.Post p
        LEFT JOIN dbo.Users u ON p.users_id = u.users_id
        LEFT JOIN dbo.Categories c ON p.categories_id = c.categories_id
        WHERE p.post_id = ?
    """, (post_id,))
    row = cursor.fetchone()
    
    if not row:
        conn.close()
        return "Yazı bulunamadı", 404
    
    post = rows_to_dicts(cursor, row)
    
    # Yazarı takip ediyor mu?
    is_following = False
    if 'user_id' in session and post['users_id']:
        cursor.execute("""
            SELECT follow_id FROM dbo.User_Follows 
            WHERE follower_id = ? AND following_id = ?
        """, (session['user_id'], post['users_id']))
        is_following = cursor.fetchone() is not None
    
    # Yorumları getir
    cursor.execute("""
        SELECT c.comment_id, c.comment_content, c.comment_date, u.users_name, u.users_id
        FROM dbo.Comments c
        LEFT JOIN dbo.Users u ON c.users_id = u.users_id
        WHERE c.post_id = ?
        ORDER BY c.comment_date DESC
    """, (post_id,))
    comments = rows_to_dicts(cursor, cursor.fetchall())
    
    # Yazının etiketlerini getir
    cursor.execute("""
        SELECT t.tags_id, t.tag_name
        FROM dbo.Tags t
        INNER JOIN dbo.Post_Tags pt ON t.tags_id = pt.tags_id
        WHERE pt.post_id = ?
    """, (post_id,))
    tags = rows_to_dicts(cursor, cursor.fetchall())
    
    conn.close()
    return render_template('post.html', post=post, comments=comments, 
                          tags=tags, is_following=is_following)

# ============================================
# YORUM EKLEME
# ============================================

@app.route('/post/<int:post_id>/comment', methods=['POST'])
@login_required
def add_comment(post_id):
    """Yazıya yorum ekle"""
    content = request.form.get('comment', '').strip()
    
    if not content:
        flash('Yorum boş olamaz.', 'error')
        return redirect(url_for('post_detail', post_id=post_id))
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO dbo.Comments (comment_content, comment_date, post_id, users_id)
        VALUES (?, GETDATE(), ?, ?)
    """, (content, post_id, session['user_id']))
    conn.commit()
    conn.close()
    
    flash('Yorumunuz eklendi.', 'success')
    return redirect(url_for('post_detail', post_id=post_id))

# ============================================
# KATEGORİ SAYFASI
# ============================================

@app.route('/category/<int:category_id>')
def category(category_id):
    """Kategoriye ait yazıları listeler"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Kategori bilgisi
    cursor.execute("SELECT categories_id, categories_name FROM dbo.Categories WHERE categories_id = ?", (category_id,))
    row = cursor.fetchone()
    
    if not row:
        conn.close()
        return "Kategori bulunamadı", 404
    
    category_data = rows_to_dicts(cursor, row)
    
    # Kategorideki yazılar
    cursor.execute("""
        SELECT p.post_id, p.post_title, p.post_content, p.post_date,
               u.users_name, c.categories_name
        FROM dbo.Post p
        LEFT JOIN dbo.Users u ON p.users_id = u.users_id
        LEFT JOIN dbo.Categories c ON p.categories_id = c.categories_id
        WHERE p.categories_id = ?
        ORDER BY p.post_date DESC
    """, (category_id,))
    posts = rows_to_dicts(cursor, cursor.fetchall())
    
    conn.close()
    return render_template('category.html', category=category_data, posts=posts)

# ============================================
# TÜM KATEGORİLER SAYFASI
# ============================================

@app.route('/categories')
def categories_page():
    """Tüm kategorileri listeler"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT c.categories_id, c.categories_name, c.categories_type, COUNT(p.post_id) as post_count
        FROM dbo.Categories c
        LEFT JOIN dbo.Post p ON c.categories_id = p.categories_id
        GROUP BY c.categories_id, c.categories_name, c.categories_type
        ORDER BY c.categories_name
    """)
    all_categories = rows_to_dicts(cursor, cursor.fetchall())
    
    conn.close()
    return render_template('categories.html', all_categories=all_categories)

# ============================================
# YAZAR SAYFASI
# ============================================

@app.route('/author/<int:author_id>')
def author(author_id):
    """Yazara ait yazıları listeler"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Yazar bilgisi
    cursor.execute("SELECT users_id, users_name, users_email FROM dbo.Users WHERE users_id = ?", (author_id,))
    row = cursor.fetchone()
    
    if not row:
        conn.close()
        return "Yazar bulunamadı", 404
    
    author_data = rows_to_dicts(cursor, row)
    
    # Yazarı takip ediyor mu?
    is_following = False
    if 'user_id' in session:
        cursor.execute("""
            SELECT follow_id FROM dbo.User_Follows 
            WHERE follower_id = ? AND following_id = ?
        """, (session['user_id'], author_id))
        is_following = cursor.fetchone() is not None
    
    # Takipçi sayısı
    cursor.execute("SELECT COUNT(*) FROM dbo.User_Follows WHERE following_id = ?", (author_id,))
    followers_count = cursor.fetchone()[0]
    
    # Yazarın yazıları
    cursor.execute("""
        SELECT p.post_id, p.post_title, p.post_content, p.post_date,
               u.users_name, c.categories_name
        FROM dbo.Post p
        LEFT JOIN dbo.Users u ON p.users_id = u.users_id
        LEFT JOIN dbo.Categories c ON p.categories_id = c.categories_id
        WHERE p.users_id = ?
        ORDER BY p.post_date DESC
    """, (author_id,))
    posts = rows_to_dicts(cursor, cursor.fetchall())
    
    conn.close()
    return render_template('author.html', author=author_data, posts=posts, 
                          is_following=is_following, followers_count=followers_count)

# ============================================
# TÜM YAZARLAR SAYFASI
# ============================================

@app.route('/authors')
def authors_page():
    """Tüm yazarları listeler"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT u.users_id, u.users_name, u.users_email, COUNT(p.post_id) as post_count,
               (SELECT COUNT(*) FROM dbo.User_Follows WHERE following_id = u.users_id) as followers_count
        FROM dbo.Users u
        LEFT JOIN dbo.Post p ON u.users_id = p.users_id
        GROUP BY u.users_id, u.users_name, u.users_email
        ORDER BY post_count DESC
    """)
    all_authors = rows_to_dicts(cursor, cursor.fetchall())
    
    # Takip durumlarını kontrol et
    if 'user_id' in session:
        for author in all_authors:
            cursor.execute("""
                SELECT follow_id FROM dbo.User_Follows 
                WHERE follower_id = ? AND following_id = ?
            """, (session['user_id'], author['users_id']))
            author['is_following'] = cursor.fetchone() is not None
    
    conn.close()
    return render_template('authors.html', all_authors=all_authors)

# ============================================
# ARAMA
# ============================================

@app.route('/search')
def search():
    """Arama sonuçları"""
    query = request.args.get('q', '').strip()
    
    if not query:
        return redirect(url_for('index'))
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Başlık veya içerikte ara
    cursor.execute("""
        SELECT p.post_id, p.post_title, p.post_content, p.post_date,
               u.users_name, c.categories_name
        FROM dbo.Post p
        LEFT JOIN dbo.Users u ON p.users_id = u.users_id
        LEFT JOIN dbo.Categories c ON p.categories_id = c.categories_id
        WHERE p.post_title LIKE ? OR p.post_content LIKE ?
        ORDER BY p.post_date DESC
    """, (f'%{query}%', f'%{query}%'))
    posts = rows_to_dicts(cursor, cursor.fetchall())
    
    conn.close()
    return render_template('search.html', posts=posts, query=query)

# ============================================
# ETİKET SAYFASI
# ============================================

@app.route('/tag/<int:tag_id>')
def tag(tag_id):
    """Etikete ait yazıları listeler"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Etiket bilgisi
    cursor.execute("SELECT tags_id, tag_name FROM dbo.Tags WHERE tags_id = ?", (tag_id,))
    row = cursor.fetchone()
    
    if not row:
        conn.close()
        return "Etiket bulunamadı", 404
    
    tag_data = rows_to_dicts(cursor, row)
    
    # Etikete sahip yazılar
    cursor.execute("""
        SELECT p.post_id, p.post_title, p.post_content, p.post_date,
               u.users_name, c.categories_name
        FROM dbo.Post p
        INNER JOIN dbo.Post_Tags pt ON p.post_id = pt.post_id
        LEFT JOIN dbo.Users u ON p.users_id = u.users_id
        LEFT JOIN dbo.Categories c ON p.categories_id = c.categories_id
        WHERE pt.tags_id = ?
        ORDER BY p.post_date DESC
    """, (tag_id,))
    posts = rows_to_dicts(cursor, cursor.fetchall())
    
    conn.close()
    return render_template('tag.html', tag=tag_data, posts=posts)

# ============================================
# UYGULAMAYI ÇALIŞTIR
# ============================================

if __name__ == '__main__':
    app.run(debug=True, port=5000)
