import requests
from bs4 import BeautifulSoup
import json
import datetime

def main():
    # URL de la página
    url = "https://loteriasdominicanas.com/"
    
    print("🚀 Conectando a loteriasdominicanas.com...")
    
    # Hacemos la petición con un "User-Agent" para simular que somos un navegador real (evita bloqueos)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status() # Verifica que la página cargó bien
    except Exception as e:
        print(f"❌ Error conectando a la web: {e}")
        return

    # Analizamos el HTML
    soup = BeautifulSoup(response.text, 'html.parser')
    
    results_list = []
    
    # Buscamos todos los bloques de juegos (divs con la clase 'game-block')
    game_blocks = soup.find_all('div', class_='game-block')
    
    print(f"🔍 Encontrados {len(game_blocks)} bloques de lotería.")

    for block in game_blocks:
        try:
            # 1. Obtener el nombre de la lotería
            title_div = block.find('div', class_='company-title')
            name = title_div.get_text(strip=True) if title_div else "Sin Nombre"
            
            # 2. Obtener la fecha
            date_div = block.find('div', class_='session-date')
            date = date_div.get_text(strip=True) if date_div else ""

            # 3. Obtener los números (esto era lo faltante!)
            scores_div = block.find('div', class_='game-scores')
            numbers = []
            if scores_div:
                # Buscamos todos los spans con clase 'score' dentro del bloque de puntuación
                numbers_spans = scores_div.find_all('span', class_='score')
                numbers = [span.get_text(strip=True) for span in numbers_spans]

            # Solo guardamos si hay números válidos (para no guardar basura de anuncios)
            if len(numbers) >= 3:
                lottery_data = {
                    "nombre": name,
                    "fecha": date,
                    "numeros": numbers,
                    "actualizado": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                results_list.append(lottery_data)
                # Debug: print(f"✅ {name}: {' '.join(numbers)}")

        except Exception as e:
            # Si falla un solo bloque, continuamos con los demás
            print(f"⚠️ Error procesando un bloque: {e}")
            continue

    # Guardar en el archivo JSON DENTRO de la carpeta de la web
    output_path = "PlanLotteries/data.json"
    
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results_list, f, ensure_ascii=False, indent=4)
        
        print(f"✅ ÉXITO TOTAL! Se guardaron {len(results_list)} resultados en '{output_path}'.")
        print("💡 Netlify debería actualizarse pronto en GitHub.")
        
    except Exception as e:
        print(f"❌ Error guardando el archivo: {e}")

if __name__ == "__main__":
    main()