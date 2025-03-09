import cv2
import numpy as np
import mss
import keyboard

# Definujeme rozsah zelené barvy tabulky v RGB
lower_green = np.array([0, 206, 245], dtype=np.uint8)  # Spodní hranice zelené
upper_green = np.array([10, 226, 255], dtype=np.uint8)  # Horní hranice zelené

def highlight_mask():
    """Po stisknutí mezerníku pořídí screenshot a zvýrazní detekovanou masku na černobílém pozadí."""
    with mss.mss() as sct:
        while True:
            if keyboard.is_pressed("space"):
                print("\nPořizuji screenshot a aplikuji masku...")

                # Pořízení screenshotu celé obrazovky
                screenshot = sct.grab(sct.monitors[1])
                img = np.array(screenshot, dtype=np.uint8)

                # OpenCV pracuje s BGR, ale mss dává BGRA -> konvertujeme na BGR
                img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

                # Vytvoření masky pro detekovanou barvu
                mask = cv2.inRange(img, lower_green, upper_green)

                # Převod originálního obrázku na černobílý
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                gray_colored = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)  # Převedeme zpět do 3 kanálového obrazu

                # Kombinace: Barevné oblasti z původního obrázku + černobílé pozadí
                highlighted = np.where(mask[:, :, None] == 255, img, gray_colored)

                # Zobrazení výsledného obrázku
                cv2.imshow("Zvýrazněná maska", highlighted)
                print("Maska zobrazena. Stiskni libovolnou klávesu pro pokračování.")

                cv2.waitKey(0)  # Počkej na stisk klávesy, než se okno zavře
                cv2.destroyAllWindows()

            # Ukončení skriptu po stisknutí ESC
            if keyboard.is_pressed("esc"):
                print("\nUkončuji skript.")
                break

# Spuštění skriptu
print("Stiskni MEZERNÍK pro pořízení screenshotu a zvýraznění masky.")
print("Stiskni ESC pro ukončení.")
highlight_mask()
