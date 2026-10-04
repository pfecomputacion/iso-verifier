# 🔐 Verificador de Firmas ISO

[![Build](https://github.com/pfecomputacion/iso-verifier/actions/workflows/build.yml/badge.svg)](https://github.com/pfecomputacion/iso-verifier/actions/workflows/build.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![PySide6](https://img.shields.io/badge/PySide6-6.6%2B-green.svg)](https://www.qt.io/qt-for-python)
[![Release](https://img.shields.io/github/v/release/pfecomputacion/iso-verifier)](https://github.com/pfecomputacion/iso-verifier/releases)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux-lightgrey.svg)]()

Aplicación de escritorio para verificar la autenticidad de imágenes ISO
mediante firmas GPG o hashes SHA-256.


![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![PySide6](https://img.shields.io/badge/PySide6-6.6%2B-green)
![License](https://img.shields.io/badge/License-MIT-yellow)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux-lightgrey)

---

## ✨ Características

- 🖥️ **GUI moderna** con PySide6 (Qt6): temas claro y oscuro, atajos de teclado, drag & drop.
- 💻 **Modo CLI** para automatización e integración en scripts.
- 🔐 **Verificación GPG** de firmas `.sig`, `.asc` y `.gpg`.
- 🧮 **Cálculo de SHA-256** en streaming, con progreso en tiempo real (MB/s, ETA, tiempo transcurrido).
- 📋 **Pegar hash desde el portapapeles** con extracción automática (aunque copies texto con formato `hash *archivo.iso`).
- ⏹️ **Cancelación** de verificaciones en curso (botón o `Esc`).
- 💾 **Persistencia de configuración**: tema, geometría de la ventana y últimas carpetas usadas.
- 📦 **Empaquetado** de instaladores `.deb` (Linux) y `.exe` (Windows) con un solo comando.
- 🎨 **Icono propio** y splash screen al arrancar.
- 🌍 **Multiplataforma**: Windows, Linux y macOS.

---

## 📸 Capturas

> _Añade aquí capturas de pantalla en `docs/screenshots/`_

| Tema claro | Tema oscuro |
|:---:|:---:|
| ![Light](docs/screenshots/light.png) | ![Dark](docs/screenshots/dark.png) |

---

## 🚀 Instalación

### Requisitos previos

- **Python 3.10 o superior**
- **GnuPG** instalado en el sistema (para verificación GPG):
  - Windows: [gpg4win.org](https://www.gpg4win.org/)
  - Debian/Ubuntu: `sudo apt install gnupg`
  - Fedora: `sudo dnf install gnupg2`
  - Arch: `sudo pacman -S gnupg`

### Instalación rápida

```bash
# 1. Clonar el repositorio
git clone https://github.com/tu-usuario/iso-verifier.git
cd iso-verifier

# 2. Crear y activar el entorno virtual
python -m venv .venv

# Linux / macOS
source .venv/bin/activate

# Windows (Git Bash)
source .venv/Scripts/activate

# Windows (PowerShell)
.venv\Scripts\Activate.ps1

# 3. Instalar dependencias (script incluido)
python install_deps.py

# 4. Generar iconos
python generate_icon.py
