import json
from datetime import datetime

# --- CONFIGURACIÓN ---
CATEGORIAS_VALIDAS = ["frutas", "verduras", "lacteos", "miel", "conservas"]

def validar_producto_ecomarket(data):
    """
    Valida un objeto JSON de producto según las reglas de negocio de EcoMarket.
    Retorna una tupla: (EsValido: bool, Mensaje: str)
    """
    try:
        # 1. Validar Campos Requeridos (Nivel Raíz)
        campos_requeridos = ["id", "nombre", "precio", "categoria", "productor", "disponible", "creado_en"]
        for campo in campos_requeridos:
            if campo not in data:
                return False, f"Error: Falta campo requerido '{campo}'"

        # 2. Seguridad: Detectar campos no permitidos (Tu caso extra)
        # Esto previene inyección de datos basura o intentos de admin hack
        campos_extra = set(data.keys()) - set(campos_requeridos)
        if campos_extra:
            return False, f"Seguridad: Se detectaron campos desconocidos/no permitidos: {campos_extra}"

        # 3. Validar Tipos de Datos Básicos
        if not isinstance(data["id"], int):
            return False, "Error: El 'id' debe ser un número entero."
        
        if not isinstance(data["nombre"], str) or not data["nombre"].strip():
            return False, "Error: El 'nombre' debe ser texto no vacío."

        if not isinstance(data["precio"], (int, float)):
            return False, "Error: El 'precio' debe ser numérico."
            
        if not isinstance(data["disponible"], bool):
            return False, "Error: El campo 'disponible' debe ser booleano."

        # 4. Validar Lógica de Negocio (Precio positivo)
        if data["precio"] <= 0:
            return False, "Error: El 'precio' debe ser mayor a 0."

        # 5. Validar Categoría (Enum)
        if data["categoria"] not in CATEGORIAS_VALIDAS:
            return False, f"Error: Categoría inválida. Permitidas: {CATEGORIAS_VALIDAS}"

        # 6. Validar Objeto Anidado (Productor)
        productor = data["productor"]
        if not isinstance(productor, dict):
             return False, "Error: El campo 'productor' debe ser un objeto JSON."
        
        if "id" not in productor or "nombre" not in productor:
            return False, "Error: El 'productor' debe tener claves 'id' y 'nombre'."
        
        if not isinstance(productor["id"], int):
             return False, "Error: El ID del productor debe ser entero."

        # 7. Validar Fecha (Formato ISO 8601)
        try:
            # Reemplazamos Z por +00:00 para compatibilidad con versiones viejas de Python
            fecha_str = data["creado_en"].replace('Z', '+00:00')
            datetime.fromisoformat(fecha_str)
        except ValueError:
            return False, "Error: La fecha no cumple el formato ISO 8601 (YYYY-MM-DDTHH:MM:SSZ)."

        return True, "Validación Exitosa"

    except Exception as e:
        return False, f"Excepción no controlada: {str(e)}"

# --- BATERÍA DE PRUEBAS (CASOS DE CAOS) ---

if __name__ == "__main__":
    # JSON Base (Válido)
    json_valido = {
        "id": 42,
        "nombre": "Miel orgánica",
        "precio": 150.00,
        "categoria": "miel",
        "productor": { "id": 7, "nombre": "Apiarios del Valle" },
        "disponible": True,
        "creado_en": "2024-01-15T10:30:00Z"
    }

    # Los 6 Casos de Prueba
    casos_prueba = [
        {
            "desc": "Caso 1: Precio Negativo",
            "json": {**json_valido, "precio": -50.00}
        },
        {
            "desc": "Caso 2: Tipo Incorrecto (SQL Injection simulado en ID)",
            "json": {**json_valido, "id": "42 OR 1=1"} 
        },
        {
            "desc": "Caso 3: Categoría Inexistente",
            "json": {**json_valido, "categoria": "electronica"}
        },
        {
            "desc": "Caso 4: Objeto Anidado Incompleto",
            "json": {**json_valido, "productor": {"nombre": "Solo Nombre"}} 
        },
        {
            "desc": "Caso 5: Fecha Malformada",
            "json": {**json_valido, "creado_en": "15/01/2024"} 
        },
        {
            "desc": "Caso 6 (MI CASO PROPIO): Inyección de Campos Extra",
            "json": {**json_valido, "es_admin": True, "borrar_bd": True} 
        }
    ]

    print(f"{'='*20} REPORTE DE VALIDACIÓN {'='*20}\n")
    
    # 1. Prueba de éxito
    ok, msg = validar_producto_ecomarket(json_valido)
    print(f"🔵 JSON Válido:\n   -> {msg}\n")

    # 2. Ejecución de casos de error
    for i, caso in enumerate(casos_prueba, 1):
        es_valido, mensaje = validar_producto_ecomarket(caso["json"])
        resultado = "✅ RECHAZADO CORRECTAMENTE" if not es_valido else "❌ ERROR: FUE ACEPTADO"
        print(f"🔸 {caso['desc']}:")
        print(f"   Respuesta del Validador: {mensaje}")
        print(f"   Estado: {resultado}\n")

    print(f"{'='*60}")