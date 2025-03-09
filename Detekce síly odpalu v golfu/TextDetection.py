import cv2
import numpy as np
import pytesseract
import mss
import keyboard

# Nastavení cesty k Tesseractu
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def capture_text():
    """Po stisknutí mezerníku sejme obrazovku a vypíše detekovaný text."""
    with mss.mss() as sct:
        while True:
            if keyboard.is_pressed("space"):
                print("\n Pořizuji screenshot a čtu text...")
                
                # Pořízení screenshotu celé obrazovky
                screenshot = sct.grab(sct.monitors[1])
                img = np.array(screenshot)

                # Převod na odstíny šedi pro lepší rozpoznání
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

                # Použití OCR k rozpoznání textu
                text = pytesseract.image_to_string(gray, lang="eng")

                # Výpis rozpoznaného textu
                print("\n Detekovaný text:")
                print(text.strip() if text.strip() else "Nebyl nalezen žádný text.")

                # Malé zpoždění, aby se nespustilo vícekrát najednou
                keyboard.wait("space")

            # Ukončení skriptu po stisknutí ESC
            if keyboard.is_pressed("esc"):
                print("\n Ukončuji skript.")
                break

# Spuštění skriptu
print("Stiskni MEZERNÍK pro detekci textu na obrazovce.")
print("Stiskni ESC pro ukončení.")
capture_text()
