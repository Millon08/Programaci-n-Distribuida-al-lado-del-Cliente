import requests


BASE_URL =  "https://retos-ia.free.beeceptor.com" 

# --- EXCEPCIONES PERSONALIZADAS ---
class EcoMarketError(Exception):
    """Clase base para errores de la API EcoMarket"""
    pass

class ProductoNoEncontrado(EcoMarketError):
    """Se lanza cuando el recurso devuelve 404"""
    pass

class ConflictoError(EcoMarketError):
    """Se lanza cuando hay duplicados (409)"""
    pass

# --- FUNCIONES EXISTENTES (Lectura) ---

def listar_productos():
    """Obtiene la lista de todos los productos."""
    try:
        response = requests.get(f"{BASE_URL}/productos")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise EcoMarketError(f"Error al listar productos: {e}")

def obtener_producto(producto_id: int):
    """Obtiene un producto por su ID."""
    response = requests.get(f"{BASE_URL}/productos/{producto_id}")
    if response.status_code == 404:
        raise ProductoNoEncontrado(f"Producto {producto_id} no encontrado")
    if response.status_code != 200:
        raise EcoMarketError(f"Error desconocido: {response.status_code}")
    return response.json()

# --- NUEVAS FUNCIONES (Escritura - Reto 3) ---

def crear_producto(datos: dict) -> dict:
    """
    Crea un nuevo producto en el sistema.
    Endpoint: POST /productos
    """
    url = f"{BASE_URL}/productos"
    # requests.post con parametro 'json' añade automáticamente el header Content-Type: application/json
    response = requests.post(url, json=datos)

    if response.status_code == 201:
        return response.json()
    elif response.status_code == 409:
        raise ConflictoError("Error 409: El producto ya existe.")
    else:
        # Lanza error para 400, 500, etc.
        raise EcoMarketError(f"Error al crear: {response.status_code} - {response.text}")

def actualizar_producto_total(producto_id: int, datos: dict) -> dict:
    """
    Reemplaza COMPLETAMENTE un recurso existente.
    Endpoint: PUT /productos/{id}
    """
    url = f"{BASE_URL}/productos/{producto_id}"
    response = requests.put(url, json=datos)

    if response.status_code == 200:
        return response.json()
    elif response.status_code == 404:
        raise ProductoNoEncontrado(f"No se puede actualizar. ID {producto_id} no existe.")
    else:
        raise EcoMarketError(f"Error en PUT: {response.status_code}")

def actualizar_producto_parcial(producto_id: int, campos: dict) -> dict:
    """
    Actualiza SOLO los campos enviados.
    Endpoint: PATCH /productos/{id}
    """
    url = f"{BASE_URL}/productos/{producto_id}"
    response = requests.patch(url, json=campos)

    if response.status_code == 200:
        return response.json()
    elif response.status_code == 404:
        raise ProductoNoEncontrado(f"No se puede parchear. ID {producto_id} no existe.")
    else:
        raise EcoMarketError(f"Error en PATCH: {response.status_code}")

def eliminar_producto(producto_id: int) -> bool:
    """
    Elimina un recurso.
    Endpoint: DELETE /productos/{id}
    """
    url = f"{BASE_URL}/productos/{producto_id}"
    response = requests.delete(url)

    if response.status_code == 204:
        return True
    elif response.status_code == 404:
        raise ProductoNoEncontrado(f"No se puede eliminar. ID {producto_id} no existe.")
    else:
        raise EcoMarketError(f"Error en DELETE: {response.status_code}")

# --- BLOQUE DE EJECUCIÓN ---
if __name__ == "__main__":
    print("--- INICIANDO PRUEBAS DEL CLIENTE CRUD ---")
    
    # Datos de prueba
    nuevo_prod = {"nombre": "Manzanas Gala", "precio": 2.5, "stock": 100}
    patch_data = {"precio": 3.0} # Solo cambiamos precio

    try:
        # 1. Crear
        print("\n1. Probando CREAR (POST)...")
        creado = crear_producto(nuevo_prod)
        print(f"✅ Creado: {creado}")

        # 2. Actualizar Parcial (PATCH) - IMPORTANTE PARA LA CAPTURA
        print("\n2. Probando ACTUALIZAR PARCIAL (PATCH)...")
        # Asumimos que el ID 1 existe o usamos el del creado si el server devuelve ID
        id_prueba = creado.get("id", 1) 
        parcheado = actualizar_producto_parcial(id_prueba, patch_data)
        print(f"✅ Parcheado: {parcheado}")

        # 3. Eliminar
        print("\n3. Probando ELIMINAR (DELETE)...")
        eliminado = eliminar_producto(id_prueba)
        print(f"✅ Eliminado: {eliminado}")

    except EcoMarketError as e:
        print(f"❌ Error controlado: {e}")
    except Exception as e:
        print(f"❌ Error inesperado: {e}")