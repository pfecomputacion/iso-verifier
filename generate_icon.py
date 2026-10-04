#!/usr/bin/env python3
"""
Genera los iconos de la aplicación (PNG + ICO) con Pillow.

Uso:
    python generate_icon.py
"""

from pathlib import Path

try:
    from PIL import Image, ImageDraw
except ImportError:
    print("ERROR: instala Pillow con:  python -m pip install Pillow")
    raise SystemExit(1)


def create_icon(size: int) -> Image.Image:
    """Dibuja un escudo con un check blanco dentro."""
    # Renderizamos en alta resolución y reducimos con LANCZOS
    # para obtener bordes suaves (antialiasing).
    scale = 4
    S = size * scale
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # ---------- Escudo exterior (verde oscuro)
    shield_outer = [
        (S * 0.50, S * 0.05),   # punta superior central
        (S * 0.92, S * 0.18),   # esquina sup. derecha
        (S * 0.92, S * 0.55),   # costado derecho
        (S * 0.50, S * 0.95),   # punta inferior
        (S * 0.08, S * 0.55),   # costado izquierdo
        (S * 0.08, S * 0.18),   # esquina sup. izquierda
    ]
    draw.polygon(shield_outer, fill=(30, 132, 73, 255))

    # ---------- Escudo interior (verde más claro, para dar profundidad)
    shield_inner = [
        (S * 0.50, S * 0.13),
        (S * 0.84, S * 0.24),
        (S * 0.84, S * 0.53),
        (S * 0.50, S * 0.87),
        (S * 0.16, S * 0.53),
        (S * 0.16, S * 0.24),
    ]
    draw.polygon(shield_inner, fill=(46, 204, 113, 255))

    # ---------- Check blanco grueso
    p1 = (S * 0.30, S * 0.53)
    p2 = (S * 0.44, S * 0.66)
    p3 = (S * 0.72, S * 0.38)
    grosor = int(S * 0.11)

    draw.line([p1, p2], fill=(255, 255, 255, 255), width=grosor)
    draw.line([p2, p3], fill=(255, 255, 255, 255), width=grosor)

    # Extremos redondeados del check
    r = grosor // 2
    for (x, y) in (p1, p2, p3):
        draw.ellipse([x - r, y - r, x + r, y + r], fill=(255, 255, 255, 255))

    # Reducimos al tamaño final
    return img.resize((size, size), Image.LANCZOS)


def main():
    assets = Path("assets")
    assets.mkdir(exist_ok=True)

    # PNG principal (Linux, macOS, splash)
    create_icon(512).save(assets / "icon.png", "PNG")
    print(f"  · {assets/'icon.png'}")

    # PNG secundario (para .deb, 256x256)
    icon_256 = create_icon(256)
    icon_256.save(assets / "icon_256.png", "PNG")
    print(f"  · {assets/'icon_256.png'}")

    # ICO multi-resolución para Windows
    icon_256.save(
        assets / "icon.ico",
        format="ICO",
        sizes=[(16, 16), (24, 24), (32, 32), (48, 48),
               (64, 64), (128, 128), (256, 256)],
    )
    print(f"  · {assets/'icon.ico'}")

    print("\n✅ Iconos generados en ./assets/")


if __name__ == "__main__":
    main()