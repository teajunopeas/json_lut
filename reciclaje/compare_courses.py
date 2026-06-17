"""Comparar contenidos de cursos LUT con AM IV."""
import sqlite3
import json

# Cargar AM IV desde JSON
with open('ulpgc_courses.json', 'r', encoding='utf-8') as f:
    ulpgc = json.load(f)
    am_iv = next(c for c in ulpgc if c['code'] == '49197')

print("=" * 100)
print("AM IV - ANÁLISIS MATEMÁTICO IV (ULPGC)")
print("=" * 100)
print(f"Créditos: {am_iv['credits']} ECTS")
print(f"\nPalabras clave:\n{am_iv.get('keywords', [])}")
print(f"\nContenido:\n{am_iv.get('content', 'N/A')}")
print(f"\nLearning Outcomes:\n{am_iv.get('learningOutcomes', 'N/A')}")

# Consultar cursos LUT
conn = sqlite3.connect('lut_courses.db')
conn.row_factory = sqlite3.Row
c = conn.cursor()

codes = ['BM20A8301', 'BM20A8300', 'BM20A7300']

for code in codes:
    c.execute('SELECT * FROM courses WHERE code = ?', (code,))
    row = c.fetchone()
    if row:
        print("\n" + "=" * 100)
        print(f"{code} - {row['name'].upper()} (LUT)")
        print("=" * 100)
        print(f"ECTS: {row['credits_min']}-{row['credits_max']}")
        print(f"\nContenido:\n{row['content']}")
        print(f"\nLearning Outcomes:\n{row['learning_outcomes']}")

conn.close()
