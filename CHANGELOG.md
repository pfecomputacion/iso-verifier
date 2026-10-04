# Changelog

Todos los cambios relevantes de este proyecto se documentan en este archivo.

El formato sigue [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/)
y el proyecto se adhiere a [Versionado Semántico](https://semver.org/lang/es/).

## [No publicado]

### Por añadir
- Verificación en lote de múltiples ISOs
- Historial de verificaciones
- Soporte para MD5, SHA-1 y SHA-512

## [1.1.0] - 2026-09-24

### Añadido
- Icono propio (escudo con check) en formato PNG e ICO multiresolución.
- Splash screen al arrancar, con tema adaptado al tema activo.
- Barra de estado enriquecida: tamaño de archivo, velocidad (MB/s),
  tiempo transcurrido y ETA durante el cálculo de SHA-256.
- Flag `--no-splash` para lanzar la app sin splash.
- Flag `--quiet` / `-q` para el modo CLI.

### Cambiado
- La barra de estado sustituye al antiguo QLabel de estado inferior.
- `install_deps.py` ahora instala Pillow y prescinde de vibegui.
- `build_installers.py` incluye el icono en el .exe y en el .deb.
- El splash y el icono se cargan vía `resource_path()` (compatible con PyInstaller --onefile).

## [1.0.0] - 2026-09-20

### Añadido
- GUI con PySide6 (Qt6) y temas claro/oscuro.
- Verificación GPG de firmas .sig, .asc y .gpg.
- Cálculo de SHA-256 con progreso.
- Modo CLI (--cli) con salida JSON y códigos de retorno.
- Drag & drop de archivos a la ventana.
- Persistencia de configuración con QSettings (tema, geometría, rutas).
- Botones de Ayuda (F1), Tema (Ctrl+T) y Salir (Ctrl+Q).
- Cancelación de verificaciones en curso (Esc).
- Copia del hash calculado al portapapeles.
- Pegado inteligente del hash desde el portapapeles.
- Generación de instaladores .deb (vía debx) y .exe (vía Inno Setup).

### Corregido
- La ventana ya no se sale de pantalla en monitores pequeños (usa QScrollArea).

---

[No publicado]: https://github.com/tu-usuario/iso-verifier/compare/v1.1.0...HEAD
[1.1.0]: https://github.com/tu-usuario/iso-verifier/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/tu-usuario/iso-verifier/releases/tag/v1.0.0
