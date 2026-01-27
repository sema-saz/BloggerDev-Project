from flask import Flask, render_template, request, redirect, url_for, flash
import pyodbc
from datetime import datetime

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
    posts = cursor.fetchall()
    
    # Kategorileri getir (sidebar için)
    cursor.execute("""
        SELECT c.categories_id, c.categories_name, COUNT(p.post_id) as post_count
        FROM dbo.Categories c
        LEFT JOIN dbo.Post p ON c.categories_id = p.categories_id
        GROUP BY c.categories_id, c.categories_name
        ORDER BY c.categories_name
    """)
    categories = cursor.fetchall()
    
    conn.close()
    return render_template('index.html', posts=posts, categories=categories)

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
    post = cursor.fetchone()
    
    if not post:
        conn.close()
        return "Yazı bulunamadı", 404
    
    # Yorumları getir
    cursor.execute("""
        SELECT c.comment_id, c.comment_content, c.comment_date, u.users_name
        FROM dbo.Comments c
        LEFT JOIN dbo.Users u ON c.users_id = u.users_id
        WHERE c.post_id = ?
        ORDER BY c.comment_date DESC
    """, (post_id,))
    comments = cursor.fetchall()
    
    # Yazının etiketlerini getir
    cursor.execute("""
        SELECT t.tags_id, t.tag_name
        FROM dbo.Tags t
        INNER JOIN dbo.Post_Tags pt ON t.tags_id = pt.tags_id
        WHERE pt.post_id = ?
    """, (post_id,))
    tags = cursor.fetchall()
    
    # Kategorileri getir (sidebar için)
    cursor.execute("""
        SELECT c.categories_id, c.categories_name, COUNT(p.post_id) as post_count
        FROM dbo.Categories c
        LEFT JOIN dbo.Post p ON c.categories_id = p.categories_id
        GROUP BY c.categories_id, c.categories_name
        ORDER BY c.categories_name
    """)
    categories = cursor.fetchall()
    
    conn.close()
    return render_template('post.html', post=post, comments=comments, 
                          tags=tags, categories=categories)

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
    category = cursor.fetchone()
    
    if not category:
        conn.close()
        return "Kategori bulunamadı", 404
    
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
    posts = cursor.fetchall()
    
    # Tüm kategoriler (sidebar için)
    cursor.execute("""
        SELECT c.categories_id, c.categories_name, COUNT(p.post_id) as post_count
        FROM dbo.Categories c
        LEFT JOIN dbo.Post p ON c.categories_id = p.categories_id
        GROUP BY c.categories_id, c.categories_name
        ORDER BY c.categories_name
    """)
    categories = cursor.fetchall()
    
    conn.close()
    return render_template('category.html', category=category, posts=posts, categories=categories)

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
    author = cursor.fetchone()
    
    if not author:
        conn.close()
        return "Yazar bulunamadı", 404
    
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
    posts = cursor.fetchall()
    
    # Kategoriler (sidebar için)
    cursor.execute("""
        SELECT c.categories_id, c.categories_name, COUNT(p.post_id) as post_count
        FROM dbo.Categories c
        LEFT JOIN dbo.Post p ON c.categories_id = p.categories_id
        GROUP BY c.categories_id, c.categories_name
        ORDER BY c.categories_name
    """)
    categories = cursor.fetchall()
    
    conn.close()
    return render_template('author.html', author=author, posts=posts, categories=categories)

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
    posts = cursor.fetchall()
    
    # Kategoriler (sidebar için)
    cursor.execute("""
        SELECT c.categories_id, c.categories_name, COUNT(p.post_id) as post_count
        FROM dbo.Categories c
        LEFT JOIN dbo.Post p ON c.categories_id = p.categories_id
        GROUP BY c.categories_id, c.categories_name
        ORDER BY c.categories_name
    """)
    categories = cursor.fetchall()
    
    conn.close()
    return render_template('search.html', posts=posts, query=query, categories=categories)

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
    tag = cursor.fetchone()
    
    if not tag:
        conn.close()
        return "Etiket bulunamadı", 404
    
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
    posts = cursor.fetchall()
    
    # Kategoriler (sidebar için)
    cursor.execute("""
        SELECT c.categories_id, c.categories_name, COUNT(p.post_id) as post_count
        FROM dbo.Categories c
        LEFT JOIN dbo.Post p ON c.categories_id = p.categories_id
        GROUP BY c.categories_id, c.categories_name
        ORDER BY c.categories_name
    """)
    categories = cursor.fetchall()
    
    conn.close()
    return render_template('tag.html', tag=tag, posts=posts, categories=categories)

# ============================================
# UYGULAMAYI ÇALIŞTIR
# ============================================

if __name__ == '__main__':
    app.run(debug=True, port=5000)
