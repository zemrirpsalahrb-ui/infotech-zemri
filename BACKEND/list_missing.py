import sqlite3
c = sqlite3.connect('db.sqlite3').cursor()
c.execute("PRAGMA table_info(api_product)")
print([r[1] for r in c.fetchall()])
c.execute("""SELECT p.id, p.reference, p.name FROM api_product p
WHERE NOT EXISTS (SELECT 1 FROM api_productimage i WHERE i.product_id=p.id AND i.image_url LIKE '/media/%')
ORDER BY p.name""")
rows = c.fetchall()
print(len(rows))
for r in rows:
    print(r[0], '|', r[1], '|', r[2])

