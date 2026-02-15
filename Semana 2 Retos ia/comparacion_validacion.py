import time
import json
from pydantic import BaseModel, ValidationError, PositiveFloat
from jsonschema import validate, ValidationError as SchemaError

# ==========================================
# DATOS DE PRUEBA
# ==========================================
producto_valido = {
    "id": 1,
    "nombre": "Manzanas Gala",
    "precio": 35.50,
    "categoria": "frutas",
    "disponible": True
}

# Producto con error (precio negativo) para probar mensajes
producto_invalido = {
    "id": 1,
    "nombre": "Manzanas Gala",
    "precio": -10.0, 
    "categoria": "frutas",
    "disponible": True
}

# ==========================================
# ESTRATEGIA 1: Validación Manual (Tu código actual)
# ==========================================
def validar_manual(data):
    # Verificamos tipos
    if not isinstance(data.get('id'), int):
        raise ValueError("El campo 'id' debe ser un entero")
    if not isinstance(data.get('nombre'), str):
        raise ValueError("El campo 'nombre' debe ser texto")
    if not isinstance(data.get('precio'), (int, float)):
        raise ValueError("El campo 'precio' debe ser numérico")
    
    # Verificamos lógica de negocio
    if data['precio'] <= 0:
        raise ValueError("El precio debe ser mayor a 0")
    
    categorias_validas = ['frutas', 'verduras', 'lacteos']
    if data.get('categoria') not in categorias_validas:
        raise ValueError(f"Categoría inválida. Opciones: {categorias_validas}")
    
    return True

# ==========================================
# ESTRATEGIA 2: Pydantic (Estándar moderno)
# ==========================================
class ProductoModel(BaseModel):
    id: int
    nombre: str
    precio: PositiveFloat  # Valida automáticamente que sea > 0
    categoria: str
    disponible: bool

def validar_pydantic(data):
    try:
        ProductoModel(**data)
        return True
    except ValidationError as e:
        raise e

# ==========================================
# ESTRATEGIA 3: JSON Schema (Estándar web)
# ==========================================
schema_producto = {
    "type": "object",
    "properties": {
        "id": {"type": "integer"},
        "nombre": {"type": "string"},
        "precio": {"type": "number", "exclusiveMinimum": 0},
        "categoria": {"type": "string", "enum": ["frutas", "verduras", "lacteos"]},
        "disponible": {"type": "boolean"}
    },
    "required": ["id", "nombre", "precio", "categoria"]
}

def validar_jsonschema(data):
    validate(instance=data, schema=schema_producto)
    return True

# ==========================================
# ⏱️ BENCHMARK (Prueba de velocidad)
# ==========================================
def correr_benchmark():
    iteraciones = 10000  # Validaremos 10,000 veces
    print(f"--- 🏁 INICIANDO BENCHMARK ({iteraciones} iteraciones) ---")

    # 1. Test Manual
    inicio = time.time()
    for _ in range(iteraciones):
        validar_manual(producto_valido)
    fin = time.time()
    tiempo_manual = fin - inicio
    print(f"1. Manual (if/else): {tiempo_manual:.4f} segundos")

    # 2. Test Pydantic
    inicio = time.time()
    for _ in range(iteraciones):
        validar_pydantic(producto_valido)
    fin = time.time()
    tiempo_pydantic = fin - inicio
    print(f"2. Pydantic:        {tiempo_pydantic:.4f} segundos")

    # 3. Test JSON Schema
    inicio = time.time()
    for _ in range(iteraciones):
        validar_jsonschema(producto_valido)
    fin = time.time()
    tiempo_schema = fin - inicio
    print(f"3. JSON Schema:     {tiempo_schema:.4f} segundos")

    print("\n--- 📢 COMPARACIÓN DE MENSAJES DE ERROR ---")
    
    print("\n[Manual] Error:")
    try: validar_manual(producto_invalido)
    except ValueError as e: print(f"  ❌ {e}")

    print("\n[Pydantic] Error:")
    try: validar_pydantic(producto_invalido)
    except ValidationError as e: 
        # Pydantic devuelve errores detallados, mostramos el primero
        print(f"  ❌ {e.errors()[0]['msg']} (Campo: {e.errors()[0]['loc']})")

    print("\n[JSON Schema] Error:")
    try: validar_jsonschema(producto_invalido)
    except SchemaError as e: print(f"  ❌ {e.message}")

if __name__ == "__main__":
    correr_benchmark()