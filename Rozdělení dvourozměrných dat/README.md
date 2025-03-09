# 📊 Shlukování a klasifikace dat

## 📖 Popis
Tento projekt implementuje **shlukování a klasifikaci dvourozměrných datových bodů** pomocí různých metod, včetně **K-means, MAXIMIN, hierarchického shlukování a neuronových sítí**. Kromě toho obsahuje **Bayesův klasifikátor, klasifikaci podle nejbližšího souseda (KNN) a lineární diskriminační funkce**.

✅ **Načtení dat a jejich vizualizace**  
✅ **Výpočet matice vzdáleností mezi jednotlivými body**  
✅ **Různé metody shlukování a klasifikace**  
✅ **Vizualizace výsledků klasifikace**  
✅ **Optimalizace algoritmů pomocí iterativních metod**  

## 🛠 Hlavní funkce

### 📥 **Načtení a zpracování dat**
- Data jsou načítána z **Google Drive** a zpracovávána do vhodného formátu.
- Vytvoření **matice vzdáleností** mezi jednotlivými body pro následné shlukování.

### 🔗 **Shlukovací metody**
- **Hierarchické shlukování** – slučování bodů do větších celků na základě nejkratších vzdáleností.
- **Řetězová mapa** – postupné spojování nejbližších bodů s detekcí velkých skoků ve vzdálenostech.
- **MAXIMIN algoritmus** – výběr reprezentativních bodů na základě maximální vzdálenosti.
- **K-means shlukování** – standardní algoritmus rozdělení bodů do předem definovaného počtu shluků.
- **K-means s binárním dělením** – postupné rozdělování shluků na základě nejvzdálenějších bodů.

### 🧠 **Klasifikační metody**
- **Bayesův klasifikátor** – statistické přiřazení bodů k třídám na základě pravděpodobností.
- **Vektorová kvantizace** – přiřazení bodů na základě jejich nejbližšího centra.
- **Klasifikace nejbližšího souseda (KNN)** – přiřazení bodů podle nejbližších sousedů.
- **Lineární diskriminační funkce** – Rosenblattův algoritmus a metoda konstantních přírůstků.

### 🤖 **Neuronové sítě**
- **Stochastický gradientní sestup (SGD)** – trénování neuronové sítě na datech.
- **Batch gradientní sestup (Batch GD)** – optimalizace učení pomocí batche dat.
- **Heavisideova aktivační funkce** – použití pro binární klasifikaci bodů.

## 📊 **Vizualizace výsledků**
- **Scatter ploty** pro vizualizaci bodů a shluků.
- **Heatmapy a konturové grafy** pro klasifikační metody.
- **Iterativní zobrazení optimalizace shlukování a klasifikace**.

