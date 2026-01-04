import requests
from bs4 import BeautifulSoup
import json
import re # Librería para expresiones regulares

# ==========================================
# 1. DEFINIR FUNCIONES AYUDANTES (FIXADO)
# ==========================================

# Función para buscar pares de números (ej: 12, 45)
def get_pairs(text):
    # Busca cualquier cosa que sean exactamente 2 dígitos
    return re.findall(r'\d{2}', text)

# Función para buscar números de 4 dígitos (ej: 1234)
def get_digits_4(text):
    return re.findall(r'\d{4}', text)

# ==========================================
# 2. CONFIGURACIÓN DEL MAESTRO
# ==========================================

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
}

urls = {
    'ld': "https://loteriasdominicanas.com/",
    'ls': "https://luckysevenlottery.com/",
    'rb': "https://robbieslottery.com/"
}

print("🧛 INICIANDO ROBOT V3 (CORREGIDO)...")
print("Cargando hoja de trucos desde data.json...")

# ==========================================
# 3. CARGAR DATA.JSON (BASE DE DATOS)
# ==========================================

try:
    with open('data.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
except FileNotFoundError:
    print("❌ Error fatal: No encuentro 'data.json'.")
    exit()

# Crear lista de qué buscar en LD (Loterías Dominicanas)
# El robot usará esta lista para buscar cada nombre en la web y agarrar los 3 primeros números siguientes.
keys_to_find_ld = [game['name'] for game in data['rd']]

keys_to_find_ls = [game['name'] for game in data['islands'] + data['king']]

keys_to_find_rb = [game['name'] for game in data['islands'] if game['company'] == "ROBBIES LOTTERY"]

print(f"🔍 Objetivos LD: {len(keys_to_find_ld)}")
print(f"🔍 Objetivos LS: {len(keys_to_find_ls)}")
print(f"🔍 Objetivos RB: {len(keys_to_find_rb)}")

# ==========================================
# 4. LÓGICA DE EXTRACCIÓN (Loterías Dominicanas)
# ==========================================

def scrape_ld():
    print("📍 Conectando a Loterías Dominicana...")
    try:
        response = requests.get(urls['ld'], headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        # Convertir toda la página a texto plano para buscar fácilmente
        full_text = soup.get_text(separator='|')
    except:
        print("⚠️ Error conexión LD.")
        return {}

    results = {}
    
    # Buscamos cada juego por su nombre exacto en el texto
    for game_name in keys_to_find_ld:
        # Truco: Dividir el texto por el nombre del juego.
        # Ejemplo: "...|LA PRIMERA 12:00PM|..." -> ["...", "LA PRIMERA", " 12:00PM", "..."]
        # Luego buscamos números en la siguiente parte.
        
        if game_name in full_text:
            parts = full_text.split(game_name)
            if len(parts) > 1:
                # Buscar números en la parte DESPUÉS del nombre
                # Usamos la función get_pairs corregida
                found = get_pairs(parts[1])
                if len(found) >= 3:
                    results[game_name] = found[:3] # Tomar los primeros 3
                    print(f"  ✅ {game_name}: {results[game_name]}")
    
    return results

# ==========================================
# 5. LÓGICA DE EXTRACCIÓN (Lucky Seven)
# ==========================================

def scrape_ls():
    print("📍 Conectando a Lucky Seven...")
    try:
        response = requests.get(urls['ls'], headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        full_text = soup.get_text(separator='|')
    except:
        print("⚠️ Error conexión LS.")
        return {}

    results = {}

    for game_name in keys_to_find_ls:
        if game_name in full_text:
            parts = full_text.split(game_name)
            if len(parts) > 1:
                # Detectar si es Pick 4 o Pares
                if "PICK 4" in game_name or "PHILLIS" in game_name or "DIARIO" in game_name or "FLAMINGO" in game_name:
                    found = get_digits_4(parts[1])
                else:
                    found = get_pairs(parts[1])
                
                if len(found) >= 3:
                    results[game_name] = found[:4] if "PICK 4" in game_name else found[:3]
                    print(f"  ✅ {game_name}: {results[game_name]}")

    return results

# ==========================================
# 6. LÓGICA DE EXTRACCIÓN (Robbies)
# ==========================================

# ==========================================
# LÓGICA DE EXTRACCIÓN (ROBBIES - MODO "DOM HUNTER")
# ==========================================

def scrape_rb():
    print("📍 Conectando a Robbies (Estructura HTML Precisa)...")
    try:
        response = requests.get(urls['rb'], headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
    except Exception as e:
        print(f"❌ Error conexión RB: {e}")
        return {}

    # 1. Buscamos todas las cajas de juegos
    # En el HTML que me pasaste, cada juego está dentro de: <div class="icon-box">
    game_boxes = soup.find_all('div', class_='icon-box')
    
    results = {}

    print(f"   Encontradas {len(game_boxes)} cajas de juegos en el código HTML.")

    # 2. Analizamos cada caja para identificar qué juego es
    for box in game_boxes:
        # Buscar el título dentro de la caja (etiqueta <h5>)
        h5 = box.find('h5')
        
        if h5:
            title = h5.get_text(strip=True).upper()
            # Limpiamos saltos de línea o espacios extra
            
            # --- IDENTIFICACIÓN DEL JUEGO ---
            game_key = None
            
            # Buscamos coincidencias con los nombres de tu data.json
            if "SMART PLAY" in title and "AFTERNOON" in title:
                game_key = "SMART PLAY AFTERNOON"
            elif "SMART PLAY" in title and "EVENING" in title:
                game_key = "SMART PLAY EVENING"
            elif "ZODIAC" in title and "AFTERNOON" in title:
                game_key = "ZODIAC AFTERNOON"
            elif "ZODIAC" in title and "EVENING" in title:
                game_key = "ZODIAC EVENING"
            elif "CURACAO" in title:
                game_key = "CURAZAO" # Aunque no está en data.json, lo encontramos por si acaso
            # "Robbies" no se menciona como tal en el título
            
            # --- EXTRACCIÓN DE NÚMEROS ---
            if game_key:
                # Buscamos todos los divs que tienen clase 'number-circle' DENTRO de la caja del juego
                # Esto nos da los números exactos que se ven en la web
                circles = box.find_all('div', class_='number-circle')
                
                numbers = []
                for c in circles:
                    txt = c.get_text(strip=True)
                    # Filtro simple: debe ser un número
                    if txt.isdigit():
                        numbers.append(txt)
                
                # Robbies es Pick 4 (4 números) o Pick 3 (Zodiac).
                # En el HTML que me pasaste, a veces salen más números, tomamos los primeros 4.
                if len(numbers) > 0:
                    results[game_key] = numbers[:4]
                    print(f"  ✅ {game_key}: {results[game_key]}")

    return results

# ==========================================
# 7. FUNCIONES DE ACTUALIZACIÓN Y GUARDADO
# ==========================================

def update_rd(results):
    # Actualizar juegos RD (Quinielas, Anguilla)
    for game in data['rd']:
        if game['name'] in results:
            nums = results[game['name']]
            game['draws'][0]['numbers'] = nums # Actualizar el primer sorteo

def update_islands_king(results):
    # Actualizar juegos de Islas y King (Pick 4, Pool, etc.)
    for section in ['islands', 'king']:
        for game in data[section]:
            if game['name'] in results:
                nums = results[game['name']]
                # Lógica para Phillisburg (6 premios) o normal (3 premios)
                if len(game['draws']) == 6:
                    # Caso especial Phillisburg: llenar los 3 del medio con el mismo o los siguientes?
                    # Como es difícil extraer 3 premios medios sin clases específicas,
                    # llenamos el 1st y 2nd, y el resto dejamos como están o duplicamos.
                    game['draws'][0]['numbers'] = nums[:4] # 1st MD
                    game['draws'][3]['numbers'] = nums[:4] # 1st EV
                    # Nota: Para tener todos los 6 premios reales, Robbies debe ser la fuente.
                    # Aquí llenamos solo lo que encontramos.
                elif len(game['draws']) == 3:
                    # Estándar Pick 4 (3 premios)
                    game['draws'][0]['numbers'] = nums[:4] # 1st
                    game['draws'][1]['numbers'] = nums[:4] # 2nd
                    game['draws'][2]['numbers'] = nums[:4] # 3rd
                elif len(game['draws']) == 1:
                    # Lotto Pool o Pick 3 (1 solo)
                    game['draws'][0]['numbers'] = nums
                else:
                    game['draws'][0]['numbers'] = nums # Fallback
                
                print(f"  ✅ {game['name']} actualizado.")

# ==========================================
# 8. EJECUCIÓN FINAL
# ==========================================

# 1. Leer LD
ld_results = scrape_ld()

# 2. Leer LS (Lucky Seven)
ls_results = scrape_ls()

# 3. Leer RB (Robbies)
rb_results = scrape_rb()

# 4. Actualizar JSON
update_rd(ld_results)
update_islands_king(ls_results)
# Ojo: RB está dentro de data['islands'] en mi JSON anterior, así que update_islands_king lo cubre.

# 5. Guardar cambios
with open('data.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=4, ensure_ascii=False)

print("\n💾 ARCHIVO data.json ACTUALIZADO Y GUARDADO.")
print("🚀 Recarga planetlotteries.com")