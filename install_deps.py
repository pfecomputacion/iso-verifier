#!/usr/bin/env python3
"""
Instala todas las dependencias Python necesarias para la aplicación
de verificación de firmas ISO con GUI dual Qt6/GTK4.
"""

import subprocess
import sys
import platform

DEPS = [
    "vibegui[qt,gtk]>=0.2.0",   # GUI multi-backend
    "python-gnupg>=0.5.0",      # Verificación de firmas GPG
    "pyinstaller>=6.0",          # Empaquetado a .exe / binario
]

SYSTEM_DEPS_LINUX = {
    "debian": [
        "python3-gi", "gir1.2-gtk-4.0", "libgtk-4-1",
        "python3-pyqt6", "libqt6gui6", "libqt6widgets6",
        "gnupg",
    ],
    "fedora": [
        "python3-gobject", "gtk4", "python3-qt6",
        "qt6-qtbase", "gnupg2",
    ],
    "arch": [
        "python-gobject", "gtk4", "python-pyqt6",
        "qt6-base", "gnupg",
    ],
}


def run(cmd, desc=""):
    print(f"  → {desc or cmd}")
    result = subprocess.run(cmd, shell=True)
    if result.returncode != 0:
        print(f"  ⚠️  Falló: {cmd}")
    return result.returncode == 0


def install_python_deps():
    print("\n📦 Instalando dependencias Python…")
    for dep in DEPS:
        run(f"{sys.executable} -m pip install --upgrade {dep}",
            f"pip install {dep}")


def install_system_deps():
    """Instala dependencias del sistema en Linux (requiere sudo)."""
    if platform.system() != "Linux":
        print("\nℹ️  No se requiere instalación de dependencias del sistema "
              "en esta plataforma.")
        return

    distro = ""
    try:
        with open("/etc/os-release") as f:
            contenido = f.read().lower()
        if "debian" in contenido or "ubuntu" in contenido:
            distro = "debian"
        elif "fedora" in contenido:
            distro = "fedora"
        elif "arch" in contenido:
            distro = "arch"
    except FileNotFoundError:
        pass

    if not distro:
        print("\n⚠️  No se pudo detectar la distribución Linux. "
              "Instala manualmente: GTK4, PyGObject, PyQt6, gnupg.")
        return

    print(f"\n🐧 Instalando dependencias del sistema para {distro}…")
    paquetes = " ".join(SYSTEM_DEPS_LINUX[distro])

    if distro == "debian":
        run(f"sudo apt-get update && sudo apt-get install -y {paquetes}")
    elif distro == "fedora":
        run(f"sudo dnf install -y {paquetes}")
    elif distro == "arch":
        run(f"sudo pacman -S --noconfirm {paquetes}")


def main():
    print("=" * 60)
    print("  Instalador de dependencias – Verificador de firmas ISO")
    print("=" * 60)
    install_system_deps()
    install_python_deps()
    print("\n✅ Instalación completada.")
    print("   Ejecuta la aplicación con:  python iso_verifier.py")
    print("   Para forzar backend:        python iso_verifier.py --backend qt")
    print("                               python iso_verifier.py --backend gtk")


if __name__ == "__main__":
    main()