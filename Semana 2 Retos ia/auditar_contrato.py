import yaml
import inspect
import importlib.util
import sys

# ==========================================
# CONFIGURACIÓN
# ==========================================
ARCHIVO_OPENAPI = "openapi.yaml"
ARCHIVO_CLIENTE = "cliente_ecomarket.py"
MODULO_CLIENTE = "cliente_ecomarket"

# Mapeo manual: Endpoint OpenAPI -> Tu función Python
# (Esto conecta el contrato con tu código)
MAPEO_FUNCIONES = {
    "listar_productos": "listar_productos",
    "crear_producto": "crear_producto",
    "obtener_producto": "obtener_producto",
    "actualizar_producto_parcial": "actualizar_producto_parcial",
    "eliminar_producto": "eliminar_producto"
}

def cargar_cliente():
    """Carga tu archivo cliente_ecomarket.py dinámicamente"""
    try:
        spec = importlib.util.spec_from_file_location(MODULO_CLIENTE, ARCHIVO_CLIENTE)
        modulo = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(modulo)
        return modulo
    except FileNotFoundError:
        print(f"❌ Error: No se encuentra el archivo {ARCHIVO_CLIENTE}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error al importar tu cliente: {e}")
        sys.exit(1)

def auditar():
    print(f"--- 🕵️ INICIANDO AUDITORÍA DE CONTRATO ({ARCHIVO_OPENAPI}) ---")
    
    # 1. Cargar Contrato
    try:
        with open(ARCHIVO_OPENAPI, 'r') as f:
            contrato = yaml.safe_load(f)
    except FileNotFoundError:
        print(f"❌ Error: Falta el archivo {ARCHIVO_OPENAPI}")
        return

    # 2. Cargar Cliente
    cliente = cargar_cliente()
    funciones_cliente = dict(inspect.getmembers(cliente, inspect.isfunction))

    total_checks = 0
    total_passed = 0

    print(f"\n{'MÉTODO':<8} {'ENDPOINT':<25} {'FUNCIÓN ESPERADA':<30} {'ESTADO'}")
    print("-" * 80)

    # 3. Recorrer el contrato y validar
    paths = contrato.get('paths', {})
    for path, methods in paths.items():
        for method, specs in methods.items():
            operation_id = specs.get('operationId')
            nombre_funcion = MAPEO_FUNCIONES.get(operation_id)
            
            method_str = method.upper()
            
            if not nombre_funcion:
                print(f"{method_str:<8} {path:<25} {'(No mapeada)':<30} ⚠️ SKIP")
                continue

            total_checks += 1
            
            # VERIFICACIÓN: ¿Existe la función en tu archivo?
            if nombre_funcion in funciones_cliente:
                print(f"{method_str:<8} {path:<25} {nombre_funcion:<30} ✅ CUMPLE")
                total_passed += 1
            else:
                print(f"{method_str:<8} {path:<25} {nombre_funcion:<30} ❌ FALTANTE")

    print("-" * 80)
    
    # 4. Resultado Final
    score = (total_passed / total_checks) * 100 if total_checks > 0 else 0
    print(f"\n📊 RESULTADO FINAL: {score:.0f}% de Conformidad")
    
    if score == 100:
        print("🎉 ¡Excelente! Tu cliente cumple con la estructura del contrato OpenAPI.")
    else:
        print("⚠️ Hay funciones faltantes o mal nombradas. Revisa la tabla anterior.")

if __name__ == "__main__":
    auditar()