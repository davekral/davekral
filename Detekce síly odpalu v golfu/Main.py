# Funkce pro detekci textu
import cv2
import numpy as np
import pytesseract
import mss
import time

# Nastavení cesty k Tesseractu (přizpůsob podle svého systému)
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Definujeme rozsah zelené barvy tabulky v RGB
lower_green = np.array([50, 100, 50], dtype=np.uint8)  # Spodní hranice zelené
upper_green = np.array([100, 180, 100], dtype=np.uint8)  # Horní hranice zelené

# Nastavení barev pro detekci rámečku ukazatele síly (zelená barva)
lower_bar = np.array([114, 188, 107], dtype=np.uint8)  # Spodní hranice zelené
upper_bar = np.array([134, 208, 127], dtype=np.uint8)  # Horní hranice zelené

lower_bar_pil = np.array([114, 188, 107], dtype=np.uint8)  # Spodní hranice zelené
upper_bar_pil = np.array([134, 208, 127], dtype=np.uint8)  # Horní hranice zelené

# Nastavení barev pro detekci žluté části síly odpalu
lower_yellow = np.array([0, 206, 245], dtype=np.uint8)  # Spodní hranice žluté v HSV
upper_yellow = np.array([10, 226, 255], dtype=np.uint8)  # Horní hranice žluté v HSV

# Funkce pro detekci libovolného slova
def detect_text(target_word):
    print(f"Snímání obrazovky pro detekci slova")
    
    with mss.mss() as sct:
        while True:
            # Pořízení screenshotu celé obrazovky
            screenshot = sct.grab(sct.monitors[1])
            img = np.array(screenshot)

            # Převod na odstíny šedi pro lepší rozpoznání
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

            # Použití OCR k rozpoznání textu
            text = pytesseract.image_to_string(gray, lang="eng")

            # Kontrola, zda se na obrazovce objeví cílové slovo
            if target_word.upper() in text.upper():  # Ignoruje velikost písmen
                print(f"Text detekován! Akce potvrzena.")
                break  # Ukončí smyčku po detekci

            # Čekání mezi snímáními
            time.sleep(1)


def detect_leaderboard():
    """Hledá tabulku výsledků na základě barvy a tvaru pomocí RGB."""
    print("Hledám tabulku výsledků...")

    with mss.mss() as sct:
        while True:
            # Pořízení screenshotu celé obrazovky
            screenshot = sct.grab(sct.monitors[1])
            img = np.array(screenshot, dtype=np.uint8)

            # OpenCV pracuje s BGR, ale mss dává BGRA -> konvertujeme na BGR
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

            # Vytvoření masky pro detekovanou barvu
            mask = cv2.inRange(img, lower_green, upper_green)

            # Najdeme kontury (obrysy) v masce
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            for contour in contours:
                area = cv2.contourArea(contour)

                # Pokud je obrys dostatečně velký, považujeme ho za tabulku výsledků
                if area > 50000:  # Tento práh můžeme upravit podle testů
                    print("Tabulka výsledků detekována! Čekám 5 sekund...")
                    time.sleep(5)
                    return True  # Potvrzení detekce tabulky

            time.sleep(1)  # Pauza před dalším snímáním

def detect_power_bar():
    """Detekuje oblast ukazatele síly odpalu na základě barev a kontur a zároveň hledá text 'HOLE'."""
    with mss.mss() as sct:
        while True:
            # Snímání celé obrazovky
            screenshot = sct.grab(sct.monitors[1])
            img = np.array(screenshot, dtype=np.uint8)
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)  # Konverze z BGRA na BGR

            # Hledání ukazatele síly odpalu
            mask = cv2.inRange(img, lower_bar, upper_bar)
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            for contour in contours:
                area = cv2.contourArea(contour)

                # Pokud je kontura dostatečně velká, považujeme ji za ukazatel síly
                if area > 5000:
                    x, y, w, h = cv2.boundingRect(contour)
                    print(f"Ukazatel síly nalezen na souřadnicích: X={x}, Y={y}, W={w}, H={h}")
                    return {"top": y, "left": x, "width": w, "height": h}

            # Průběžné hledání textu "HOLE"
            print("Kontroluji, ukončení odpalů...")
            if detect_text("HOLE"):
                print("Konec odpalů detekován! Ukončuji odpaly a hledám tabulku výsledků...")
                return None  # Vrátíme None, což signalizuje, že se ukončí odpaly

            time.sleep(0.1)  # Krátká pauza a hledáme znovu

import threading

def check_for_hole_event(stop_event):
    """Asynchronně hledá text 'HOLE' a nastaví event pro ukončení odpalů."""
    while not stop_event.is_set():
        if detect_text("HOLE"):
            print("Konec odpalů detekován! Ukončuji odpaly a hledám tabulku výsledků...")
            stop_event.set()  # Nastavíme event pro ukončení hlavní smyčky
        time.sleep(0.1)  # Krátká pauza, aby se nezatěžoval procesor

def get_power_percentage(power_bar_region):
    """Získá procentuální sílu odpalu a současně hledá text 'HOLE'."""
    with mss.mss() as sct:
        previous_yellow_length = 0  # Sledování poslední známé délky žluté části
        stop_event = threading.Event()  # Event pro zastavení smyčky

        # Spuštění paralelního vlákna pro hledání "HOLE"
        hole_thread = threading.Thread(target=check_for_hole_event, args=(stop_event,))
        hole_thread.start()

        while not stop_event.is_set():
            # Pořízení screenshotu oblasti s ukazatelem síly
            screenshot = sct.grab(power_bar_region)
            img = np.array(screenshot, dtype=np.uint8)
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)  # Konverze z BGRA na BGR

            # Detekce žluté části v ukazateli síly
            mask = cv2.inRange(img, lower_yellow, upper_yellow)
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            yellow_length = 0  # Celková délka viditelné žluté oblasti

            if contours:
                for contour in contours:
                    x, y, w, h = cv2.boundingRect(contour)
                    yellow_length += w  # Sečteme délku žluté oblasti

            # Výpočet procentuální síly odpalu
            total_bar_length = power_bar_region["width"]
            power_percentage = (yellow_length / total_bar_length) * 100
            power_percentage = min(power_percentage, 100)  # Zajistíme, že nepřekročí 100 %

            print(f"Žlutá délka: {yellow_length} px, Síla odpalu: {power_percentage:.2f}%")

            # Detekce momentu výstřelu (zmizení žluté části)
            if previous_yellow_length > 0 and yellow_length == 0:
                print(f"Výstřel! Síla odpalu byla {previous_yellow_length / total_bar_length * 100:.2f}%")
                break  # Ukončí smyčku po odpalu

            previous_yellow_length = yellow_length  # Uloží poslední známou hodnotu

            time.sleep(0.05)  # Malá pauza pro optimalizaci výkonu

        stop_event.set()  # Ukončíme vlákno pro hledání "HOLE"
        hole_thread.join()  # Počkáme na jeho ukončení



def play_golf():
    jamka = 1
    print(f"Mapa detekována! Start první jamky za 10 sekund.")
    time.sleep(10)

    while jamka <= 18:
        print(f"Hrajeme jamku {jamka}...")

        # **Hledáme ukazatel síly odpalu pro první odpal**
        power_bar = detect_power_bar()

        if power_bar is None:
            print("Konec odpalů detekován během hledání ukazatele síly. Přecházím na tabulku výsledků...")
        else:
            print(f"Ukazatel síly nalezen na souřadnicích X={power_bar['left']}, Y={power_bar['top']}. Čekám na odpaly...")
            first_power_bar_position = (power_bar["left"], power_bar["top"])  # Uložíme počáteční polohu

            while True:
                get_power_percentage(power_bar)  # **Sledujeme sílu odpalu**

                # **Po odpalu hledáme ukazatel síly znovu**
                power_bar_check = detect_power_bar()

                # Pokud se během hledání ukazatele síly detekoval text "HOLE"
                if power_bar_check is None:
                    print("Konec odpalu detekován! Ukončuji odpaly, hledám tabulku výsledků...")
                    break  # Přecházíme na detekci tabulky

                if power_bar_check:
                    current_position = (power_bar_check["left"], power_bar_check["top"])

                    if current_position == first_power_bar_position:
                        print("Ukazatel síly je na stejném místě – čekám na další odpal...")
                        continue  # Vrátíme se na začátek smyčky pro další odpal
                    else:
                        print("Ukazatel síly se posunul – ukončuji odpaly, hledám tabulku výsledků...")
                        break  # Ukončíme smyčku odpalu, protože se ukazatel posunul

                else:
                    print("Ukazatel síly nenalezen – hledám tabulku výsledků...")
                    break  # Pokud ukazatel není nalezen, přejdeme na detekci tabulky

        # **Čekáme na tabulku výsledků**
        if detect_leaderboard():
            jamka += 1  # Zvýšíme číslo jamky

    print("Hra dokončena!")




# Příklad použití
detect_text("FOREST")
# Spuštění hry
play_golf()
