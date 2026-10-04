#!/usr/bin/env python3
"""
Genera instaladores .deb (Linux/Windows/macOS) y .exe (Windows) para la
aplicación de verificación de firmas ISO.

- .deb  → se construye con la librería 'debx' (cross-platform, sin dpkg-deb).
- .exe  → se genera un instalador con Inno Setup a partir del .exe creado
          por PyInstaller.

Uso:
    python build_installers.py
"""

import os
import shutil
import subprocess
import sys
import platform
from pathlib import Path

# ---------------------------------------------------------------------------
# Importación de debx (se instala con: pip install debx)
# ---------------------------------------------------------------------------
try:
    from debx import DebBuilder, Deb822
except ImportError:
    print("❌ La librería 'debx' no está instalada.")
    print("   Instálala dentro del venv con:")
    print("       python -m pip install debx")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Configuración
# ---------------------------------------------------------------------------
APP_NAME = "iso-verifier"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = "Verificador de firmas ISO con GUI dual Qt6/GTK4"
APP_MAINTAINER = "Tu Nombre <tu@email.com>"
APP_ARCH = "amd64"

MAIN_SCRIPT = "iso_verifier.py"
DIST_DIR = Path("dist")
BUILD_DIR = Path("build")


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------
def run(cmd, cwd=None, desc=""):
    print(f"  → {desc or cmd}")
    return subprocess.run(cmd, shell=True, cwd=cwd).returncode == 0


def clean():
    """Limpia directorios de builds anteriores."""
    for d in (DIST_DIR, BUILD_DIR):
        if d.exists():
            shutil.rmtree(d)
    print("🧹 Directorios de build limpiados.")


# ---------------------------------------------------------------------------
# PyInstaller (binario base)
# ---------------------------------------------------------------------------
def build_binary():
    """Genera un ejecutable autónomo con PyInstaller."""
    print("\n🔨 Generando binario con PyInstaller…")
    # Comprobamos que PyInstaller está disponible
    if not shutil.which("pyinstaller"):
        print("❌ PyInstaller no encontrado. Instálalo con: pip install pyinstaller")
        sys.exit(1)

    cmd = (
        f"pyinstaller --onefile --windowed "
        f"--name {APP_NAME} "
        f"--distpath {DIST_DIR} "
        f"--workpath {BUILD_DIR} "
        f"{MAIN_SCRIPT}"
    )
    if not run(cmd, desc="PyInstaller build"):
        print("❌ PyInstaller falló.")
        sys.exit(1)

    # Verificamos que el binario se ha creado (sin extensión en Linux/macOS,
    # con .exe en Windows)
    binario = DIST_DIR / (APP_NAME + (".exe" if platform.system() == "Windows" else ""))
    if not binario.exists():
        # Algunas configuraciones de PyInstaller añaden .exe en Windows
        binario = DIST_DIR / f"{APP_NAME}.exe"
    if not binario.exists():
        print(f"❌ No se encontró el binario generado en {DIST_DIR}/")
        sys.exit(1)

    print(f"✅ Binario generado: {binario}")
    return binario


# ---------------------------------------------------------------------------
# .deb con debx (cross-platform)
# ---------------------------------------------------------------------------
def build_deb(binario: Path):
    """Construye un paquete .deb usando debx (funciona en Linux, macOS y Windows)."""
    print("\n📦 Construyendo paquete .deb con debx…")

    # 1. Crear el builder
    builder = DebBuilder()

    # 2. Metadatos del paquete (control)
    control = Deb822({
        "Package": APP_NAME,
        "Version": APP_VERSION,
        "Architecture": APP_ARCH,
        "Maintainer": APP_MAINTAINER,
        "Description": APP_DESCRIPTION,
        "Depends": "python3, gnupg",
        "Section": "utils",
        "Priority": "optional",
    })
    builder.add_control_entry("control", control.dump())

    # 3. Añadir el ejecutable a /usr/bin/
    with open(binario, "rb") as f:
        builder.add_data_entry(f.read(), f"/usr/bin/{APP_NAME}", mode=0o755)

    # 4. Añadir el archivo .desktop
    desktop_content = (
        "[Desktop Entry]\n"
        "Name=Verificador de Firmas ISO\n"
        "Comment=Comprueba firmas GPG de imágenes ISO\n"
        f"Exec={APP_NAME}\n"
        f"Icon={APP_NAME}\n"
        "Terminal=false\n"
        "Type=Application\n"
        "Categories=Utility;Security;\n"
    )
    builder.add_data_entry(
        desktop_content.encode("utf-8"),
        f"/usr/share/applications/{APP_NAME}.desktop",
        mode=0o644,
    )

    # 5. (Opcional) Añadir un icono placeholder.
    #    Si tienes un archivo .png real, cámbialo aquí.
    #    Por ahora creamos un PNG vacío como marcador de posición.
    #    Puedes comentar este bloque si no quieres icono.
    # icon_data = b""  # <-- Reemplaza con open("icono.png", "rb").read()
    # builder.add_data_entry(
    #     icon_data,
    #     f"/usr/share/icons/hicolor/256x256/apps/{APP_NAME}.png",
    #     mode=0o644,
    # )

    # 6. Escribir el .deb
    deb_file = DIST_DIR / f"{APP_NAME}_{APP_VERSION}_{APP_ARCH}.deb"
    with open(deb_file, "wb") as f:
        f.write(builder.pack())

    print(f"✅ Paquete .deb generado: {deb_file}")
    print(f"   Instálalo en Debian/Ubuntu con: sudo dpkg -i {deb_file}")


# ---------------------------------------------------------------------------
# .exe con Inno Setup (solo Windows)
# ---------------------------------------------------------------------------
def build_exe():
    """Genera un instalador .exe para Windows con Inno Setup."""
    print("\n📦 Construyendo instalador .exe…")

    if platform.system() != "Windows":
        print("ℹ️  El instalador .exe solo se genera en Windows. Omitiendo.")
        return

    # Ruta típica de Inno Setup 6
    iscc_candidates = [
        shutil.which("ISCC.exe"),
        r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
        r"C:\Program Files\Inno Setup 6\ISCC.exe",
    ]
    iscc = next((p for p in iscc_candidates if p and Path(p).exists()), None)

    if not iscc:
        print("❌ No se encontró Inno Setup (ISCC.exe).")
        print("   Descárgalo de: https://jrsoftware.org/isdl.php")
        print("   Instálalo y vuelve a ejecutar este script.")
        return

    # El ejecutable de PyInstaller en Windows lleva .exe
    exe_name = f"{APP_NAME}.exe"
    exe_path = DIST_DIR / exe_name
    if not exe_path.exists():
        print(f"❌ No se encontró {exe_path}. Ejecuta primero build_binary().")
        return

    iss_content = f"""[Setup]
AppName=Verificador de Firmas ISO
AppVersion={APP_VERSION}
DefaultDirName={{autopf}}\\{APP_NAME}
DefaultGroupName=Verificador ISO
OutputDir={DIST_DIR.resolve()}
OutputBaseFilename={APP_NAME}_setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern

[Files]
Source: "{exe_path.resolve()}"; DestDir: "{{app}}"; Flags: ignoreversion

[Icons]
Name: "{{group}}\\Verificador de Firmas ISO"; Filename: "{{app}}\\{exe_name}"
Name: "{{commondesktop}}\\Verificador de Firmas ISO"; Filename: "{{app}}\\{exe_name}"

[Run]
Filename: "{{app}}\\{exe_name}"; Description: "Ejecutar ahora"; Flags: postinstall nowait skipifsilent
"""
    iss_file = BUILD_DIR / f"{APP_NAME}.iss"
    iss_file.parent.mkdir(parents=True, exist_ok=True)
    iss_file.write_text(iss_content)

    if run(f'"{iscc}" "{iss_file}"', desc="Inno Setup compile"):
        print(f"✅ Instalador .exe generado en {DIST_DIR}/")
    else:
        print("❌ Falló la compilación con Inno Setup.")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    print("=" * 60)
    print(f"  Generador de instaladores – {APP_NAME} v{APP_VERSION}")
    print("=" * 60)

    # 1. Limpiar builds anteriores
    clean()

    # 2. Generar el binario con PyInstaller
    binario = build_binary()

    # 3. Generar .deb (cross-platform con debx)
    build_deb(binario)

    # 4. Generar .exe (solo en Windows)
    if platform.system() == "Windows":
        build_exe()
    else:
        print("\nℹ️  Para generar el instalador .exe, ejecuta este script en Windows.")

    print("\n" + "=" * 60)
    print("✅ Proceso completado. Revisa el directorio dist/")
    print("=" * 60)


if __name__ == "__main__":
    main()