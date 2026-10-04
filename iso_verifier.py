#!/usr/bin/env python3
"""
Verificador de firmas ISO — GUI PySide6 + CLI.

Características:
  · Verificación individual (GPG o hash)
  · Verificación en lote contra un archivo SHA256SUMS / MD5SUMS / etc.
  · Multi-algoritmo: MD5, SHA-1, SHA-256, SHA-512
  · Multi-idioma: español e inglés
  · Auto-detección de firma/hash para Ubuntu, Debian, Mint, CachyOS,
    Fedora, openSUSE, Arch Linux, Zorin OS, Bazzite, Soplos Linux,
    Slackware y BigLinux.
  · Botón "Verificar TODO" para automatizar el proceso completo
  · Integración con menú contextual (Windows y Linux)
  · Historial de verificaciones
  · Guía de compilación integrada (F2)
  · Temas claro/oscuro, splash, iconos, drag & drop
"""

import sys
import re
import json
import argparse
import hashlib
import traceback
import tempfile
import platform
from pathlib import Path
from string import Template
from datetime import datetime

try:
    import gnupg
except ImportError:
    print("ERROR: Instala python-gnupg con: python -m pip install python-gnupg")
    sys.exit(1)

try:
    import requests
except ImportError:
    print("ERROR: Instala requests con: python -m pip install requests")
    sys.exit(1)

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit, QFileDialog, QMessageBox,
    QProgressBar, QFrame, QScrollArea, QDialog, QTextBrowser, QSplashScreen,
    QTabWidget, QComboBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QCheckBox, QListWidget, QListWidgetItem,
)
from PySide6.QtCore import (
    Qt, QThread, Signal, QUrl, QSettings, QByteArray, QElapsedTimer, QTimer, QRect,
)
from PySide6.QtGui import (
    QFont, QDesktopServices, QShortcut, QKeySequence, QIcon, QPixmap,
    QPainter, QColor, QGuiApplication, QBrush,
)

APP_VERSION = "1.7.0"


# ===========================================================================
# i18n (Internacionalización)
# ===========================================================================

STRINGS = {
    "es": {
        "app_title": "Verificador de Firmas ISO",
        "subtitle": "v{v} · Comprueba la autenticidad de tus imágenes ISO.",
        "btn_help": "❓ Ayuda", "btn_theme": "🌓 Tema",
        "btn_lang": "🌐 EN", "btn_exit": "⏻ Salir",
        "btn_history": "📜 Historial",
        "btn_guide": "📘  Guía de compilación",
        "tab_single": "Individual", "tab_batch": "En lote",
        "sec_iso": "1 · Imagen ISO",
        "sec_gpg": "2 · Firma GPG  (.sig / .asc / .gpg) — para ISOs de Linux",
        "sec_hash": "3 · Hash — para ISOs de Windows y otras",
        "ph_iso": "Ruta al archivo .iso (o arrástralo a la ventana)",
        "ph_gpg": "Opcional. Ruta al archivo de firma.",
        "ph_hash": "Pega aquí el hash publicado por el fabricante.",
        "hint_gpg": "Descarga el archivo .sig o .asc junto a la ISO desde la web oficial.",
        "hint_hash": "Copia el hash de la web oficial del fabricante y pégalo aquí.",
        "btn_browse": "📁  Examinar…", "btn_paste": "📋  Pegar",
        "btn_web": "🌐  Web oficial", "algo_label": "Algoritmo:",
        "btn_verify": "🔍   Verificar autenticidad",
        "btn_verify_all": "🚀   Verificar TODO (auto)",
        "btn_cancel": "⏹   Cancelar",
        "label_result": "Resultado",
        "btn_copy_hash": "📋  Copiar hash",
        "chk_auto": "🔎 Autodetectar firma/hash (Ubuntu, Debian, Mint, CachyOS, Fedora, openSUSE, Arch, Zorin, Bazzite, Soplos, Slackware, BigLinux)",
        "auto_detecting": "🔎 Buscando firma/hash para {n}…",
        "auto_not_detected": "ℹ️ No se reconoció la distribución. Introduce la firma o hash manualmente.",
        "auto_error_net": "⚠️ No se pudo conectar con el servidor de {d}.",
        "auto_hash_ok": "✅ Hash encontrado y cargado automáticamente ({a}).",
        "auto_gpg_ok": "✅ Firma GPG descargada automáticamente.",
        "auto_no_entry": "⚠️ La ISO no aparece en el archivo de hashes de {d}.",
        "auto_downloading": "🔎 Descargando lista de hashes de {d}…",
        "auto_fetching_gpg": "🔎 Descargando firma GPG de {d}…",
        "batch_sums": "Archivo de hashes (SHA256SUMS, MD5SUMS, …)",
        "ph_sums": "Ruta al archivo con hashes y nombres de archivo.",
        "batch_dir": "Carpeta con las ISOs",
        "ph_dir": "Carpeta que contiene las ISOs a verificar.",
        "batch_algo": "Algoritmo:",
        "btn_start_batch": "🔍   Verificar lote",
        "batch_table_cols": ["Archivo", "Estado", "Hash calculado", "Esperado"],
        "batch_summary": "Resumen: {ok} correctos, {fail} fallidos, {missing} no encontrados, {total} total.",
        "ready": "Listo.",
        "starting": "{m}: iniciando…",
        "cancelling": "Cancelando…",
        "verify_ok": "✅ Verificación completada.",
        "verify_fail": "❌ La verificación ha fallado.",
        "cancelled": "⏹ Verificación cancelada.",
        "iso_loaded": "ISO cargada: {n}",
        "sig_loaded": "Firma GPG cargada: {n}",
        "hash_extracted": "Hash extraído de {n}",
        "hash_pasted": "Hash pegado desde el portapapeles.",
        "hash_copied": "Hash copiado al portapapeles.",
        "no_hash_yet": "Aún no hay un hash calculado.",
        "clipboard_empty": "El portapapeles está vacío.",
        "not_a_hash": "Lo pegado no parece un hash válido.",
        "ext_unknown": "Extensión no reconocida: {e}",
        "no_file": "{n} no contiene ningún hash válido.",
        "batch_none": "El archivo de hashes no contiene entradas válidas.",
        "batch_no_dir": "La carpeta de ISOs no existe.",
        "batch_done": "Lote completado.",
        "batch_cancelled": "⏹ Lote cancelado.",
        "calculating": "Calculando {a}… {p}%",
        "help_title": "Ayuda — Verificador de Firmas ISO",
        "warn_no_iso": "Falta ISO",
        "warn_no_iso_txt": "Debes seleccionar un archivo ISO.",
        "warn_iso_notfound": "ISO no encontrada",
        "warn_iso_notfound_txt": "No existe el archivo:\n{p}",
        "warn_hash_bad": "Hash inválido",
        "warn_hash_bad_txt": "El campo hash no contiene un valor válido para el algoritmo seleccionado.",
        "lang_changed_t": "Idioma cambiado",
        "lang_changed_m": "El idioma se aplicará al reiniciar la aplicación.",
        "status_file": "📁 {n} · {s}",
        "status_progress": "{l} / {t}  ·  ⏱ {e}  ·  ⚡ {v}  ·  ETA {eta}",
        "status_done": "📁 {n} · {s}  ·  ⏱ {t}",
        "history_title": "Historial de verificaciones",
        "history_empty": "No hay verificaciones registradas todavía.",
        "history_clear": "Vaciar historial",
        "history_cleared": "Historial vaciado.",
        "history_date": "Fecha",
        "history_file": "Archivo",
        "history_result": "Resultado",
        "history_hash": "Hash",
        "guide_not_found_t": "Guía no encontrada",
        "guide_not_found_m": (
            "No se encontró el archivo de la guía de compilación.\n\n"
            "Coloca 'guia_compilacion.html' (o .pdf) en:\n"
            "  · la carpeta del proyecto, o\n"
            "  · la subcarpeta 'docs/'."
        ),
    },
    "en": {
        "app_title": "ISO Signature Verifier",
        "subtitle": "v{v} · Verify the authenticity of your ISO images.",
        "btn_help": "❓ Help", "btn_theme": "🌓 Theme",
        "btn_lang": "🌐 ES", "btn_exit": "⏻ Exit",
        "btn_history": "📜 History",
        "btn_guide": "📘  Compilation guide",
        "tab_single": "Single", "tab_batch": "Batch",
        "sec_iso": "1 · ISO image",
        "sec_gpg": "2 · GPG signature  (.sig / .asc / .gpg) — for Linux ISOs",
        "sec_hash": "3 · Hash — for Windows ISOs and others",
        "ph_iso": "Path to the .iso file (or drag & drop it here)",
        "ph_gpg": "Optional. Path to the signature file.",
        "ph_hash": "Paste the manufacturer-published hash here.",
        "hint_gpg": "Download the .sig or .asc file alongside the ISO from the official website.",
        "hint_hash": "Copy the hash from the official manufacturer website and paste it here.",
        "btn_browse": "📁  Browse…", "btn_paste": "📋  Paste",
        "btn_web": "🌐  Official site", "algo_label": "Algorithm:",
        "btn_verify": "🔍   Verify authenticity",
        "btn_verify_all": "🚀   Verify ALL (auto)",
        "btn_cancel": "⏹   Cancel",
        "label_result": "Result",
        "btn_copy_hash": "📋  Copy hash",
        "chk_auto": "🔎 Auto-detect signature/hash (Ubuntu, Debian, Mint, CachyOS, Fedora, openSUSE, Arch, Zorin, Bazzite, Soplos, Slackware, BigLinux)",
        "auto_detecting": "🔎 Looking for signature/hash for {n}…",
        "auto_not_detected": "ℹ️ Distribution not recognized. Please provide the signature or hash manually.",
        "auto_error_net": "⚠️ Could not connect to {d} server.",
        "auto_hash_ok": "✅ Hash found and loaded automatically ({a}).",
        "auto_gpg_ok": "✅ GPG signature downloaded automatically.",
        "auto_no_entry": "⚠️ The ISO is not listed in the {d} hash file.",
        "auto_downloading": "🔎 Downloading hash list from {d}…",
        "auto_fetching_gpg": "🔎 Downloading GPG signature from {d}…",
        "batch_sums": "Hash file (SHA256SUMS, MD5SUMS, …)",
        "ph_sums": "Path to the file with hashes and filenames.",
        "batch_dir": "Folder containing the ISOs",
        "ph_dir": "Folder that contains the ISOs to verify.",
        "batch_algo": "Algorithm:",
        "btn_start_batch": "🔍   Verify batch",
        "batch_table_cols": ["File", "Status", "Computed hash", "Expected"],
        "batch_summary": "Summary: {ok} OK, {fail} failed, {missing} missing, {total} total.",
        "ready": "Ready.",
        "starting": "{m}: starting…",
        "cancelling": "Cancelling…",
        "verify_ok": "✅ Verification complete.",
        "verify_fail": "❌ Verification failed.",
        "cancelled": "⏹ Verification cancelled.",
        "iso_loaded": "ISO loaded: {n}",
        "sig_loaded": "GPG signature loaded: {n}",
        "hash_extracted": "Hash extracted from {n}",
        "hash_pasted": "Hash pasted from clipboard.",
        "hash_copied": "Hash copied to clipboard.",
        "no_hash_yet": "No hash computed yet.",
        "clipboard_empty": "The clipboard is empty.",
        "not_a_hash": "The pasted text does not look like a valid hash.",
        "ext_unknown": "Unrecognized extension: {e}",
        "no_file": "{n} does not contain any valid hash.",
        "batch_none": "The hash file contains no valid entries.",
        "batch_no_dir": "The ISO folder does not exist.",
        "batch_done": "Batch complete.",
        "batch_cancelled": "⏹ Batch cancelled.",
        "calculating": "Computing {a}… {p}%",
        "help_title": "Help — ISO Signature Verifier",
        "warn_no_iso": "Missing ISO",
        "warn_no_iso_txt": "You must select an ISO file.",
        "warn_iso_notfound": "ISO not found",
        "warn_iso_notfound_txt": "The file does not exist:\n{p}",
        "warn_hash_bad": "Invalid hash",
        "warn_hash_bad_txt": "The hash field does not contain a valid value for the selected algorithm.",
        "lang_changed_t": "Language changed",
        "lang_changed_m": "The language will be applied after restarting the application.",
        "status_file": "📁 {n} · {s}",
        "status_progress": "{l} / {t}  ·  ⏱ {e}  ·  ⚡ {v}  ·  ETA {eta}",
        "status_done": "📁 {n} · {s}  ·  ⏱ {t}",
        "history_title": "Verification history",
        "history_empty": "No verifications recorded yet.",
        "history_clear": "Clear history",
        "history_cleared": "History cleared.",
        "history_date": "Date",
        "history_file": "File",
        "history_result": "Result",
        "history_hash": "Hash",
        "guide_not_found_t": "Guide not found",
        "guide_not_found_m": (
            "The compilation guide file could not be found.\n\n"
            "Place 'guia_compilacion.html' (or .pdf) in:\n"
            "  · the project root, or\n"
            "  · the 'docs/' subfolder."
        ),
    },
}

_current_lang = "es"


def set_language(lang: str):
    global _current_lang
    if lang in STRINGS:
        _current_lang = lang


def tr(key: str, **kwargs) -> str:
    s = STRINGS.get(_current_lang, {}).get(key)
    if s is None:
        s = STRINGS["es"].get(key, key)
    return s.format(**kwargs) if kwargs else s


# ===========================================================================
# Algoritmos
# ===========================================================================

ALGORITHMS = {
    "md5":    {"label": "MD5",     "len": 32,  "fn": hashlib.md5},
    "sha1":   {"label": "SHA-1",   "len": 40,  "fn": hashlib.sha1},
    "sha256": {"label": "SHA-256", "len": 64,  "fn": hashlib.sha256},
    "sha512": {"label": "SHA-512", "len": 128, "fn": hashlib.sha512},
}


def detectar_algoritmo(texto_hash: str) -> str | None:
    if not texto_hash:
        return None
    L = len(texto_hash.strip())
    for alg, info in ALGORITHMS.items():
        if info["len"] == L:
            return alg
    return None


def es_hash_valido(texto: str, algoritmo: str | None = None) -> bool:
    t = texto.strip()
    if not t:
        return False
    if algoritmo and algoritmo in ALGORITHMS:
        return bool(re.fullmatch(rf"[a-fA-F0-9]{{{ALGORITHMS[algoritmo]['len']}}}", t))
    for info in ALGORITHMS.values():
        if re.fullmatch(rf"[a-fA-F0-9]{{{info['len']}}}", t):
            return True
    return False


def extraer_hash(texto: str, algoritmo: str | None = None) -> str | None:
    if not texto:
        return None
    if algoritmo and algoritmo in ALGORITHMS:
        pat = rf"[a-fA-F0-9]{{{ALGORITHMS[algoritmo]['len']}}}"
    else:
        pat = r"[a-fA-F0-9]{32,128}"
    m = re.findall(pat, texto)
    if not m:
        return None
    if algoritmo:
        return m[0].lower()
    for h in m:
        if detectar_algoritmo(h):
            return h.lower()
    return None


# ===========================================================================
# Auto-detección de firmas para distros Linux
# ===========================================================================

CACHE_DIR = Path(tempfile.gettempdir()) / "iso_verifier_cache"
_AUTO_CACHE: dict[str, dict] = {}


def _cache_file_name(url: str) -> str:
    h = hashlib.sha1(url.encode("utf-8")).hexdigest()[:16]
    ext = Path(url).suffix or ".dat"
    return f"{h}{ext}"


def _descargar(url: str, timeout: int = 12) -> bytes | None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_path = CACHE_DIR / _cache_file_name(url)
    if cache_path.is_file():
        try:
            import time
            if time.time() - cache_path.stat().st_mtime < 24 * 3600:
                return cache_path.read_bytes()
        except OSError:
            pass
    try:
        r = requests.get(url, timeout=timeout,
                         headers={"User-Agent": f"iso-verifier/{APP_VERSION}"})
        if r.status_code != 200:
            return None
        cache_path.write_bytes(r.content)
        return r.content
    except requests.RequestException:
        return None


# --- Definición de URLs para cada distribución ---

def _ubuntu_urls(flavor: str, version: str) -> dict:
    if flavor == "ubuntu":
        base = f"https://releases.ubuntu.com/{version}"
    else:
        base = f"https://cdimage.ubuntu.com/{flavor}/releases/{version}/release"
    return {"sums": f"{base}/SHA256SUMS", "gpg": f"{base}/SHA256SUMS.gpg",
            "distro": flavor.capitalize()}


def _debian_urls(version: str) -> dict:
    base = f"https://cdimage.debian.org/mirror/cdimage/archive/{version}/amd64/iso-cd"
    return {"sums": f"{base}/SHA256SUMS", "gpg": f"{base}/SHA256SUMS.sign",
            "distro": "Debian"}


def _mint_urls(version: str) -> dict:
    base = f"https://mirrors.kernel.org/linuxmint/stable/{version}"
    return {"sums": f"{base}/sha256sum.txt", "gpg": f"{base}/sha256sum.txt.gpg",
            "distro": "Linux Mint"}


def _cachyos_urls(version: str) -> dict:
    base = f"https://mirror.cachyos.org/ISO/desktop/{version}"
    return {"sums": f"{base}/cachyos-desktop-linux-{version}.iso.sha256",
            "gpg": None, "distro": "CachyOS"}


def _fedora_urls(version: str) -> dict:
    base = f"https://fedoraproject.org/static/checksums/{version}"
    return {"sums": f"{base}/Fedora-Everything-{version}-x86_64-CHECKSUM",
            "gpg": None, "distro": "Fedora"}


def _opensuse_urls(version: str) -> dict:
    base = "https://download.opensuse.org/tumbleweed/appliances"
    return {"sums": f"{base}/SHA256SUMS", "gpg": f"{base}/SHA256SUMS.gpg",
            "distro": "openSUSE"}


def _arch_urls(version: str) -> dict:
    return {
        "sums": f"https://archlinux.org/iso/{version}/sha256sums.txt",
        "gpg": f"https://archlinux.org/iso/{version}/archlinux-{version}-x86_64.iso.sig",
        "distro": "Arch Linux",
    }


def _zorin_urls(version: str) -> dict:
    return {
        "sums": f"https://mirror.kumi.systems/zorinos/{version}/SHA256SUMS.txt",
        "gpg": None,
        "distro": "Zorin OS",
    }


def _bazzite_urls(version: str) -> dict:
    return {
        "sums": "https://download.bazzite.gg/bazzite-deck-stable-live-amd64.iso-CHECKSUM",
        "gpg": None,
        "distro": "Bazzite",
    }


def _soplos_urls(version: str) -> dict:
    return {
        "sums": "https://soploslinux.com/descargas/SHA256SUMS",
        "gpg": None,
        "distro": "Soplos Linux",
    }


def _slackware_urls(version: str) -> dict:
    return {
        "sums": f"https://mirrors.slackware.com/slackware/slackware64-{version}/CHECKSUMS.md5",
        "gpg": f"https://mirrors.slackware.com/slackware/slackware64-{version}/CHECKSUMS.md5.asc",
        "distro": "Slackware",
        "algoritmo": "md5",
    }


def _biglinux_urls(version: str) -> dict:
    return {
        "sums": f"https://iso.biglinux.com.br/biglinux_{version}.iso.md5",
        "gpg": None,
        "distro": "BigLinux",
        "algoritmo": "md5",
    }


def _rocky_urls(version: str) -> dict:
    base = f"https://download.rockylinux.org/pub/rocky/{version}/isos/x86_64"
    return {
        "sums": f"{base}/CHECKSUM",
        "gpg": f"{base}/CHECKSUM.asc",
        "distro": "Rocky Linux",
    }


def _alma_urls(version: str) -> dict:
    base = f"https://repo.almalinux.org/almalinux/{version}/isos/x86_64"
    return {
        "sums": f"{base}/CHECKSUM",
        "gpg": f"{base}/CHECKSUM.asc",
        "distro": "AlmaLinux",
    }


def _alpine_urls(version: str) -> dict:
    base = f"https://dl-cdn.alpinelinux.org/alpine/{version}/releases/x86_64"
    return {
        "sums": f"{base}/alpine-standard-{version}-x86_64.iso.sha256",
        "gpg": None,
        "distro": "Alpine Linux",
    }


def _void_urls(version: str) -> dict:
    return {
        "sums": "https://repo-default.voidlinux.org/live/current/sha256sum.txt",
        "gpg": "https://repo-default.voidlinux.org/live/current/sha256sum.sig",
        "distro": "Void Linux",
    }


def _gentoo_urls(version: str) -> dict:
    base = ("https://distfiles.gentoo.org/releases/amd64/autobuilds/"
            "current-install-amd64-minimal")
    return {
        "sums": f"{base}/latest-install-amd64-minimal.txt",
        "gpg": None,
        "distro": "Gentoo",
    }


def _popos_urls(version: str) -> dict:
    base = f"https://iso.pop-os.org/{version}/amd64"
    return {
        "sums": f"{base}/SHA256SUMS",
        "gpg": f"{base}/SHA256SUMS.gpg",
        "distro": "Pop!_OS",
    }


def _kde_neon_urls(version: str) -> dict:
    return {
        "sums": f"https://files.kde.org/neon/images/{version}/current/SHA256SUMS",
        "gpg": None,
        "distro": "KDE Neon",
    }



DISTRO_PATTERNS = [
    {
        "regex": re.compile(
            r"^(?P<flavor>ubuntu|xubuntu|kubuntu|lubuntu|ubuntu-mate|"
            r"ubuntukylin|ubuntustudio|edubuntu)-(?P<version>\d{2}\.\d{2}(?:\.\d+)?)-.*\.iso$",
            re.IGNORECASE),
        "urls": lambda m: _ubuntu_urls(m.group("flavor").lower(), m.group("version")),
    },
    {
        "regex": re.compile(r"^debian-(?P<version>\d+\.\d+\.\d+)-.*\.iso$", re.IGNORECASE),
        "urls": lambda m: _debian_urls(m.group("version")),
    },
    {
        "regex": re.compile(r"^linuxmint-(?P<version>\d+(?:\.\d+)?)-.*\.iso$", re.IGNORECASE),
        "urls": lambda m: _mint_urls(m.group("version")),
    },
    {
        "regex": re.compile(r"^cachyos-(?P<version>.*)\.iso$", re.IGNORECASE),
        "urls": lambda m: _cachyos_urls(m.group("version")),
    },
    {
        "regex": re.compile(r"^Fedora-(?P<version>\d+)-.*\.iso$", re.IGNORECASE),
        "urls": lambda m: _fedora_urls(m.group("version")),
    },
    {
        "regex": re.compile(r"^openSUSE-(?P<version>.*)\.iso$", re.IGNORECASE),
        "urls": lambda m: _opensuse_urls(m.group("version")),
    },
    {
        "regex": re.compile(r"^archlinux-(?P<version>\d{4}\.\d{2}\.\d{2})-x86_64\.iso$",
                            re.IGNORECASE),
        "urls": lambda m: _arch_urls(m.group("version")),
    },
    {
        "regex": re.compile(r"^Zorin-OS-(?P<version>\d+)-Core-64-bit\.iso$", re.IGNORECASE),
        "urls": lambda m: _zorin_urls(m.group("version")),
    },
    {
        "regex": re.compile(r"^bazzite-.*\.iso$", re.IGNORECASE),
        "urls": lambda m: _bazzite_urls("latest"),
    },
    {
        "regex": re.compile(r"^soplos-linux-.*-(?P<version>\d+\.\d+)\.iso$", re.IGNORECASE),
        "urls": lambda m: _soplos_urls(m.group("version")),
    },
    {
        "regex": re.compile(r"^slackware64-(?P<version>\d+\.\d+)-.*\.iso$", re.IGNORECASE),
        "urls": lambda m: _slackware_urls(m.group("version")),
    },
    {
        "regex": re.compile(r"^biglinux_(?P<version>\d{4}-\d{2}-\d{2})_.*\.iso$", re.IGNORECASE),
        "urls": lambda m: _biglinux_urls(m.group("version")),
    },
    {
        "regex": re.compile(r"^Rocky-(?P<version>\d+(?:\.\d+)?)-.*\.iso$", re.IGNORECASE),
        "urls": lambda m: _rocky_urls(m.group("version")),
    },
    {
        "regex": re.compile(r"^AlmaLinux-(?P<version>\d+(?:\.\d+)?)-.*\.iso$", re.IGNORECASE),
        "urls": lambda m: _alma_urls(m.group("version")),
    },
    {
        "regex": re.compile(r"^alpine-standard-(?P<version>\d+\.\d+(?:\.\d+)?)-x86_64\.iso$",
                            re.IGNORECASE),
        "urls": lambda m: _alpine_urls(m.group("version")),
    },
    {
        "regex": re.compile(r"^void-live-(?P<version>.*)\.iso$", re.IGNORECASE),
        "urls": lambda m: _void_urls(m.group("version")),
    },
    {
        "regex": re.compile(
            r"^install-amd64-minimal-(?P<version>\d{8}T\d{6}Z)\.iso$",
            re.IGNORECASE),
        "urls": lambda m: _gentoo_urls(m.group("version")),
    },
    {
        "regex": re.compile(r"^pop-os_(?P<version>.*)\.iso$", re.IGNORECASE),
        "urls": lambda m: _popos_urls(m.group("version")),
    },
    {
        "regex": re.compile(r"^neon-(?P<version>.*)\.iso$", re.IGNORECASE),
        "urls": lambda m: _kde_neon_urls(m.group("version")),
    },
]


def detectar_distro(nombre_iso: str) -> dict | None:
    nombre = Path(nombre_iso).name
    for p in DISTRO_PATTERNS:
        m = p["regex"].match(nombre)
        if m:
            info = p["urls"](m)
            return {
                "distro": info["distro"],
                "sums_url": info["sums"],
                "gpg_url": info.get("gpg"),
                "algoritmo": info.get("algoritmo", "sha256"),
            }
    return None


def parsear_hash_lista(contenido: str, nombre_iso: str,
                       algoritmo: str = "sha256") -> str | None:
    L = ALGORITHMS.get(algoritmo, {}).get("len", 64)
    pat_hash = re.compile(rf"\b[a-fA-F0-9]{{{L}}}\b")
    for linea in contenido.splitlines():
        if nombre_iso not in linea:
            continue
        m = pat_hash.search(linea)
        if m:
            return m.group(0).lower()
    return None


def auto_detect_signature(iso_path: str, progreso_cb=None,
                          timeout: int = 12) -> dict:
    resultado = {
        "reconocida": False, "distro": None, "hash": None,
        "algoritmo": "sha256", "sig_path": None, "error": None,
    }
    nombre = Path(iso_path).name
    if nombre in _AUTO_CACHE:
        return _AUTO_CACHE[nombre]

    info = detectar_distro(nombre)
    if not info:
        resultado["error"] = "distro_not_recognized"
        _AUTO_CACHE[nombre] = resultado
        return resultado

    resultado["reconocida"] = True
    resultado["distro"] = info["distro"]
    algoritmo = info.get("algoritmo", "sha256")

    def _prog(msg: str):
        if progreso_cb:
            progreso_cb(msg)

    _prog(tr("auto_downloading", d=info["distro"]))
    contenido_sums = _descargar(info["sums_url"], timeout=timeout)
    if contenido_sums is None:
        resultado["error"] = "network"
        _AUTO_CACHE[nombre] = resultado
        return resultado

    texto = contenido_sums.decode("utf-8", errors="ignore")
    h = parsear_hash_lista(texto, nombre, algoritmo)
    if not h:
        resultado["error"] = "not_listed"
        _AUTO_CACHE[nombre] = resultado
        return resultado

    resultado["hash"] = h
    resultado["algoritmo"] = algoritmo

    if info["gpg_url"]:
        _prog(tr("auto_fetching_gpg", d=info["distro"]))
        contenido_gpg = _descargar(info["gpg_url"], timeout=timeout)
        if contenido_gpg is not None:
            CACHE_DIR.mkdir(parents=True, exist_ok=True)
            sufijo = ".gpg" if info["gpg_url"].endswith(".gpg") else ".sign"
            sig_local = CACHE_DIR / f"{Path(info['gpg_url']).stem}{sufijo}"
            try:
                sig_local.write_bytes(contenido_gpg)
                resultado["sig_path"] = str(sig_local)
            except OSError:
                pass

    _AUTO_CACHE[nombre] = resultado
    return resultado


# ===========================================================================
# Formato y utilidades
# ===========================================================================

def fmt_size(b: float) -> str:
    if b >= 1024 ** 3:
        return f"{b / 1024 ** 3:.2f} GB"
    if b >= 1024 ** 2:
        return f"{b / 1024 ** 2:.1f} MB"
    if b >= 1024:
        return f"{b / 1024:.0f} KB"
    return f"{int(b)} B"


def fmt_time(seconds: float) -> str:
    s = int(round(seconds))
    if s >= 3600:
        return f"{s // 3600:02d}:{(s % 3600) // 60:02d}:{s % 60:02d}"
    return f"{s // 60:02d}:{s % 60:02d}"


def fmt_speed(bps: float) -> str:
    mb = bps / (1024 * 1024)
    if mb >= 1000:
        return f"{mb / 1024:.2f} GB/s"
    if mb >= 1:
        return f"{mb:.0f} MB/s"
    return f"{mb * 1024:.0f} KB/s"


def resource_path(rel: str) -> Path:
    if hasattr(sys, "_MEIPASS"):
        base = Path(sys._MEIPASS)
    else:
        base = Path(__file__).parent
    return base / rel


def buscar_guia_compilacion() -> Path | None:
    """Busca la guía de compilación en HTML o PDF. Devuelve la ruta o None."""
    candidatos = [
        resource_path("docs/guia_compilacion.html"),
        resource_path("guia_compilacion.html"),
        Path(__file__).parent / "docs" / "guia_compilacion.html",
        Path(__file__).parent / "guia_compilacion.html",
        resource_path("docs/guia_compilacion.pdf"),
        resource_path("guia_compilacion.pdf"),
        Path(__file__).parent / "docs" / "guia_compilacion.pdf",
        Path(__file__).parent / "guia_compilacion.pdf",
    ]
    for ruta in candidatos:
        if ruta.is_file():
            return ruta
    return None


# ===========================================================================
# Temas
# ===========================================================================

THEMES = {
    "light": {
        "bg": "#f5f6fa", "bg_card": "#ffffff", "fg": "#2c3e50",
        "fg_muted": "#57606f", "fg_hint": "#7f8c8d",
        "border": "#dcdde1", "border_focus": "#3498db",
        "input_bg": "#ffffff",
        "btn_bg": "#ffffff", "btn_hover": "#ecf0f1", "btn_pressed": "#dfe4ea",
        "separator": "#e1e4e8",
        "accent": "#27ae60", "accent_hover": "#229954",
        "accent_pressed": "#1e8449", "accent_disabled": "#bdc3c7",
        "ok": "#27ae60", "error": "#c0392b", "warn": "#f39c12",
        "progress_bg": "#ecf0f1", "progress_chunk": "#3498db",
        "hash_ok_bg": "#f0fbf5", "hash_err_bg": "#fdf3f2",
        "tab_bg": "#e8ebf0", "tab_sel": "#ffffff",
        "row_ok": "#e8f8f0", "row_err": "#fdeaea", "row_warn": "#fef5e7",
    },
    "dark": {
        "bg": "#1e1e24", "bg_card": "#2a2a32", "fg": "#e8e8ea",
        "fg_muted": "#b0b0b8", "fg_hint": "#808088",
        "border": "#3a3a44", "border_focus": "#4fa8e0",
        "input_bg": "#25252c",
        "btn_bg": "#2f2f38", "btn_hover": "#3a3a44", "btn_pressed": "#454550",
        "separator": "#3a3a44",
        "accent": "#2ecc71", "accent_hover": "#27ae60",
        "accent_pressed": "#1e8449", "accent_disabled": "#4a4a54",
        "ok": "#2ecc71", "error": "#e74c3c", "warn": "#f39c12",
        "progress_bg": "#3a3a44", "progress_chunk": "#4fa8e0",
        "hash_ok_bg": "#1e3a2a", "hash_err_bg": "#3a1e1e",
        "tab_bg": "#26262e", "tab_sel": "#2a2a32",
        "row_ok": "#1e3a2a", "row_err": "#3a1e1e", "row_warn": "#3a3020",
    },
}

QSS_TEMPLATE = Template("""
QMainWindow, QWidget {
    background-color: $bg; color: $fg;
    font-family: "Segoe UI", "Ubuntu", sans-serif; font-size: 13px;
}
QScrollArea { background-color: $bg; border: none; }
QScrollBar:vertical { background: $bg; width: 10px; border-radius: 5px; }
QScrollBar::handle:vertical { background: $border; border-radius: 5px; min-height: 30px; }
QScrollBar::handle:vertical:hover { background: $fg_hint; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }

QLabel#titulo    { font-size: 20px; font-weight: 600; color: $fg; }
QLabel#subtitulo { font-size: 12px; color: $fg_muted; }
QLabel#seccion   { font-weight: 600; color: $fg; padding-top: 4px; }
QLabel#hint      { color: $fg_hint; font-size: 11px; }

QLineEdit {
    background-color: $input_bg; border: 1px solid $border;
    border-radius: 6px; padding: 8px 10px; color: $fg;
    selection-background-color: $border_focus;
}
QLineEdit:focus        { border: 1px solid $border_focus; }
QLineEdit#hashValido   { border: 1px solid $ok;    background-color: $hash_ok_bg; }
QLineEdit#hashInvalido { border: 1px solid $error; background-color: $hash_err_bg; }

QCheckBox { color: $fg; spacing: 6px; }
QCheckBox::indicator { width: 16px; height: 16px; }

QComboBox {
    background-color: $input_bg; border: 1px solid $border;
    border-radius: 6px; padding: 6px 10px; color: $fg; min-width: 100px;
}
QComboBox:hover { border: 1px solid $border_focus; }
QComboBox::drop-down { border: none; }
QComboBox QAbstractItemView {
    background-color: $bg_card; color: $fg; border: 1px solid $border;
    selection-background-color: $border_focus;
}

QPushButton {
    background-color: $btn_bg; border: 1px solid $border;
    border-radius: 6px; padding: 8px 14px; color: $fg;
}
QPushButton:hover    { background-color: $btn_hover; border-color: $border_focus; }
QPushButton:pressed  { background-color: $btn_pressed; }
QPushButton:disabled { color: $fg_hint; }

QPushButton#btnVerificar {
    background-color: $accent; border: none; color: white;
    font-weight: 600; font-size: 14px; padding: 12px 20px; border-radius: 8px;
}
QPushButton#btnVerificar:hover    { background-color: $accent_hover; }
QPushButton#btnVerificar:pressed  { background-color: $accent_pressed; }
QPushButton#btnVerificar:disabled { background-color: $accent_disabled; }

QPushButton#btnCancelar {
    background-color: $error; border: none; color: white;
    font-weight: 600; font-size: 14px; padding: 12px 20px; border-radius: 8px;
}
QPushButton#btnCancelar:hover { background-color: #a93226; }

QTextEdit, QTextBrowser {
    background-color: $bg_card; border: 1px solid $border; border-radius: 6px;
    padding: 10px; color: $fg;
    font-family: "Consolas", "Monaco", monospace; font-size: 12px;
}
QTableWidget {
    background-color: $bg_card; border: 1px solid $border;
    border-radius: 6px; color: $fg;
    gridline-color: $border;
    selection-background-color: $border_focus;
}
QHeaderView::section {
    background-color: $tab_bg; color: $fg;
    border: none; border-right: 1px solid $border;
    padding: 6px 8px; font-weight: 600;
}
QTableWidget::item { padding: 4px 6px; }

QTabWidget::pane {
    border: 1px solid $border; border-radius: 6px;
    background-color: $bg; top: -1px;
}
QTabBar::tab {
    background-color: $tab_bg; color: $fg_muted;
    border: 1px solid $border; border-bottom: none;
    padding: 8px 18px; margin-right: 2px;
    border-top-left-radius: 6px; border-top-right-radius: 6px;
}
QTabBar::tab:selected {
    background-color: $tab_sel; color: $fg;
    border-bottom: 1px solid $tab_sel;
}
QTabBar::tab:hover:!selected { background-color: $btn_hover; }

QProgressBar {
    border: none; background-color: $progress_bg;
    border-radius: 4px; height: 6px;
}
QProgressBar::chunk { background-color: $progress_chunk; border-radius: 4px; }

QStatusBar {
    background-color: $bg; color: $fg_muted;
    border-top: 1px solid $separator;
}
QStatusBar::item { border: none; }
QStatusBar QLabel { background: transparent; }

QLabel#estado      { color: $fg_muted; padding: 2px 0; }
QLabel#estadoOk    { color: $ok;    font-weight: 600; padding: 2px 0; }
QLabel#estadoError { color: $error; font-weight: 600; padding: 2px 0; }

QLabel#statusInfo {
    color: $fg_muted;
    font-family: "Consolas", "Monaco", monospace;
    font-size: 11px; padding: 2px 4px;
}
QFrame#separador {
    background-color: $separator;
    max-height: 1px; min-height: 1px; border: none;
}
QToolTip { background-color: $bg_card; color: $fg; border: 1px solid $border; padding: 4px; }
""")


def build_qss(tema: str) -> str:
    return QSS_TEMPLATE.substitute(THEMES[tema])


# ===========================================================================
# Ayuda
# ===========================================================================

HELP_HTML = {
    "es": """
<h2>Verificador de Firmas ISO</h2>
<p>Comprueba la autenticidad de tus imágenes ISO mediante <b>GPG</b>,
<b>MD5</b>, <b>SHA-1</b>, <b>SHA-256</b> o <b>SHA-512</b>.</p>
<hr>
<h3>🚀 Verificación rápida</h3>
<p>El botón <b>Verificar TODO (auto)</b> hace todo el trabajo por ti:</p>
<ol>
  <li>Detecta la distribución de la ISO por su nombre.</li>
  <li>Descarga automáticamente el archivo de hashes y la firma GPG (si está disponible).</li>
  <li>Calcula el hash de tu ISO.</li>
  <li>Verifica la firma GPG del archivo de hashes (si es posible).</li>
  <li>Compara el hash calculado con el oficial.</li>
  <li>Muestra un resultado unificado.</li>
</ol>
<hr>
<h3>📘 Guía de compilación</h3>
<p>Pulsa el botón <b>📘 Guía de compilación</b> (o la tecla <b>F2</b>) para
abrir la guía completa sobre cómo generar el <code>.exe</code>, el instalador
con Inno Setup y el paquete <code>.deb</code>.</p>
<hr>
<h3>🔌 Integración con el menú contextual</h3>
<p>Pulsa el botón <b>🔌</b> de la cabecera para añadir
<b>"Verificar con ISO Verifier"</b> al menú de clic derecho.</p>
<ul>
  <li><b>Windows</b>: se registra en <code>HKCU\\Software\\Classes</code>, sin
      necesidad de permisos de administrador.</li>
  <li><b>Linux (KDE)</b>: se añade a los <i>service menus</i> de Dolphin.</li>
</ul>
<p>Al pulsarlo de nuevo, se te ofrecerá <b>desinstalar</b> la integración.</p>
<hr>
<h3>📜 Historial de verificaciones</h3>
<p>Pulsa el botón <b>📜 Historial</b> para ver las últimas 20 verificaciones
realizadas, con fecha, archivo, resultado y hash.</p>
<hr>
<h3>🔎 Autodetección al seleccionar una ISO</h3>
<p>Al seleccionar o arrastrar una ISO, la app intenta descargar
automáticamente el hash y la firma GPG de <b>Ubuntu, Debian, Linux Mint,
CachyOS, Fedora, openSUSE, Arch Linux, Zorin OS, Bazzite, Soplos Linux,
Slackware y BigLinux</b>.</p>
<hr>
<h3>🪟 Verificar una ISO de Windows (hash)</h3>
<ol>
  <li>Abre <a href="https://www.microsoft.com/software-download">microsoft.com/software-download</a>.</li>
  <li>Copia el hash SHA-256 publicado.</li>
  <li>Pégalo en el campo 3 (botón <b>📋 Pegar</b>).</li>
  <li>Pulsa <b>Verificar autenticidad</b>.</li>
</ol>
<h3>⌨️ Atajos</h3>
<table cellpadding="6">
  <tr><td><b>F1</b></td>     <td>Ayuda</td></tr>
  <tr><td><b>F2</b></td>     <td>Guía de compilación</td></tr>
  <tr><td><b>Ctrl+O</b></td> <td>Abrir ISO</td></tr>
  <tr><td><b>Ctrl+T</b></td> <td>Cambiar tema</td></tr>
  <tr><td><b>Ctrl+L</b></td> <td>Cambiar idioma (requiere reinicio)</td></tr>
  <tr><td><b>Ctrl+Q</b></td> <td>Salir</td></tr>
</table>
""",
    "en": """
<h2>ISO Signature Verifier</h2>
<p>Verify the authenticity of your ISO images using <b>GPG</b>,
<b>MD5</b>, <b>SHA-1</b>, <b>SHA-256</b> or <b>SHA-512</b>.</p>
<hr>
<h3>🚀 Quick verification</h3>
<p>The <b>Verify ALL (auto)</b> button does all the work for you:</p>
<ol>
  <li>Detects the distribution from the ISO filename.</li>
  <li>Automatically downloads the hash file and GPG signature (if available).</li>
  <li>Computes the hash of your ISO.</li>
  <li>Verifies the GPG signature of the hash file (if possible).</li>
  <li>Compares the computed hash with the official one.</li>
  <li>Shows a unified result.</li>
</ol>
<hr>
<h3>📘 Compilation guide</h3>
<p>Press the <b>📘 Compilation guide</b> button (or the <b>F2</b> key) to
open the complete guide on how to generate the <code>.exe</code>, the
Inno Setup installer and the <code>.deb</code> package.</p>
<hr>
<h3>🔌 Context menu integration</h3>
<p>Click the <b>🔌</b> button in the header to add
<b>"Verify with ISO Verifier"</b> to the right-click menu.</p>
<ul>
  <li><b>Windows</b>: registers under <code>HKCU\\Software\\Classes</code>, no admin needed.</li>
  <li><b>Linux (KDE)</b>: adds a service menu entry for Dolphin.</li>
</ul>
<p>Clicking again offers to <b>uninstall</b> the integration.</p>
<hr>
<h3>📜 Verification history</h3>
<p>Click the <b>📜 History</b> button to see the last 20 verifications
with date, file, result and hash.</p>
<hr>
<h3>🔎 Auto-detection</h3>
<p>When you select or drop an ISO, the app tries to automatically
download the hash and GPG signature for <b>Ubuntu, Debian, Linux Mint,
CachyOS, Fedora, openSUSE, Arch Linux, Zorin OS, Bazzite, Soplos Linux,
Slackware and BigLinux</b>.</p>
<hr>
<h3>🪟 Verify a Windows ISO (hash)</h3>
<ol>
  <li>Open <a href="https://www.microsoft.com/software-download">microsoft.com/software-download</a>.</li>
  <li>Copy the published SHA-256 hash.</li>
  <li>Paste it in field 3 (button <b>📋 Paste</b>).</li>
  <li>Click <b>Verify authenticity</b>.</li>
</ol>
<h3>⌨️ Shortcuts</h3>
<table cellpadding="6">
  <tr><td><b>F1</b></td>     <td>Help</td></tr>
  <tr><td><b>F2</b></td>     <td>Compilation guide</td></tr>
  <tr><td><b>Ctrl+O</b></td> <td>Open ISO</td></tr>
  <tr><td><b>Ctrl+T</b></td> <td>Toggle theme</td></tr>
  <tr><td><b>Ctrl+L</b></td> <td>Change language (needs restart)</td></tr>
  <tr><td><b>Ctrl+Q</b></td> <td>Quit</td></tr>
</table>
""",
}


# ===========================================================================
# Cálculo de hash, verificación GPG y parseo
# ===========================================================================

def calcular_hash_stream(ruta: str, algoritmo: str = "sha256",
                         progreso_cb=None, cancelado_cb=None) -> str | None:
    if algoritmo not in ALGORITHMS:
        algoritmo = "sha256"
    h = ALGORITHMS[algoritmo]["fn"]()
    total = Path(ruta).stat().st_size
    leido = 0
    with open(ruta, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            if cancelado_cb and cancelado_cb():
                return None
            h.update(chunk)
            leido += len(chunk)
            pct = int(leido * 100 / total) if total else 100
            if progreso_cb:
                progreso_cb(pct, leido, total)
    return h.hexdigest()


def verificar_gpg(iso_path: str, sig_path: str) -> dict:
    iso = Path(iso_path)
    if not iso.is_file():
        return {"valido": False, "mensaje": f"La ISO no existe: {iso}", "detalles": ""}
    gpg = gnupg.GPG()
    gpg.encoding = "utf-8"
    with open(sig_path, "rb") as f_sig:
        v = gpg.verify_file(f_sig, data_filename=iso_path)

    if v.valid:
        return {
            "valido": True,
            "mensaje": ("✅ GPG signature VALID. The ISO is authentic."
                        if _current_lang == "en" else
                        "✅ Firma GPG VÁLIDA. La ISO es auténtica."),
            "detalles": (
                f"Signed by : {v.username or 'Unknown'}\n"
                f"Key       : {v.key_id}\n"
                f"Fingerprint: {v.fingerprint}\n"
                f"Date      : {v.timestamp}\n"
                f"Signature : {sig_path}"
            ),
        }
    return {
        "valido": False,
        "mensaje": ("❌ GPG signature INVALID or unverifiable."
                    if _current_lang == "en" else
                    "❌ Firma GPG INVÁLIDA o no verificable."),
        "detalles": (
            f"GPG status: {v.status}\nSignature : {sig_path}\n\n"
            "Make sure the signer's public key is imported:\n"
            "    gpg --import <keyfile>\n    gpg --list-keys"
            if _current_lang == "en" else
            f"Estado GPG: {v.status}\nFirma     : {sig_path}\n\n"
            "Comprueba que tienes importada la clave pública del firmante:\n"
            "    gpg --import <archivo-de-clave>\n    gpg --list-keys"
        ),
    }


def parse_hash_file(path: str) -> list[tuple[str, str, str]]:
    entradas: list[tuple[str, str, str]] = []
    try:
        contenido = Path(path).read_text(errors="ignore")
    except Exception:
        return entradas
    for linea in contenido.splitlines():
        linea = linea.strip()
        if not linea or linea.startswith("#"):
            continue
        partes = linea.split(None, 1)
        if len(partes) != 2:
            continue
        h, nombre = partes[0].lower().strip(), partes[1].lstrip("*").strip()
        alg = detectar_algoritmo(h)
        if alg:
            entradas.append((h, nombre, alg))
    return entradas


# ===========================================================================
# Historial
# ===========================================================================

class HistorialDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("history_title"))
        self.resize(700, 500)
        self.setMinimumSize(500, 300)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        self.lista = QListWidget()
        layout.addWidget(self.lista, 1)

        fila = QHBoxLayout()
        fila.addStretch()
        btn_clear = QPushButton(tr("history_clear"))
        btn_clear.clicked.connect(self.limpiar_historial)
        fila.addWidget(btn_clear)
        btn_close = QPushButton("Cerrar" if _current_lang == "es" else "Close")
        btn_close.clicked.connect(self.accept)
        fila.addWidget(btn_close)
        layout.addLayout(fila)

        self.cargar_historial()

    def cargar_historial(self):
        settings = QSettings()
        raw = settings.value("history/entries", [])
        if isinstance(raw, str):
            try:
                raw = json.loads(raw)
            except Exception:
                raw = []

        if not raw:
            item = QListWidgetItem(tr("history_empty"))
            item.setFlags(Qt.NoItemFlags)
            self.lista.addItem(item)
            return

        for entry in raw:
            texto = (
                f"[{entry.get('fecha', '')}]  "
                f"{entry.get('archivo', '')}  →  "
                f"{entry.get('resultado', '')}  "
                f"({entry.get('algoritmo', '')}: {entry.get('hash', '')[:16]}…)"
            )
            item = QListWidgetItem(texto)
            if entry.get("resultado") == "✅ Válido":
                item.setForeground(QBrush(QColor(THEMES["light"]["ok"])))
            elif entry.get("resultado") == "❌ Inválido":
                item.setForeground(QBrush(QColor(THEMES["light"]["error"])))
            self.lista.addItem(item)

    def limpiar_historial(self):
        settings = QSettings()
        settings.setValue("history/entries", [])
        settings.sync()
        self.lista.clear()
        item = QListWidgetItem(tr("history_empty"))
        item.setFlags(Qt.NoItemFlags)
        self.lista.addItem(item)
        QMessageBox.information(self, tr("history_title"), tr("history_cleared"))


def guardar_en_historial(archivo: str, resultado: str,
                         hash_val: str, algoritmo: str):
    settings = QSettings()
    raw = settings.value("history/entries", [])
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except Exception:
            raw = []

    entrada = {
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "archivo": Path(archivo).name,
        "resultado": resultado,
        "hash": hash_val or "",
        "algoritmo": algoritmo or "",
    }
    raw.insert(0, entrada)
    raw = raw[:20]
    settings.setValue("history/entries", json.dumps(raw))
    settings.sync()


# ===========================================================================
# Hilos
# ===========================================================================

class VerificadorThread(QThread):
    progreso = Signal(int, str, "qint64", "qint64")
    terminado = Signal(dict)

    def __init__(self, iso_path: str,
                 gpg_sig_path: str | None = None,
                 expected_hash: str | None = None,
                 algoritmo: str = "sha256"):
        super().__init__()
        self.iso_path = iso_path
        self.gpg_sig_path = gpg_sig_path
        self.expected_hash = expected_hash
        self.algoritmo = algoritmo
        self._cancelado = False

    def cancelar(self):
        self._cancelado = True

    def _esta_cancelado(self) -> bool:
        return self._cancelado

    def run(self):
        try:
            resultado = (self._verificar_gpg() if self.gpg_sig_path
                         else self._verificar_hash())
        except Exception as e:
            resultado = {"valido": False,
                         "mensaje": f"Error inesperado: {e}",
                         "detalles": traceback.format_exc()}
        self.terminado.emit(resultado)

    def _verificar_gpg(self) -> dict:
        if self._cancelado:
            return {"valido": False, "mensaje": tr("cancelled"),
                    "detalles": "", "cancelado": True}
        self.progreso.emit(20, "GPG…", 0, 0)
        self.progreso.emit(50, "GPG…", 0, 0)
        r = verificar_gpg(self.iso_path, self.gpg_sig_path)
        self.progreso.emit(100, "", 0, 0)
        return r

    def _verificar_hash(self) -> dict:
        iso = Path(self.iso_path)
        if not iso.is_file():
            return {"valido": False,
                    "mensaje": (f"ISO not found: {iso}" if _current_lang == "en"
                                else f"La ISO no existe: {iso}"),
                    "detalles": ""}
        alg_label = ALGORITHMS[self.algoritmo]["label"]

        def _prog(pct, leido, total):
            self.progreso.emit(max(2, pct),
                               tr("calculating", a=alg_label, p=pct),
                               leido, total)

        calculado = calcular_hash_stream(self.iso_path, self.algoritmo,
                                         _prog, self._esta_cancelado)
        if calculado is None:
            return {"valido": False, "mensaje": tr("cancelled"),
                    "detalles": "", "cancelado": True, "hash": None,
                    "algoritmo": self.algoritmo}
        self.progreso.emit(100, "", 0, 0)

        if not self.expected_hash:
            msg = (f"ℹ️ {alg_label} computed (no reference hash provided)."
                   if _current_lang == "en"
                   else f"ℹ️ {alg_label} calculado (sin hash de referencia).")
            det = (
                f"File   : {iso.name}\n{alg_label} : {calculado}\n\n"
                "To verify authenticity:\n"
                "  1. Open the official manufacturer website.\n"
                f"  2. Copy the {alg_label} hash.\n"
                "  3. Paste it in the hash field and click Verify.\n"
                if _current_lang == "en" else
                f"Archivo : {iso.name}\n{alg_label} : {calculado}\n\n"
                "Para verificar la autenticidad:\n"
                "  1. Abre la web oficial del fabricante.\n"
                f"  2. Copia el {alg_label} publicado.\n"
                "  3. Pégalo en el campo hash y pulsa Verificar."
            )
            return {"valido": True, "mensaje": msg, "detalles": det,
                    "hash": calculado, "algoritmo": self.algoritmo}

        if calculado == self.expected_hash:
            msg = (f"✅ {alg_label} MATCHES. The ISO is authentic."
                   if _current_lang == "en"
                   else f"✅ {alg_label} COINCIDE. La ISO es auténtica.")
            det = (
                f"File      : {iso.name}\nComputed  : {calculado}\nExpected  : {self.expected_hash}"
                if _current_lang == "en" else
                f"Archivo   : {iso.name}\nCalculado : {calculado}\nEsperado  : {self.expected_hash}"
            )
            return {"valido": True, "mensaje": msg, "detalles": det,
                    "hash": calculado, "algoritmo": self.algoritmo}

        msg = (f"❌ {alg_label} DOES NOT MATCH. The ISO may be corrupted or tampered."
               if _current_lang == "en"
               else f"❌ {alg_label} NO COINCIDE. La ISO puede estar corrupta o alterada.")
        det = (
            f"File      : {iso.name}\nComputed  : {calculado}\nExpected  : {self.expected_hash}\n\n"
            "Check that the pasted hash matches the exact same edition and language."
            if _current_lang == "en" else
            f"Archivo   : {iso.name}\nCalculado : {calculado}\nEsperado  : {self.expected_hash}\n\n"
            "Comprueba que el hash pegado corresponde a la misma edición e idioma."
        )
        return {"valido": False, "mensaje": msg, "detalles": det,
                "hash": calculado, "algoritmo": self.algoritmo}


class AutoDetectThread(QThread):
    progreso = Signal(str)
    terminado = Signal(dict, str)

    def __init__(self, iso_path: str):
        super().__init__()
        self.iso_path = iso_path

    def run(self):
        try:
            r = auto_detect_signature(
                self.iso_path,
                progreso_cb=lambda m: self.progreso.emit(m),
            )
        except Exception as e:
            r = {"reconocida": False, "distro": None, "hash": None,
                 "algoritmo": "sha256", "sig_path": None,
                 "error": f"exception: {e}"}
        self.terminado.emit(r, self.iso_path)


class LoteThread(QThread):
    progreso = Signal(int, str, "qint64", "qint64")
    item = Signal(int, dict)
    terminado = Signal(list)

    def __init__(self, entradas: list[tuple[str, str, str]], carpeta: str):
        super().__init__()
        self.entradas = entradas
        self.carpeta = Path(carpeta)
        self._cancelado = False

    def cancelar(self):
        self._cancelado = True

    def _esta_cancelado(self) -> bool:
        return self._cancelado

    def run(self):
        resultados: list[dict] = []
        total = len(self.entradas)
        for idx, (h_esperado, nombre, alg) in enumerate(self.entradas):
            if self._cancelado:
                break
            ruta_iso = self.carpeta / nombre
            label_alg = ALGORITHMS.get(alg, {}).get("label", alg.upper())
            res = {
                "archivo": nombre, "ruta": str(ruta_iso),
                "algoritmo": alg, "esperado": h_esperado,
                "calculado": None, "estado": "pending", "valido": False,
            }
            if not ruta_iso.is_file():
                res["estado"] = "missing"
                resultados.append(res)
                self.item.emit(idx, res)
                self.progreso.emit(
                    int((idx + 1) * 100 / total), f"{nombre} — missing", idx, 100,
                )
                continue

            def _prog(pct, leido, tot, _idx=idx, _n=nombre, _a=label_alg):
                self.progreso.emit(
                    int((_idx * 100 + pct) / total),
                    f"{_n} — {_a} {pct}%", _idx, pct,
                )

            calculado = calcular_hash_stream(str(ruta_iso), alg,
                                             _prog, self._esta_cancelado)
            if calculado is None:
                res["estado"] = "cancelled"
                resultados.append(res)
                self.item.emit(idx, res)
                break

            res["calculado"] = calculado
            if calculado == h_esperado:
                res["estado"] = "ok"
                res["valido"] = True
            else:
                res["estado"] = "fail"
            resultados.append(res)
            self.item.emit(idx, res)

        self.terminado.emit(resultados)


# ===========================================================================
# Splash y diálogos
# ===========================================================================

def crear_splash_pixmap(tema: str, icon_pixmap: QPixmap | None) -> QPixmap:
    w, h = 460, 300
    pix = QPixmap(w, h)
    pix.fill(QColor(0, 0, 0, 0))
    p = QPainter(pix)
    p.setRenderHint(QPainter.Antialiasing)
    p.setRenderHint(QPainter.SmoothPixmapTransform)
    t = THEMES[tema]
    p.setBrush(QColor(t["bg_card"]))
    p.setPen(Qt.NoPen)
    p.drawRoundedRect(0, 0, w, h, 16, 16)
    p.setBrush(Qt.NoBrush)
    p.setPen(QColor(t["border"]))
    p.drawRoundedRect(0, 0, w - 1, h - 1, 16, 16)
    if icon_pixmap and not icon_pixmap.isNull():
        scaled = icon_pixmap.scaled(96, 96, Qt.KeepAspectRatio,
                                    Qt.SmoothTransformation)
        p.drawPixmap((w - scaled.width()) // 2, 34, scaled)
    p.setPen(QColor(t["fg"]))
    p.setFont(QFont("Segoe UI", 16, QFont.Bold))
    p.drawText(QRect(0, 150, w, 30), Qt.AlignCenter, tr("app_title"))
    p.setPen(QColor(t["fg_muted"]))
    p.setFont(QFont("Segoe UI", 10))
    p.drawText(QRect(0, 184, w, 24), Qt.AlignCenter, f"v{APP_VERSION}")
    p.setBrush(QColor(t["progress_bg"]))
    p.setPen(Qt.NoPen)
    bar_w, bar_h = 220, 4
    bar_x = (w - bar_w) // 2
    p.drawRoundedRect(bar_x, 240, bar_w, bar_h, 2, 2)
    p.setBrush(QColor(t["accent"]))
    p.drawRoundedRect(bar_x, 240, int(bar_w * 0.65), bar_h, 2, 2)
    p.end()
    return pix


class AyudaDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("help_title"))
        self.resize(720, 600)
        self.setMinimumSize(520, 400)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        browser = QTextBrowser()
        browser.setOpenExternalLinks(True)
        browser.setHtml(HELP_HTML.get(_current_lang, HELP_HTML["es"]))
        browser.setStyleSheet("font-family: 'Segoe UI', sans-serif; font-size: 13px;")
        layout.addWidget(browser, 1)

        fila = QHBoxLayout()

        # Botón para abrir la guía de compilación
        btn_guia = QPushButton(tr("btn_guide"))
        btn_guia.setToolTip(
            "Abre la guía completa de compilación (.exe, .deb, instalador)"
            if _current_lang == "es" else
            "Opens the complete compilation guide (.exe, .deb, installer)"
        )
        btn_guia.clicked.connect(self.abrir_guia_compilacion)
        fila.addWidget(btn_guia)

        fila.addStretch()

        btn = QPushButton("Cerrar" if _current_lang == "es" else "Close")
        btn.clicked.connect(self.accept)
        btn.setDefault(True)
        fila.addWidget(btn)
        layout.addLayout(fila)

    def abrir_guia_compilacion(self):
        """Abre la guía de compilación en el navegador o visor predeterminado."""
        ruta = buscar_guia_compilacion()
        if ruta is not None:
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(ruta)))
            return
        QMessageBox.information(self,
                                tr("guide_not_found_t"),
                                tr("guide_not_found_m"))


class NoDropLineEdit(QLineEdit):
    def dragEnterEvent(self, event):
        event.ignore()

    def dropEvent(self, event):
        event.ignore()


# ===========================================================================
# Pestaña Individual
# ===========================================================================

class TabIndividual(QWidget):
    estadoCambiado = Signal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._hash_calculado: str | None = None
        self._elapsed = QElapsedTimer()
        self._thread: VerificadorThread | None = None
        self._auto_thread: AutoDetectThread | None = None
        self._ultima_iso_auto = ""

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        self.chk_auto = QCheckBox(tr("chk_auto"))
        self.chk_auto.setChecked(True)
        layout.addWidget(self.chk_auto)

        layout.addWidget(self._label_seccion(tr("sec_iso")))
        fila_iso = QHBoxLayout()
        self.input_iso = NoDropLineEdit()
        self.input_iso.setPlaceholderText(tr("ph_iso"))
        self.input_iso.textChanged.connect(self._on_iso_changed)
        fila_iso.addWidget(self.input_iso, 1)
        btn_iso = QPushButton(tr("btn_browse"))
        btn_iso.clicked.connect(self.seleccionar_iso)
        fila_iso.addWidget(btn_iso)
        layout.addLayout(fila_iso)

        layout.addWidget(self._label_seccion(tr("sec_gpg")))
        fila_gpg = QHBoxLayout()
        self.input_gpg = NoDropLineEdit()
        self.input_gpg.setPlaceholderText(tr("ph_gpg"))
        fila_gpg.addWidget(self.input_gpg, 1)
        btn_gpg = QPushButton(tr("btn_browse"))
        btn_gpg.clicked.connect(self.seleccionar_gpg)
        fila_gpg.addWidget(btn_gpg)
        layout.addLayout(fila_gpg)

        hint_gpg = QLabel(tr("hint_gpg"))
        hint_gpg.setObjectName("hint")
        hint_gpg.setWordWrap(True)
        layout.addWidget(hint_gpg)

        layout.addWidget(self._label_seccion(tr("sec_hash")))
        fila_algo = QHBoxLayout()
        fila_algo.addWidget(QLabel(tr("algo_label")))
        self.combo_algo = QComboBox()
        for key, info in ALGORITHMS.items():
            self.combo_algo.addItem(info["label"], key)
        self.combo_algo.setCurrentIndex(2)
        self.combo_algo.currentIndexChanged.connect(self._on_algo_changed)
        fila_algo.addWidget(self.combo_algo)
        fila_algo.addStretch(1)
        layout.addLayout(fila_algo)

        fila_hash = QHBoxLayout()
        self.input_hash = NoDropLineEdit()
        self.input_hash.setPlaceholderText(tr("ph_hash"))
        self.input_hash.textChanged.connect(self._validar_hash_en_vivo)
        fila_hash.addWidget(self.input_hash, 1)

        btn_pegar = QPushButton(tr("btn_paste"))
        btn_pegar.clicked.connect(self.pegar_hash)
        fila_hash.addWidget(btn_pegar)

        btn_web = QPushButton(tr("btn_web"))
        btn_web.clicked.connect(
            lambda: QDesktopServices.openUrl(
                QUrl("https://www.microsoft.com/software-download")
            )
        )
        fila_hash.addWidget(btn_web)
        layout.addLayout(fila_hash)

        hint_hash = QLabel(tr("hint_hash"))
        hint_hash.setObjectName("hint")
        hint_hash.setWordWrap(True)
        layout.addWidget(hint_hash)

        fila_botones = QHBoxLayout()
        fila_botones.setSpacing(8)
        self.btn_verificar = QPushButton(tr("btn_verify"))
        self.btn_verificar.setObjectName("btnVerificar")
        self.btn_verificar.setCursor(Qt.PointingHandCursor)
        self.btn_verificar.clicked.connect(self.verificar)
        fila_botones.addWidget(self.btn_verificar, 1)

        self.btn_verificar_todo = QPushButton(tr("btn_verify_all"))
        self.btn_verificar_todo.setObjectName("btnVerificar")
        self.btn_verificar_todo.setCursor(Qt.PointingHandCursor)
        self.btn_verificar_todo.clicked.connect(self.verificar_todo)
        fila_botones.addWidget(self.btn_verificar_todo, 1)

        self.btn_cancelar = QPushButton(tr("btn_cancel"))
        self.btn_cancelar.setObjectName("btnCancelar")
        self.btn_cancelar.setCursor(Qt.PointingHandCursor)
        self.btn_cancelar.setEnabled(False)
        self.btn_cancelar.setVisible(False)
        self.btn_cancelar.clicked.connect(self.cancelar_verificacion)
        fila_botones.addWidget(self.btn_cancelar, 0)
        layout.addLayout(fila_botones)

        self.progreso = QProgressBar()
        self.progreso.setRange(0, 100)
        self.progreso.setValue(0)
        self.progreso.setTextVisible(False)
        layout.addWidget(self.progreso)

        fila_res = QHBoxLayout()
        fila_res.addWidget(self._label_seccion(tr("label_result")), 1)
        self.btn_copiar_hash = QPushButton(tr("btn_copy_hash"))
        self.btn_copiar_hash.setEnabled(False)
        self.btn_copiar_hash.clicked.connect(self.copiar_hash)
        fila_res.addWidget(self.btn_copiar_hash, 0)
        layout.addLayout(fila_res)

        self.resultado = QTextEdit()
        self.resultado.setReadOnly(True)
        self.resultado.setMinimumHeight(120)
        layout.addWidget(self.resultado, 1)

    def _label_seccion(self, texto: str) -> QLabel:
        lbl = QLabel(texto)
        lbl.setObjectName("seccion")
        return lbl

    def set_estado(self, texto: str, tipo: str = "normal"):
        self.estadoCambiado.emit(texto, tipo)

    def seleccionar_iso(self):
        settings = QSettings()
        inicio = settings.value("paths/last_iso_dir", str(Path.home()), type=str)
        ruta, _ = QFileDialog.getOpenFileName(
            self, tr("sec_iso"), inicio,
            "ISO (*.iso *.img);;All files (*)",
        )
        if ruta:
            self.input_iso.setText(ruta)
            settings.setValue("paths/last_iso_dir", str(Path(ruta).parent))

    def seleccionar_gpg(self):
        settings = QSettings()
        inicio = settings.value("paths/last_gpg_dir", str(Path.home()), type=str)
        ruta, _ = QFileDialog.getOpenFileName(
            self, tr("sec_gpg"), inicio,
            "GPG (*.sig *.asc *.gpg *.sign);;All files (*)",
        )
        if ruta:
            self.input_gpg.setText(ruta)
            settings.setValue("paths/last_gpg_dir", str(Path(ruta).parent))

    def _on_iso_changed(self, texto: str):
        texto = texto.strip()
        if texto and Path(texto).is_file():
            size = Path(texto).stat().st_size
            self.set_estado(tr("status_file", n=Path(texto).name,
                               s=fmt_size(size)), "ok")
            if self.chk_auto.isChecked():
                self._disparar_autodeteccion(texto)

    def _disparar_autodeteccion(self, iso_path: str):
        if iso_path == self._ultima_iso_auto:
            return
        self._ultima_iso_auto = iso_path
        if self._auto_thread and self._auto_thread.isRunning():
            return
        nombre = Path(iso_path).name
        self.set_estado(tr("auto_detecting", n=nombre), "normal")
        self._auto_thread = AutoDetectThread(iso_path)
        self._auto_thread.progreso.connect(lambda m: self.set_estado(m, "normal"))
        self._auto_thread.terminado.connect(self._on_auto_detect_done)
        self._auto_thread.start()

    def _on_auto_detect_done(self, resultado: dict, iso_path: str):
        if self.input_iso.text().strip() != iso_path:
            return
        distro = resultado.get("distro") or "distro"
        if not resultado.get("reconocida"):
            if resultado.get("error") == "network":
                self.set_estado(tr("auto_error_net", d=distro), "error")
            else:
                self.set_estado(tr("auto_not_detected"), "normal")
            return
        if resultado.get("error") == "network":
            self.set_estado(tr("auto_error_net", d=distro), "error")
            return
        if resultado.get("error") == "not_listed":
            self.set_estado(tr("auto_no_entry", d=distro), "error")
            return
        h = resultado.get("hash")
        alg = resultado.get("algoritmo", "sha256")
        if h:
            idx = self.combo_algo.findData(alg)
            if idx >= 0:
                self.combo_algo.blockSignals(True)
                self.combo_algo.setCurrentIndex(idx)
                self.combo_algo.blockSignals(False)
            self.input_hash.setText(h)
        sig = resultado.get("sig_path")
        if sig:
            self.input_gpg.setText(sig)
        msgs = []
        if h:
            msgs.append(tr("auto_hash_ok", a=alg.upper()))
        if sig:
            msgs.append(tr("auto_gpg_ok"))
        if msgs:
            self.set_estado(" · ".join(msgs), "ok")

    def _algoritmo_actual(self) -> str:
        return self.combo_algo.currentData() or "sha256"

    def _on_algo_changed(self, _idx):
        self._validar_hash_en_vivo(self.input_hash.text())

    def _validar_hash_en_vivo(self, texto: str):
        texto = texto.strip()
        alg = self._algoritmo_actual()
        if not texto:
            self.input_hash.setObjectName("")
        elif es_hash_valido(texto, alg):
            self.input_hash.setObjectName("hashValido")
        else:
            self.input_hash.setObjectName("hashInvalido")
        self.input_hash.style().polish(self.input_hash)

    def pegar_hash(self):
        texto = QApplication.clipboard().text()
        if not texto.strip():
            self.set_estado(tr("clipboard_empty"), "error")
            return
        limpio = texto.strip()
        alg_detectado = detectar_algoritmo(limpio)
        if alg_detectado:
            idx = self.combo_algo.findData(alg_detectado)
            if idx >= 0 and idx != self.combo_algo.currentIndex():
                self.combo_algo.blockSignals(True)
                self.combo_algo.setCurrentIndex(idx)
                self.combo_algo.blockSignals(False)
        h = extraer_hash(texto, self._algoritmo_actual())
        if h:
            self.input_hash.setText(h)
            self.set_estado(tr("hash_pasted"), "ok")
        else:
            self.input_hash.setText(texto.strip())
            self.set_estado(tr("not_a_hash"), "error")

    def copiar_hash(self):
        if not self._hash_calculado:
            self.set_estado(tr("no_hash_yet"), "error")
            return
        QApplication.clipboard().setText(self._hash_calculado)
        self.set_estado(tr("hash_copied"), "ok")

    def manejar_drop(self, ruta: str) -> bool:
        ext = Path(ruta).suffix.lower()
        if ext in (".iso", ".img"):
            self.input_iso.setText(ruta)
            self.set_estado(tr("iso_loaded", n=Path(ruta).name), "ok")
            return True
        if ext in (".sig", ".asc", ".gpg", ".sign"):
            self.input_gpg.setText(ruta)
            self.set_estado(tr("sig_loaded", n=Path(ruta).name), "ok")
            return True
        if ext in (".txt", ".sha256", ".sha512", ".md5", ".sha1"):
            try:
                contenido = Path(ruta).read_text(errors="ignore")
                h = extraer_hash(contenido)
                if h:
                    alg = detectar_algoritmo(h)
                    if alg:
                        idx = self.combo_algo.findData(alg)
                        if idx >= 0:
                            self.combo_algo.setCurrentIndex(idx)
                    self.input_hash.setText(h)
                    self.set_estado(tr("hash_extracted", n=Path(ruta).name), "ok")
                else:
                    self.set_estado(tr("no_file", n=Path(ruta).name), "error")
            except Exception as e:
                self.set_estado(f"{e}", "error")
            return True
        return False

    def verificar(self):
        iso = self.input_iso.text().strip()
        gpg = self.input_gpg.text().strip()
        hash_texto = self.input_hash.text().strip()
        alg = self._algoritmo_actual()

        if not iso:
            QMessageBox.warning(self, tr("warn_no_iso"), tr("warn_no_iso_txt"))
            return
        if not Path(iso).is_file():
            QMessageBox.warning(self, tr("warn_iso_notfound"),
                                tr("warn_iso_notfound_txt", p=iso))
            return

        expected_hash = None
        if hash_texto:
            expected_hash = extraer_hash(hash_texto, alg)
            if expected_hash is None:
                QMessageBox.warning(self, tr("warn_hash_bad"),
                                    tr("warn_hash_bad_txt"))

        if gpg:
            modo = "GPG"
            gpg_param, hash_param = gpg, None
        else:
            modo = f"{ALGORITHMS[alg]['label']}"
            gpg_param, hash_param = None, expected_hash

        self._iniciar_hilo(iso, gpg_param, hash_param, alg, modo)

    def verificar_todo(self):
        iso = self.input_iso.text().strip()
        if not iso or not Path(iso).is_file():
            QMessageBox.warning(self, tr("warn_no_iso"), tr("warn_no_iso_txt"))
            return

        self.set_estado(tr("auto_detecting", n=Path(iso).name), "normal")
        self._ultima_iso_auto = ""
        auto_result = auto_detect_signature(iso)

        if not auto_result.get("reconocida") or auto_result.get("error"):
            if auto_result.get("error") == "network":
                self.set_estado(tr("auto_error_net",
                                   d=auto_result.get("distro", "desconocida")),
                                "error")
            else:
                self.set_estado(tr("auto_not_detected"), "error")
            QMessageBox.information(
                self, "Autodetección no disponible",
                "No se reconoció la distribución de esta ISO, por lo que no "
                "se puede descargar automáticamente el hash oficial.\n\n"
                "Puedes:\n"
                "  · Copiar el hash desde la web oficial y pegarlo en el campo 3.\n"
                "  · O descargar la firma .sig y ponerla en el campo 2.\n\n"
                "Si quieres solo el hash de la ISO (para comparar manualmente), "
                "pulsa 'Verificar autenticidad' sin rellenar los campos 2 ni 3."
            )
            return

        h = auto_result.get("hash")
        sig_path = auto_result.get("sig_path")
        alg = auto_result.get("algoritmo", "sha256")

        if h:
            self.combo_algo.setCurrentIndex(self.combo_algo.findData(alg))
            self.input_hash.setText(h)
        if sig_path:
            self.input_gpg.setText(sig_path)

        self.verificar()

    def _iniciar_hilo(self, iso, gpg_param, hash_param, alg, modo):
        self._hash_calculado = None
        self.btn_copiar_hash.setEnabled(False)
        self.btn_verificar.setEnabled(False)
        self.btn_verificar_todo.setEnabled(False)
        self.btn_cancelar.setEnabled(True)
        self.btn_cancelar.setVisible(True)
        self.progreso.setValue(0)
        self.resultado.clear()
        self.set_estado(tr("starting", m=modo))
        self._elapsed.start()

        self._thread = VerificadorThread(iso, gpg_param, hash_param, alg)
        self._thread.progreso.connect(self._on_progreso)
        self._thread.terminado.connect(self._on_terminado)
        self._thread.start()

    def cancelar_verificacion(self):
        if self._thread and self._thread.isRunning():
            self._thread.cancelar()
            self.set_estado(tr("cancelling"), "error")
            self.btn_cancelar.setEnabled(False)
            self.btn_verificar_todo.setEnabled(True)

    def _on_progreso(self, pct: int, msg: str, leido: int, total: int):
        self.progreso.setValue(pct)
        if msg:
            self.set_estado(msg)
        if total > 0 and self._elapsed.isValid():
            elapsed_s = max(self._elapsed.elapsed() / 1000, 0.05)
            bps = leido / elapsed_s
            eta_str = "--:--"
            if 0 < pct < 100:
                eta_str = fmt_time(elapsed_s * (100 - pct) / pct)
            self.set_estado(tr("status_progress",
                               l=fmt_size(leido), t=fmt_size(total),
                               e=fmt_time(elapsed_s), v=fmt_speed(bps),
                               eta=eta_str))

    def _on_terminado(self, resultado: dict):
        self.btn_verificar.setEnabled(True)
        self.btn_verificar_todo.setEnabled(True)
        self.btn_cancelar.setEnabled(False)
        self.btn_cancelar.setVisible(False)
        self.progreso.setValue(0 if resultado.get("cancelado") else 100)

        if resultado.get("cancelado"):
            self.set_estado(tr("cancelled"), "error")
        elif resultado["valido"]:
            self.set_estado(tr("verify_ok"), "ok")
        else:
            self.set_estado(tr("verify_fail"), "error")

        h = resultado.get("hash")
        if h:
            self._hash_calculado = h
            self.btn_copiar_hash.setEnabled(True)

        # Guardar en historial
        iso_path = self.input_iso.text().strip()
        resultado_str = "✅ Válido" if resultado["valido"] else "❌ Inválido"
        guardar_en_historial(iso_path, resultado_str, h or "",
                             resultado.get("algoritmo", ""))

        self.resultado.setPlainText(
            f"{resultado['mensaje']}\n\n{resultado['detalles']}"
        )


# ===========================================================================
# Pestaña En lote
# ===========================================================================

class TabLote(QWidget):
    estadoCambiado = Signal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._thread: LoteThread | None = None
        self._entradas: list[tuple[str, str, str]] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        layout.addWidget(self._label_seccion(tr("batch_sums")))
        fila_sums = QHBoxLayout()
        self.input_sums = NoDropLineEdit()
        self.input_sums.setPlaceholderText(tr("ph_sums"))
        fila_sums.addWidget(self.input_sums, 1)
        btn_sums = QPushButton(tr("btn_browse"))
        btn_sums.clicked.connect(self.seleccionar_sums)
        fila_sums.addWidget(btn_sums)
        layout.addLayout(fila_sums)

        layout.addWidget(self._label_seccion(tr("batch_dir")))
        fila_dir = QHBoxLayout()
        self.input_dir = NoDropLineEdit()
        self.input_dir.setPlaceholderText(tr("ph_dir"))
        fila_dir.addWidget(self.input_dir, 1)
        btn_dir = QPushButton(tr("btn_browse"))
        btn_dir.clicked.connect(self.seleccionar_dir)
        fila_dir.addWidget(btn_dir)
        layout.addLayout(fila_dir)

        fila_botones = QHBoxLayout()
        fila_botones.setSpacing(8)
        self.btn_verificar = QPushButton(tr("btn_start_batch"))
        self.btn_verificar.setObjectName("btnVerificar")
        self.btn_verificar.setCursor(Qt.PointingHandCursor)
        self.btn_verificar.clicked.connect(self.verificar_lote)
        fila_botones.addWidget(self.btn_verificar, 1)

        self.btn_cancelar = QPushButton(tr("btn_cancel"))
        self.btn_cancelar.setObjectName("btnCancelar")
        self.btn_cancelar.setCursor(Qt.PointingHandCursor)
        self.btn_cancelar.setEnabled(False)
        self.btn_cancelar.setVisible(False)
        self.btn_cancelar.clicked.connect(self.cancelar_lote)
        fila_botones.addWidget(self.btn_cancelar, 0)
        layout.addLayout(fila_botones)

        self.progreso = QProgressBar()
        self.progreso.setRange(0, 100)
        self.progreso.setValue(0)
        self.progreso.setTextVisible(False)
        layout.addWidget(self.progreso)

        self.tabla = QTableWidget(0, 4)
        self.tabla.setHorizontalHeaderLabels(tr("batch_table_cols"))
        self.tabla.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabla.verticalHeader().setVisible(False)
        hh = self.tabla.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.Stretch)
        hh.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        layout.addWidget(self.tabla, 1)

        self.lbl_resumen = QLabel("")
        self.lbl_resumen.setObjectName("hint")
        layout.addWidget(self.lbl_resumen)

    def _label_seccion(self, texto: str) -> QLabel:
        lbl = QLabel(texto)
        lbl.setObjectName("seccion")
        return lbl

    def set_estado(self, texto: str, tipo: str = "normal"):
        self.estadoCambiado.emit(texto, tipo)

    def seleccionar_sums(self):
        ruta, _ = QFileDialog.getOpenFileName(
            self, tr("batch_sums"), str(Path.home()),
            "Hash files (*SUMS *.txt *.sha256 *.md5 *.sha1 *.sha512);;All files (*)",
        )
        if ruta:
            self.input_sums.setText(ruta)
            try:
                self._entradas = parse_hash_file(ruta)
                n = len(self._entradas)
                self.lbl_resumen.setText(f"{n} entries")
                self._poblar_tabla_pendiente()
            except Exception as e:
                self.set_estado(str(e), "error")

    def seleccionar_dir(self):
        ruta = QFileDialog.getExistingDirectory(
            self, tr("batch_dir"), str(Path.home()),
        )
        if ruta:
            self.input_dir.setText(ruta)

    def _poblar_tabla_pendiente(self):
        self.tabla.setRowCount(0)
        for h, nombre, alg in self._entradas:
            fila = self.tabla.rowCount()
            self.tabla.insertRow(fila)
            self.tabla.setItem(fila, 0, QTableWidgetItem(nombre))
            self.tabla.setItem(fila, 1, QTableWidgetItem("…"))
            self.tabla.setItem(fila, 2, QTableWidgetItem(""))
            self.tabla.setItem(fila, 3, QTableWidgetItem(h[:16] + "…"))

    def manejar_drop(self, ruta: str) -> bool:
        ext = Path(ruta).suffix.lower()
        if ext in (".txt",) or "SUMS" in Path(ruta).name.upper():
            self.input_sums.setText(ruta)
            try:
                self._entradas = parse_hash_file(ruta)
                self._poblar_tabla_pendiente()
            except Exception:
                pass
            return True
        if Path(ruta).is_dir():
            self.input_dir.setText(ruta)
            return True
        return False

    def verificar_lote(self):
        sums = self.input_sums.text().strip()
        carpeta = self.input_dir.text().strip()

        if not sums or not Path(sums).is_file():
            QMessageBox.warning(self, tr("batch_sums"),
                                tr("warn_iso_notfound_txt", p=sums))
            return
        if not carpeta or not Path(carpeta).is_dir():
            QMessageBox.warning(self, tr("batch_dir"), tr("batch_no_dir"))
            return

        self._entradas = parse_hash_file(sums)
        if not self._entradas:
            QMessageBox.warning(self, tr("batch_sums"), tr("batch_none"))
            return

        self._poblar_tabla_pendiente()
        self.btn_verificar.setEnabled(False)
        self.btn_cancelar.setEnabled(True)
        self.btn_cancelar.setVisible(True)
        self.progreso.setValue(0)
        self.lbl_resumen.setText("")
        self.set_estado(tr("starting", m="Batch"))

        self._thread = LoteThread(self._entradas, carpeta)
        self._thread.progreso.connect(self._on_progreso)
        self._thread.item.connect(self._on_item)
        self._thread.terminado.connect(self._on_terminado)
        self._thread.start()

    def cancelar_lote(self):
        if self._thread and self._thread.isRunning():
            self._thread.cancelar()
            self.set_estado(tr("cancelling"), "error")
            self.btn_cancelar.setEnabled(False)

    def _on_progreso(self, pct: int, msg: str, idx: int, _pct_item: int):
        self.progreso.setValue(pct)
        if msg:
            self.set_estado(msg)

    def _on_item(self, idx: int, res: dict):
        if idx >= self.tabla.rowCount():
            return
        estado = res["estado"]
        tema = QSettings().value("ui/theme", "light")
        if estado == "ok":
            txt, color = "✅ OK", THEMES[tema]["row_ok"]
        elif estado == "fail":
            txt, color = "❌ FAIL", THEMES[tema]["row_err"]
        elif estado == "missing":
            txt, color = "⚠️ MISSING", THEMES[tema]["row_warn"]
        elif estado == "cancelled":
            txt, color = "⏹", THEMES[tema]["row_warn"]
        else:
            txt, color = "…", None
        self.tabla.setItem(idx, 1, QTableWidgetItem(txt))
        if res.get("calculado"):
            self.tabla.setItem(idx, 2, QTableWidgetItem(res["calculado"][:16] + "…"))
        if color:
            for col in range(4):
                it = self.tabla.item(idx, col)
                if it:
                    it.setBackground(QBrush(QColor(color)))

    def _on_terminado(self, resultados: list[dict]):
        self.btn_verificar.setEnabled(True)
        self.btn_cancelar.setEnabled(False)
        self.btn_cancelar.setVisible(False)
        self.progreso.setValue(100)

        ok = sum(1 for r in resultados if r["estado"] == "ok")
        fail = sum(1 for r in resultados if r["estado"] == "fail")
        missing = sum(1 for r in resultados if r["estado"] == "missing")
        total = len(resultados)

        self.lbl_resumen.setText(
            tr("batch_summary", ok=ok, fail=fail, missing=missing, total=total)
        )
        if any(r["estado"] == "cancelled" for r in resultados):
            self.set_estado(tr("batch_cancelled"), "error")
        elif fail == 0 and missing == 0:
            self.set_estado(tr("batch_done"), "ok")
        else:
            self.set_estado(tr("batch_done"), "error")

        for r in resultados:
            res_str = "✅ Válido" if r["valido"] else "❌ Inválido"
            guardar_en_historial(r["archivo"], res_str,
                                 r.get("calculado", ""), r.get("algoritmo", ""))


# ===========================================================================
# Ventana principal
# ===========================================================================

class IsoVerifierWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(tr("app_title"))
        self.setMinimumSize(760, 540)
        self.resize(880, 720)
        self.setAcceptDrops(True)

        icon_path = resource_path("assets/icon.png")
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

        self.settings = QSettings()
        self.tema_actual = self.settings.value("ui/theme", "light", type=str)
        if self.tema_actual not in THEMES:
            self.tema_actual = "light"

        self._construir_ui()
        self._construir_status_bar()
        self._construir_atajos()
        self._restaurar_geometria()
        self._aplicar_tema()

    def _construir_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        outer = QVBoxLayout(central)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        outer.addWidget(scroll)

        content = QWidget()
        scroll.setWidget(content)
        layout = QVBoxLayout(content)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(10)

        cabecera = QHBoxLayout()
        cabecera.setSpacing(8)
        col_titulos = QVBoxLayout()
        col_titulos.setSpacing(2)
        titulo = QLabel(tr("app_title"))
        titulo.setObjectName("titulo")
        col_titulos.addWidget(titulo)
        subtitulo = QLabel(tr("subtitle", v=APP_VERSION))
        subtitulo.setObjectName("subtitulo")
        col_titulos.addWidget(subtitulo)
        cabecera.addLayout(col_titulos, 1)

        self.btn_ayuda = QPushButton(tr("btn_help"))
        self.btn_ayuda.clicked.connect(self.mostrar_ayuda)
        cabecera.addWidget(self.btn_ayuda, 0, Qt.AlignTop)

        self.btn_historial = QPushButton(tr("btn_history"))
        self.btn_historial.clicked.connect(self.mostrar_historial)
        cabecera.addWidget(self.btn_historial, 0, Qt.AlignTop)

        self.btn_integrar = QPushButton("🔌")
        self.btn_integrar.setToolTip(
            "Integrar/desintegrar del menú contextual "
            "(Integrate/uninstall from context menu)"
        )
        self.btn_integrar.clicked.connect(self.integrar_menu_contextual)
        cabecera.addWidget(self.btn_integrar, 0, Qt.AlignTop)

        self.btn_lang = QPushButton(tr("btn_lang"))
        self.btn_lang.setToolTip("Switch language / Cambiar idioma")
        self.btn_lang.clicked.connect(self.cambiar_idioma)
        cabecera.addWidget(self.btn_lang, 0, Qt.AlignTop)

        self.btn_tema = QPushButton(tr("btn_theme"))
        self.btn_tema.clicked.connect(self.cambiar_tema)
        cabecera.addWidget(self.btn_tema, 0, Qt.AlignTop)

        self.btn_salir = QPushButton(tr("btn_exit"))
        self.btn_salir.clicked.connect(self.close)
        cabecera.addWidget(self.btn_salir, 0, Qt.AlignTop)

        layout.addLayout(cabecera)

        self.tabs = QTabWidget()
        self.tab_individual = TabIndividual()
        self.tab_individual.estadoCambiado.connect(self._set_estado)
        self.tab_lote = TabLote()
        self.tab_lote.estadoCambiado.connect(self._set_estado)

        auto_guardado = self.settings.value("ui/auto_detect", True, type=bool)
        self.tab_individual.chk_auto.setChecked(auto_guardado)
        self.tab_individual.chk_auto.toggled.connect(
            lambda v: self.settings.setValue("ui/auto_detect", v)
        )

        self.tabs.addTab(self.tab_individual, tr("tab_single"))
        self.tabs.addTab(self.tab_lote, tr("tab_batch"))
        layout.addWidget(self.tabs, 1)

    def _construir_status_bar(self):
        sb = self.statusBar()
        sb.setSizeGripEnabled(False)
        self.status_msg = QLabel(tr("ready"))
        self.status_msg.setObjectName("estado")
        sb.addWidget(self.status_msg, 1)
        self.status_info = QLabel("")
        self.status_info.setObjectName("statusInfo")
        sb.addPermanentWidget(self.status_info)

    def _construir_atajos(self):
        QShortcut(QKeySequence("F1"),     self, self.mostrar_ayuda)
        QShortcut(QKeySequence("F2"),     self, self._abrir_guia_directo)
        QShortcut(QKeySequence("Ctrl+T"), self, self.cambiar_tema)
        QShortcut(QKeySequence("Ctrl+L"), self, self.cambiar_idioma)
        QShortcut(QKeySequence("Ctrl+Q"), self, self.close)
        QShortcut(QKeySequence("Ctrl+O"), self, self.tab_individual.seleccionar_iso)
        QShortcut(QKeySequence("Esc"),    self, self._atajo_escape)

    def _atajo_escape(self):
        if self.tab_individual._thread and self.tab_individual._thread.isRunning():
            self.tab_individual.cancelar_verificacion()
        if self.tab_lote._thread and self.tab_lote._thread.isRunning():
            self.tab_lote.cancelar_lote()

    def _abrir_guia_directo(self):
        """Atajo F2: abre directamente la guía de compilación."""
        ruta = buscar_guia_compilacion()
        if ruta is not None:
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(ruta)))
        else:
            self._set_estado(tr("guide_not_found_t"), "error")

    def _restaurar_geometria(self):
        geo = self.settings.value("ui/geometry")
        if geo:
            try:
                self.restoreGeometry(geo if isinstance(geo, QByteArray)
                                     else QByteArray(geo))
                screens = QGuiApplication.screens()
                visible = any(
                    s.availableGeometry().intersects(self.frameGeometry())
                    for s in screens
                )
                if not visible:
                    self.resize(880, 720)
                    self.move(100, 60)
            except Exception:
                pass

    def closeEvent(self, event):
        self.settings.setValue("ui/geometry", self.saveGeometry())
        self.settings.setValue("ui/theme", self.tema_actual)
        self.settings.sync()
        super().closeEvent(event)

    def _aplicar_tema(self):
        QApplication.instance().setStyleSheet(build_qss(self.tema_actual))
        self.tab_individual._validar_hash_en_vivo(
            self.tab_individual.input_hash.text()
        )
        icono = "☀️" if self.tema_actual == "dark" else "🌓"
        self.btn_tema.setText(f"{icono}")

    def cambiar_tema(self):
        self.tema_actual = "dark" if self.tema_actual == "light" else "light"
        self._aplicar_tema()
        self.settings.setValue("ui/theme", self.tema_actual)

    def cambiar_idioma(self):
        nuevo = "en" if _current_lang == "es" else "es"
        self.settings.setValue("ui/lang", nuevo)
        QMessageBox.information(self, tr("lang_changed_t"),
                                tr("lang_changed_m"))

    def _set_estado(self, texto: str, tipo: str = "normal"):
        self.status_msg.setText(texto)
        if tipo == "ok":
            self.status_msg.setObjectName("estadoOk")
        elif tipo == "error":
            self.status_msg.setObjectName("estadoError")
        else:
            self.status_msg.setObjectName("estado")
        self.status_msg.style().polish(self.status_msg)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if not urls:
            return
        for url in urls:
            ruta = url.toLocalFile()
            if not ruta:
                continue
            ext = Path(ruta).suffix.lower()
            if ext in (".iso", ".img", ".sig", ".asc", ".gpg", ".sign"):
                self.tabs.setCurrentIndex(0)
                self.tab_individual.manejar_drop(ruta)
            else:
                self.tabs.setCurrentIndex(1)
                if not self.tab_lote.manejar_drop(ruta):
                    self.tab_individual.manejar_drop(ruta)
        event.acceptProposedAction()

    def mostrar_ayuda(self):
        AyudaDialog(self).exec()

    def mostrar_historial(self):
        HistorialDialog(self).exec()

    # ------------------------------------------------------------------
    # Carga de archivo externo (menú contextual / línea de comandos)
    # ------------------------------------------------------------------
    def cargar_archivo_externo(self, ruta: str):
        p = Path(ruta)
        if not p.is_file():
            self._set_estado(f"Archivo no encontrado: {ruta}", "error")
            return
        ext = p.suffix.lower()
        if ext in (".iso", ".img"):
            self.tabs.setCurrentIndex(0)
            self.tab_individual.input_iso.setText(str(p))
        elif ext in (".sig", ".asc", ".gpg", ".sign"):
            self.tabs.setCurrentIndex(0)
            self.tab_individual.input_gpg.setText(str(p))
        elif ext in (".txt", ".sha256", ".sha512", ".md5", ".sha1"):
            self.tabs.setCurrentIndex(1)
            self.tab_lote.manejar_drop(str(p))
        else:
            self._set_estado(f"Extensión no reconocida: {ext}", "error")

    # ------------------------------------------------------------------
    # Integración con el menú contextual
    # ------------------------------------------------------------------
    def integrar_menu_contextual(self):
        sistema = platform.system()

        if sistema == "Windows":
            ya_instalado = False
            try:
                import winreg
                with winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER,
                    r"Software\Classes\*\shell\ISO_Verifier",
                ):
                    ya_instalado = True
            except (FileNotFoundError, ImportError):
                pass

            if ya_instalado:
                r = QMessageBox.question(
                    self, "Integración existente",
                    "La opción ya está instalada en el menú contextual.\n\n"
                    "¿Quieres DESINSTALARLA?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No,
                )
                if r == QMessageBox.Yes:
                    self._desintegrar_windows()
            else:
                self._integrar_windows()

        elif sistema == "Linux":
            self._integrar_linux()
        else:
            QMessageBox.information(
                self, "Integración",
                "La integración con el menú contextual solo está disponible "
                "en Windows y Linux por ahora.",
            )

    def _integrar_windows(self):
        import winreg

        if getattr(sys, "frozen", False):
            comando = f'"{sys.executable}" "%1"'
        else:
            python_exe = Path(sys.executable).resolve()
            script_py = Path(sys.argv[0]).resolve()
            comando = f'"{python_exe}" "{script_py}" "%1"'

        exe_icono = str(Path(sys.executable).resolve())

        try:
            base_key = r"Software\Classes\*\shell\ISO_Verifier"
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, base_key) as k:
                winreg.SetValueEx(k, "", 0, winreg.REG_SZ,
                                  "Verificar con ISO Verifier")
                winreg.SetValueEx(k, "Icon", 0, winreg.REG_SZ, exe_icono)

            with winreg.CreateKey(winreg.HKEY_CURRENT_USER,
                                  base_key + r"\command") as k:
                winreg.SetValueEx(k, "", 0, winreg.REG_SZ, comando)

            ext_key = (r"Software\Classes\SystemFileAssociations\.iso"
                       r"\shell\ISO_Verifier")
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, ext_key) as k:
                winreg.SetValueEx(k, "", 0, winreg.REG_SZ,
                                  "Verificar con ISO Verifier")
                winreg.SetValueEx(k, "Icon", 0, winreg.REG_SZ, exe_icono)

            with winreg.CreateKey(winreg.HKEY_CURRENT_USER,
                                  ext_key + r"\command") as k:
                winreg.SetValueEx(k, "", 0, winreg.REG_SZ, comando)

            QMessageBox.information(
                self, "Integración completada",
                "✅ Se ha añadido 'Verificar con ISO Verifier' al menú contextual.\n\n"
                "· Clic derecho sobre cualquier archivo → Verificar con ISO Verifier\n"
                "· Clic derecho sobre un .iso → Verificar con ISO Verifier\n\n"
                "No es necesario reiniciar ni ejecutar como administrador.\n\n"
                "Puedes desinstalarlo con el mismo botón 🔌.",
            )
        except PermissionError as e:
            QMessageBox.critical(
                self, "Permisos insuficientes",
                f"No se pudo escribir en el registro:\n{e}\n\n"
                "Prueba cerrando la app y abriéndola de nuevo.",
            )
        except Exception as e:
            QMessageBox.critical(
                self, "Error de integración",
                f"Error inesperado:\n{e}\n\n{traceback.format_exc()}",
            )

    def _desintegrar_windows(self):
        import winreg

        claves = [
            r"Software\Classes\*\shell\ISO_Verifier",
            r"Software\Classes\SystemFileAssociations\.iso\shell\ISO_Verifier",
        ]

        eliminadas = 0
        for clave in claves:
            try:
                try:
                    winreg.DeleteKey(winreg.HKEY_CURRENT_USER,
                                     clave + r"\command")
                except FileNotFoundError:
                    pass
                winreg.DeleteKey(winreg.HKEY_CURRENT_USER, clave)
                eliminadas += 1
            except FileNotFoundError:
                pass
            except OSError as e:
                QMessageBox.warning(
                    self, "Error al desinstalar",
                    f"No se pudo eliminar {clave}:\n{e}",
                )
                return

        if eliminadas > 0:
            QMessageBox.information(
                self, "Desinstalación completada",
                f"✅ Se han eliminado {eliminadas} entradas del menú contextual.",
            )
        else:
            QMessageBox.information(
                self, "Nada que eliminar",
                "No se encontraron entradas previas en el registro.",
            )

    def _integrar_linux(self):
        service_dir = Path.home() / ".local/share/kio/servicemenus"
        service_dir.mkdir(parents=True, exist_ok=True)

        icono = resource_path("assets/icon.png")
        desktop_content = f"""[Desktop Entry]
Type=Service
ServiceTypes=KonqPopupMenu/Plugin
MimeType=application/x-iso9660-image;
Actions=VerifyISO;

[Desktop Action VerifyISO]
Name=Verificar con ISO Verifier
Icon={icono}
Exec={sys.executable} {Path(sys.argv[0]).resolve()} %f
"""
        desktop_file = service_dir / "iso-verifier.desktop"
        desktop_file.write_text(desktop_content)

        QMessageBox.information(
            self, "Integración completada",
            "Se ha añadido la opción 'Verificar con ISO Verifier' "
            "al menú contextual de KDE Plasma (Dolphin).",
        )


# ===========================================================================
# CLI
# ===========================================================================

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="iso_verifier",
        description="Verificador de firmas ISO (GUI por defecto, CLI con --cli).",
    )
    p.add_argument("--cli", action="store_true")
    p.add_argument("--no-splash", action="store_true")
    p.add_argument("--iso", help="Ruta a la ISO (modo individual).")
    p.add_argument("--gpg", help="Ruta a la firma GPG (.sig/.asc/.gpg).")
    p.add_argument("--hash", help="Hash esperado.")
    p.add_argument("--algoritmo", "-a",
                   choices=list(ALGORITHMS.keys()) + ["auto"],
                   default="auto")
    p.add_argument("--auto", action="store_true",
                   help="Intentar descargar firma/hash automáticamente.")
    p.add_argument("--lote", help="Archivo de hashes (SHA256SUMS, MD5SUMS…).")
    p.add_argument("--carpeta", help="Carpeta con las ISOs (junto a --lote).")
    p.add_argument("--json", action="store_true")
    p.add_argument("--quiet", "-q", action="store_true")
    p.add_argument("--lang", choices=["es", "en"], default=None)
    p.add_argument("archivo", nargs="?", default=None,
                   help="Archivo a cargar al abrir la GUI (ISO, firma o hash).")
    return p


def run_cli(args) -> int:
    if args.lang:
        set_language(args.lang)

    def log(msg: str):
        if not args.quiet:
            print(msg, file=sys.stderr)

    # ---------------- Lote
    if args.lote:
        if not args.carpeta:
            print("ERROR: --lote requiere --carpeta", file=sys.stderr)
            return 2
        entradas = parse_hash_file(args.lote)
        if not entradas:
            print("ERROR: no valid entries in hash file", file=sys.stderr)
            return 2
        carpeta = Path(args.carpeta)
        if not carpeta.is_dir():
            print(f"ERROR: folder not found: {carpeta}", file=sys.stderr)
            return 2

        resultados = []
        for h, nombre, alg in entradas:
            ruta = carpeta / nombre
            if not ruta.is_file():
                resultados.append({"archivo": nombre, "algoritmo": alg,
                                   "esperado": h, "calculado": None,
                                   "estado": "missing", "valido": False})
                log(f"  ⚠️ {nombre}: missing")
                continue
            log(f"  · {nombre} ({alg})")
            calculado = calcular_hash_stream(str(ruta), alg)
            valido = (calculado == h)
            resultados.append({"archivo": nombre, "algoritmo": alg,
                               "esperado": h, "calculado": calculado,
                               "estado": "ok" if valido else "fail",
                               "valido": valido})
        n_ok = sum(1 for r in resultados if r["estado"] == "ok")
        n_fail = sum(1 for r in resultados if r["estado"] == "fail")
        n_miss = sum(1 for r in resultados if r["estado"] == "missing")
        if args.json:
            print(json.dumps({"total": len(resultados), "ok": n_ok,
                              "fail": n_fail, "missing": n_miss,
                              "resultados": resultados},
                             indent=2, ensure_ascii=False))
        else:
            print(f"\n{n_ok} OK · {n_fail} FAIL · {n_miss} MISSING · {len(resultados)} total")
        return 0 if n_fail == 0 and n_miss == 0 else 1

    # ---------------- Individual
    if not args.iso:
        print("ERROR: --cli requires --iso or --lote", file=sys.stderr)
        return 2
    if not Path(args.iso).is_file():
        print(f"ERROR: ISO not found: {args.iso}", file=sys.stderr)
        return 2

    gpg_path = args.gpg
    hash_esperado = args.hash
    algoritmo = args.algoritmo

    if args.auto and not args.gpg:
        log("Auto-detecting signature/hash…")
        auto = auto_detect_signature(
            args.iso,
            progreso_cb=lambda m: log(f"  {m}"),
        )
        if auto.get("hash") and not hash_esperado:
            hash_esperado = auto["hash"]
            algoritmo = auto["algoritmo"]
            log(f"  → Hash {algoritmo.upper()} encontrado: {hash_esperado[:16]}…")
        if auto.get("sig_path") and not gpg_path:
            gpg_path = auto["sig_path"]
            log(f"  → Firma GPG descargada: {gpg_path}")

    if gpg_path:
        log(f"Verifying GPG signature of {Path(args.iso).name}…")
        resultado = verificar_gpg(args.iso, gpg_path)
        resultado["hash"] = None
        resultado["algoritmo"] = None
    else:
        alg = algoritmo
        if alg == "auto":
            alg = detectar_algoritmo(hash_esperado) or "sha256"
            log(f"Auto-detected algorithm: {alg}")
        ultimo = [0]

        def _prog(pct, leido, total):
            if args.quiet:
                return
            if pct >= ultimo[0] + 5 or pct == 100:
                print(f"  {ALGORITHMS[alg]['label']}… {pct}%", file=sys.stderr)
                ultimo[0] = pct

        log(f"Computing {ALGORITHMS[alg]['label']} of {Path(args.iso).name}…")
        calculado = calcular_hash_stream(args.iso, alg, progreso_cb=_prog)
        if calculado is None:
            print("Cancelled.", file=sys.stderr)
            return 2
        esperado = extraer_hash(hash_esperado, alg) if hash_esperado else None
        if esperado is None:
            resultado = {
                "valido": True,
                "mensaje": f"{ALGORITHMS[alg]['label']} computed (no reference).",
                "detalles": f"File : {Path(args.iso).name}\n{alg}: {calculado}",
                "hash": calculado, "algoritmo": alg,
            }
        elif calculado == esperado:
            resultado = {
                "valido": True,
                "mensaje": f"✅ {ALGORITHMS[alg]['label']} MATCHES.",
                "detalles": (f"File      : {Path(args.iso).name}\n"
                             f"Computed  : {calculado}\nExpected  : {esperado}"),
                "hash": calculado, "algoritmo": alg,
            }
        else:
            resultado = {
                "valido": False,
                "mensaje": f"❌ {ALGORITHMS[alg]['label']} DOES NOT MATCH.",
                "detalles": (f"File      : {Path(args.iso).name}\n"
                             f"Computed  : {calculado}\nExpected  : {esperado}"),
                "hash": calculado, "algoritmo": alg,
            }

    if args.json:
        print(json.dumps({
            "iso": str(Path(args.iso).resolve()),
            "algoritmo": resultado.get("algoritmo"),
            "valido": resultado["valido"],
            "mensaje": resultado["mensaje"],
            "detalles": resultado["detalles"],
            "hash": resultado.get("hash"),
        }, indent=2, ensure_ascii=False))
    else:
        print()
        print(resultado["mensaje"])
        if resultado["detalles"]:
            print()
            print(resultado["detalles"])

    return 0 if resultado["valido"] else 1


# ===========================================================================
# GUI
# ===========================================================================

def run_gui(show_splash: bool = True,
            archivo_inicial: str | None = None) -> int:
    app = QApplication(sys.argv)
    app.setOrganizationName("IsoVerifier")
    app.setApplicationName("IsoVerifier")
    app.setFont(QFont("Segoe UI", 10))

    settings = QSettings()
    lang = settings.value("ui/lang", "es", type=str)
    set_language(lang)

    icon_path = resource_path("assets/icon.png")
    app_icon = QIcon(str(icon_path)) if icon_path.exists() else QIcon()
    if not app_icon.isNull():
        app.setWindowIcon(app_icon)

    splash = None
    if show_splash and not archivo_inicial:
        tema = settings.value("ui/theme", "light", type=str)
        if tema not in THEMES:
            tema = "light"
        icon_pix = app_icon.pixmap(96, 96) if not app_icon.isNull() else QPixmap()
        splash_pix = crear_splash_pixmap(tema, icon_pix)
        splash = QSplashScreen(splash_pix, Qt.WindowStaysOnTopHint)
        splash.setAttribute(Qt.WA_TranslucentBackground)
        splash.show()
        app.processEvents()

    ventana = IsoVerifierWindow()
    ventana.show()

    if archivo_inicial:
        ventana.cargar_archivo_externo(archivo_inicial)

    if splash:
        QTimer.singleShot(1400, lambda: splash.finish(ventana))

    return app.exec()


# ===========================================================================
# Main
# ===========================================================================

def main():
    parser = build_parser()
    args, _ = parser.parse_known_args()
    if args.cli:
        sys.exit(run_cli(args))
    else:
        sys.exit(run_gui(show_splash=not args.no_splash,
                         archivo_inicial=args.archivo))


if __name__ == "__main__":
    main()
