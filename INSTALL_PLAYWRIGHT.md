# Installation de Playwright pour le générateur de screenshots

## Prérequis

Le générateur automatique de screenshots nécessite Playwright pour fonctionner.

## Installation

### 1. Installer Playwright via pip

```bash
pip install playwright
```

### 2. Installer les navigateurs Chromium

**Méthode recommandée (fonctionne même si playwright n'est pas dans PATH) :**

```bash
python -m playwright install chromium
```

**Alternative (si playwright est dans PATH) :**

```bash
playwright install chromium
```

### Sur Windows (PowerShell)

```powershell
# Installer Playwright
pip install playwright

# Installer Chromium (utilisez cette méthode si playwright n'est pas dans PATH)
python -m playwright install chromium
```

**Note :** Si vous obtenez l'erreur "playwright n'est pas reconnu", utilisez `python -m playwright install chromium` à la place.

### Sur Linux/Mac

```bash
# Installer Playwright
pip install playwright

# Installer Chromium
playwright install chromium
```

## Vérification

Pour vérifier que Playwright est correctement installé :

```python
from playwright.async_api import async_playwright

async def test():
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch()
    print("✅ Playwright fonctionne correctement!")
    await browser.close()
    await playwright.stop()

import asyncio
asyncio.run(test())
```

## Dépannage

### Erreur "Playwright not installed"

1. Vérifiez que Playwright est installé :
   ```bash
   pip list | grep playwright
   ```

2. Si non installé, réinstallez :
   ```bash
   pip install playwright
   playwright install chromium
   ```

### Erreur "Executable doesn't exist"

Cela signifie que Chromium n'est pas installé. Exécutez :
```bash
playwright install chromium
```

### Sur les serveurs Linux (headless)

Assurez-vous d'avoir les dépendances système :
```bash
# Ubuntu/Debian
sudo apt-get install -y libnss3 libatk-bridge2.0-0 libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 libxfixes3 libxrandr2 libgbm1 libasound2

# CentOS/RHEL
sudo yum install -y nss atk at-spi2-atk libdrm libxkbcommon libXcomposite libXdamage libXfixes libXrandr mesa-libgbm alsa-lib
```

## Utilisation

Une fois installé, le générateur de screenshots sera automatiquement disponible dans l'interface :

1. Allez sur la page de votre projet
2. Cliquez sur l'onglet "Advanced"
3. Utilisez la section "Store Screenshots Generator"
4. Choisissez iOS, Android, ou les deux
5. Cliquez sur le bouton pour générer

Les screenshots seront téléchargés dans un fichier ZIP organisé par store et résolution.

