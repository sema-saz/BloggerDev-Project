import pyodbc

server='SORA\\SQLEXPRESS'
database='BloggerDev'
connection=pyodbc.connect(
    f'DRIVER={{ODBC Driver 17 for SQL Server}};'
    f'SERVER={server};'
    f'DATABASE={database};'
    f'Trusted_Connection=yes;'
)

cursor = connection.cursor()

print("=== POST TABLOSU SÜTUNLARI ===")
cursor.execute("SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'Post'")
for col in cursor.fetchall():
    print(col[0])

print("\n=== CATEGORIES TABLOSU SÜTUNLARI ===")
cursor.execute("SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'Categories'")
for col in cursor.fetchall():
    print(col[0])

print("\n=== USERS TABLOSU SÜTUNLARI ===")
cursor.execute("SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'Users'")
for col in cursor.fetchall():
    print(col[0])

print("\n=== COMMENTS TABLOSU SÜTUNLARI ===")
cursor.execute("SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'Comments'")
for col in cursor.fetchall():
    print(col[0])

connection.close()