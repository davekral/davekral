# 🚀 Vizualizace a ovládání rakety  

## 📖 Popis  
Tento projekt implementuje **Qt aplikaci**, která vizualizuje a ovládá **raketu** na základě dat z API.  
Aplikace komunikuje se serverem pomocí **HTTP požadavků** a vykresluje aktuální stav rakety, včetně její pozice, rychlosti a rotace.  

✅ **Vizualizace rakety v 2D prostoru**  
✅ **Komunikace s API pro získání a odeslání dat**  
✅ **Ovládání rakety pomocí tlačítek a klávesnice**  
✅ **Grafické zobrazení rychlosti rakety**  
✅ **Detekce nárazu do hranic scény**  

## 🛠 Hlavní funkce  

### 🎨 **Vizualizace scény**  
- Raketa je vykreslena ve **2D prostředí**, kde lze sledovat její pohyb, rotaci a interakce s hranicemi scény.  
- Scéna obsahuje **startovací plošiny**, proti kterým se detekuje přistání.  

### 🔄 **Aktualizace dat z API**  
- Aplikace **periodicky načítá data** z REXYGEN API na lokální adrese
- Z API se získávají následující hodnoty:  
- **X, Y** – souřadnice rakety  
- **VX, VY** – rychlost rakety  
- **Rotation** – úhel otočení rakety  
- **EngineThrottle** – výkon hlavního motoru  
- **LeftThruster, RightThruster** – stav bočních trysek  
- **Touchdown** – zda raketa přistála  
- **Crashed** – zda raketa havarovala  
- **Width, Height** – rozměry scény  

### 🎮 **Ovládání rakety**  

| Ovládací prvek | Akce |
|---------------|------|
| `W` | Aktivace hlavního motoru |
| `Shift + W` | Zvýšení výkonu hlavního motoru |
| `S` | Vypnutí hlavního motoru |
| `A` | Aktivace levé trysky |
| `D` | Aktivace pravé trysky |
| `R` | Reset rakety |
| **Tlačítka v GUI** | Ovládání trysek, reset rakety, změna rozměrů scény |

### 📊 **Grafická vizualizace dat**  
- Rychlosti `VX` a `VY` jsou zobrazeny pomocí **bar grafů**.  
- Vektor rychlosti je znázorněn **šipkou na scéně**.  
- Barva textových popisků se mění podle aktuálního stavu.  

### 🔍 **Detekce kolizí**  
- Aplikace kontroluje, zda raketa **opustila scénu nebo narazila do země**.  
- Pokud dojde k **havarování**, ovládání se zablokuje a zobrazí se příslušná informace.  

## 📂 Struktura projektu  

- **`MyWidget.h / MyWidget.cpp`** – hlavní třída pro vizualizaci a ovládání rakety  
- **`main.cpp`** – spuštění aplikace  
