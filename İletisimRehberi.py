import pyodbc

conn=pyodbc.connec(
    'Driver={ODBC Driver 17 for SQL Server};'
    'Server=SORA\\SQLEXPRESS;' 
    'Database=TEST;' 
    'Trusted_Connection=yes;'
)
cursor=conn.cursor()
def kisi_ekle(ad,soyad,telefon,email):
    cursor.execute('''
         INSERT INTO Kisiler(ad,soyad,telefon,email)
         VALUES("Sema", "Saz","05418232132","semasazz7@gmail.com")
                   ''',(ad,soyad,telefon,email))
    conn.commit()
    print("Kişi başarıyla eklendi!")