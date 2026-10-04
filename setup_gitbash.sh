#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# setup_gitbash.sh
# Configura el entorno de desarrollo para el verificador de firmas ISO
# desde Git Bash en Windows (o cualquier bash en Linux/macOS).
#
# Es idempotente: si .venv ya existe, no lo recrea.
# ---------------------------------------------------------------------------

set -e  # abortar si algo falla

VENV_DIR=".venv"
PYTHON_BIN=""

# ---------------------------------------------------------------------------
# Colores para que se vea bonito
# ---------------------------------------------------------------------------
GREEN="\033[0;32m"
YELLOW="\033[1;33m"
RED="\033[0;31m"
CYAN="\033[0;36m"
NC="\033[0m"  # sin color

info()  { echo -e "${CYAN}ℹ️  $1${NC}"; }
ok()    { echo -e "${GREEN}✅ $1${NC}"; }
warn()  { echo -e "${YELLOW}⚠️  $1${NC}"; }
error() { echo -e "${RED}❌ $1${NC}"; }

# ---------------------------------------------------------------------------
# 1. Detectar intérprete de Python disponible
# ---------------------------------------------------------------------------
detect_python() {
    for cmd in python python3 py; do
        if command -v "$cmd" >/dev/null 2>&1; then
            # Verificar que realmente funcione
            if "$cmd" --version >/dev/null 2>&1; then
                PYTHON_BIN="$cmd"
                return 0
            fi
        fi
    done
    return 1
}

# ---------------------------------------------------------------------------
# 2. Detectar ruta de activación del venv según plataforma
# ---------------------------------------------------------------------------
get_activate_path() {
    if [ -f "$VENV_DIR/Scripts/activate" ]; then
        echo "$VENV_DIR/Scripts/activate"      # Windows
    elif [ -f "$VENV_DIR/bin/activate" ]; then
        echo "$VENV_DIR/bin/activate"          # Linux/macOS
    else
        echo ""
    fi
}

# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------
echo "======================================================================"
echo "  Configuración del entorno – Verificador de Firmas ISO"
echo "======================================================================"

# --- Paso 1: ¿existe ya el venv? ------------------------------------------
if [ -d "$VENV_DIR" ]; then
    ACTIVATE_PATH=$(get_activate_path)
    if [ -n "$ACTIVATE_PATH" ]; then
        ok "El entorno virtual '$VENV_DIR' ya existe. Se reutilizará."
    else
        warn "El directorio '$VENV_DIR' existe pero está corrupto o incompleto."
        warn "Se eliminará y se volverá a crear."
        rm -rf "$VENV_DIR"
    fi
fi

# --- Paso 2: crear el venv si no existe -----------------------------------
if [ ! -d "$VENV_DIR" ]; then
    if ! detect_python; then
        error "No se encontró ningún intérprete de Python (python, python3, py)."
        error "Instala Python 3.10+ y vuelve a intentarlo."
        exit 1
    fi

    info "Usando intérprete: $PYTHON_BIN ($($PYTHON_BIN --version))"
    info "Creando entorno virtual en '$VENV_DIR'…"
    "$PYTHON_BIN" -m venv "$VENV_DIR"
    ok "Entorno virtual creado."
fi

# --- Paso 3: activar el venv ----------------------------------------------
ACTIVATE_PATH=$(get_activate_path)
if [ -z "$ACTIVATE_PATH" ]; then
    error "No se encontró el script de activación en '$VENV_DIR'."
    exit 1
fi

info "Activando entorno: source $ACTIVATE_PATH"
# shellcheck disable=SC1090
source "$ACTIVATE_PATH"

# --- Paso 4: comprobar que estamos dentro del venv ------------------------
if [[ "$VIRTUAL_ENV" != *"$VENV_DIR"* ]]; then
    error "La activación falló. VIRTUAL_ENV='$VIRTUAL_ENV'"
    exit 1
fi
ok "Entorno activo: $VIRTUAL_ENV"

# --- Paso 5: actualizar pip -----------------------------------------------
info "Actualizando pip, setuptools y wheel…"
python -m pip install --upgrade pip setuptools wheel --quiet
ok "pip actualizado ($(python -m pip --version))"

# --- Paso 6: instalar dependencias del proyecto ---------------------------
if [ -f "install_deps.py" ]; then
    info "Ejecutando install_deps.py…"
    python install_deps.py
else
    warn "No se encontró install_deps.py. Instalando dependencias mínimas…"
    python -m pip install "vibegui[qt,gtk]" python-gnupg pyinstaller --quiet
fi

# --- Paso 7: verificación final -------------------------------------------
info "Verificando que los módulos clave se importan correctamente…"
if python -c "import gnupg, vibegui" 2>/dev/null; then
    ok "Los módulos 'gnupg' y 'vibegui' se importan sin problemas."
else
    warn "Algún módulo no se pudo importar. Revisa la salida anterior."
fi

# ---------------------------------------------------------------------------
# Resumen final
# ---------------------------------------------------------------------------
echo
echo "======================================================================"
ok "Entorno listo."
echo "======================================================================"
echo
echo "  Para usar la aplicación:"
echo "    python iso_verifier.py                 # backend autodetectado"
echo "    python iso_verifier.py --backend qt    # forzar Qt6"
echo "    python iso_verifier.py --backend gtk   # forzar GTK4"
echo
echo "  Para generar instaladores:"
echo "    python build_installers.py"
echo
echo "  Para salir del entorno:"
echo "    deactivate"
echo