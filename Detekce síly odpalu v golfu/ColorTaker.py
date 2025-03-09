import cv2
import numpy as np
import pyautogui
import mss
import keyboard

def get_pixel_color():
    """Po stisknutí mezerníku vypíše barvu pixelu pod kurzorem a vygeneruje rozumný RGB rozsah."""
    with mss.mss() as sct:
        while True:
            if keyboard.is_pressed("space"):
                # Získání pozice kurzoru
                x, y = pyautogui.position()

                # Pořízení screenshotu celé obrazovky
                screenshot = sct.grab(sct.monitors[1])
                img = np.array(screenshot)

                # Získání RGB hodnoty daného pixelu
                pixel_rgb = img[y, x]
                r, g, b = pixel_rgb[0], pixel_rgb[1], pixel_rgb[2]

                # Nastavení dynamického rozsahu (+-10 pro R, G, B s ochranou proti překročení 0–255)
                r_range = 10
                g_range = 10
                b_range = 10

                lower_rgb = np.array([max(0, r - r_range), max(0, g - g_range), max(0, b - b_range)], dtype=np.uint8)
                upper_rgb = np.array([min(255, r + r_range), min(255, g + g_range), min(255, b + b_range)], dtype=np.uint8)

                # Výpis výsledků
                print("\nPixel na souřadnicích:", (x, y))
                print(f"RGB: ({r}, {g}, {b})")
                print(f"Doporučený RGB rozsah pro detekci:")
                print(f"   lower_rgb = np.array({lower_rgb.tolist()}, dtype=np.uint8)")
                print(f"   upper_rgb = np.array({upper_rgb.tolist()}, dtype=np.uint8)")

                # Počkej, než uživatel uvolní mezerník, aby nedošlo k opakovanému čtení
                keyboard.wait("space", suppress=True)

            # Ukončení skriptu po stisknutí ESC
            if keyboard.is_pressed("esc"):
                print("\nUkončuji skript.")
                break

# Spuštění skriptu
print("Stiskni MEZERNÍK pro detekci barvy pod kurzorem.")
print("Stiskni ESC pro ukončení.")
get_pixel_color()
