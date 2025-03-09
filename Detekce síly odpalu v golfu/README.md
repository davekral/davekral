# ⛳ Detekce odpalu ve hře *Golf With Your Friends*  

## 📖 Popis  
Tento projekt umožňuje **automatickou analýzu odpalu** ve hře *Golf With Your Friends* pomocí **zpracování obrazových dat**.  
Hlavní funkce zahrnují:  

✅ **Detekci síly odpalu** – analýza vizuálního ukazatele síly odpalu  
✅ **Rozpoznání čísla jamky** – extrakce textu ze hry pomocí OCR  
✅ **Identifikaci stavu hry** – sledování, zda se míček pohybuje nebo skončil v jamce  
✅ **Hledání tabulky výsledků** – detekce na základě barvy a kontur  

## 🛠 Použité technologie  
- 📸 **MSS** – rychlé snímání obrazovky  
- 🎯 **OpenCV** – zpracování obrazu pro detekci ukazatele síly a tabulek  
- 🔍 **Tesseract OCR** – rozpoznávání textu (např. číslo jamky, stav hry)  
- ⏳ **Multithreading** – paralelní hledání textu „HOLE“ během měření odpalu  
- ⌨ **PyAutoGUI & Keyboard** – detekce vstupu a získání barevných rozsahů  

## 📂 Soubory v projektu  

- **`Main.py`** – hlavní skript pro detekci odpalu a stavu hry  
- **`ColorTaker.py`** – nástroj pro získání RGB hodnot pixelu  
- **`ContoursFinder.py`** – vizualizace detekovaných kontur v obraze  
- **`TextDetection.py`** – OCR detekce textu ze hry 
