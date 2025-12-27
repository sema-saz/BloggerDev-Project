
"""import pyodbc

try:
    conn = pyodbc.connect(
        'DRIVER={ODBC Driver 17 for SQL Server};'
        'SERVER=SORA\\SQLEXPRESS;'
        'DATABASE=TEST;'  # Buraya bağlanmak istediğin veritabanının adını yazabilirsin
        'Trusted_Connection=yes;'
    )
    print("Başarıyla MSSQL'e bağlandık! 🎉")
except Exception as e:
    print("Bağlantı hatası:", e)
"""
import pyodbc

# Bağlantı oluştur
conn = pyodbc.connect(
    'DRIVER={ODBC Driver 17 for SQL Server};'
    'SERVER=SORA\\SQLEXPRESS;'
    'DATABASE=TEST;'
    'Trusted_Connection=yes;'
)

cursor = conn.cursor()

# Öğrenciler tablosunun var olup olmadığını kontrol et ve yoksa oluştur
cursor.execute('''
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name = 'Students' AND xtype = 'U')
BEGIN
    CREATE TABLE Students (
        student_id INT PRIMARY KEY,
        student_name VARCHAR(100),
        age INT
    )
END
''')

# Bağlantıyı commit et ve kapat
cursor.commit()
conn.close()

print("Tablo oluşturuldu veya zaten mevcut!")
