import asyncio
import aiohttp

class EcoMarketError(Exception): pass
class ValidationError(EcoMarketError): pass
class ServerError(EcoMarketError): pass

def validar_producto(datos):
    if not isinstance(datos, dict) or "id" not in datos:
        raise ValidationError("Producto inválido.")
    return datos

def validar_lista_productos(datos):
    if not isinstance(datos, list):
        raise ValidationError("Se esperaba una lista de productos.")
    return [validar_producto(p) for p in datos]

async def _verificar_respuesta(response):
    if response.status >= 500:
        raise ServerError(f"Error del servidor: {response.status}")
    if response.status >= 400:
        raise ValidationError(f"Error de cliente: {response.status}")
    
    content_type = response.headers.get('Content-Type', '')
    if 'application/json' not in content_type:
        if response.status != 204:
            raise ValidationError(f"No es JSON: {content_type}")
    return response

# --- Migración Asíncrona de Funciones CRUD ---

BASE_URL = "http://localhost:3000/api"

async def listar_productos(session, categoria=None, orden=None):
    params = {}
    if categoria: params['categoria'] = categoria
    if orden: params['orden'] = orden
    try:
        async with session.get(f"{BASE_URL}/productos", params=params) as response:
            await _verificar_respuesta(response)
            datos = await response.json()
            return validar_lista_productos(datos)
    except asyncio.TimeoutError:
        raise EcoMarketError("Timeout al listar productos")
    except aiohttp.ClientConnectorError:
        raise EcoMarketError("No se pudo conectar al servidor")
    except asyncio.CancelledError:
        print("La petición de listar productos fue cancelada.")
        raise

async def obtener_producto(session, producto_id):
    try:
        async with session.get(f"{BASE_URL}/productos/{producto_id}") as response:
            await _verificar_respuesta(response)
            datos = await response.json()
            return validar_producto(datos)
    except asyncio.TimeoutError:
        raise EcoMarketError("Timeout al obtener producto")
    except aiohttp.ClientConnectorError:
        raise EcoMarketError("No se pudo conectar al servidor")

async def crear_producto(session, datos):
    try:
        async with session.post(f"{BASE_URL}/productos", json=datos) as response:
            await _verificar_respuesta(response)
            nuevo_producto = await response.json()
            return validar_producto(nuevo_producto)
    except asyncio.TimeoutError:
        raise EcoMarketError("Timeout al crear producto")
    except aiohttp.ClientConnectorError:
        raise EcoMarketError("No se pudo conectar al servidor")

async def actualizar_producto_total(session, producto_id, datos):
    try:
        async with session.put(f"{BASE_URL}/productos/{producto_id}", json=datos) as response:
            await _verificar_respuesta(response)
            producto_act = await response.json()
            return validar_producto(producto_act)
    except asyncio.TimeoutError:
        raise EcoMarketError("Timeout al actualizar producto")
    except aiohttp.ClientConnectorError:
        raise EcoMarketError("No se pudo conectar al servidor")

async def actualizar_producto_parcial(session, producto_id, campos):
    try:
        async with session.patch(f"{BASE_URL}/productos/{producto_id}", json=campos) as response:
            await _verificar_respuesta(response)
            producto_act = await response.json()
            return validar_producto(producto_act)
    except asyncio.TimeoutError:
        raise EcoMarketError("Timeout al actualizar parcialmente")
    except aiohttp.ClientConnectorError:
        raise EcoMarketError("No se pudo conectar al servidor")

async def eliminar_producto(session, producto_id):
    try:
        async with session.delete(f"{BASE_URL}/productos/{producto_id}") as response:
            await _verificar_respuesta(response)
            return True
    except asyncio.TimeoutError:
        raise EcoMarketError("Timeout al eliminar producto")
    except aiohttp.ClientConnectorError:
        raise EcoMarketError("No se pudo conectar al servidor")

# --- Funciones Mocks temporales para Categories y Perfil ---

async def obtener_categorias(session):
    try:
        async with session.get(f"{BASE_URL}/categorias") as response:
            await _verificar_respuesta(response)
            return await response.json()
    except asyncio.TimeoutError:
        raise EcoMarketError("Timeout al obtener categorias")
    except aiohttp.ClientConnectorError:
        raise EcoMarketError("Aviso de Conexión a categorías")

async def obtener_perfil(session):
    try:
        async with session.get(f"{BASE_URL}/perfil") as response:
            await _verificar_respuesta(response)
            return await response.json()
    except asyncio.TimeoutError:
        raise EcoMarketError("Timeout al obtener perfil")
    except aiohttp.ClientConnectorError:
        raise EcoMarketError("Aviso de Conexión a perfil")

# --- 2. Cargar Dashboard (Paralelo) ---

async def cargar_dashboard():
    # Se crea UNA sola sesion para lanzar las peticiones en lote
    timeout = aiohttp.ClientTimeout(total=10)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        tareas = [
            listar_productos(session),
            obtener_categorias(session),
            obtener_perfil(session)
        ]
        
        try:
            # gather(..., return_exceptions=True) es crítico
            resultados = await asyncio.gather(*tareas, return_exceptions=True)
            
            dashboard_data = {"datos": {}, "errores": {}}
            nombres = ["productos", "categorias", "perfil"]
            
            for nombre, resultado in zip(nombres, resultados):
                if isinstance(resultado, Exception):
                    dashboard_data["errores"][nombre] = str(resultado)
                else:
                    dashboard_data["datos"][nombre] = resultado
                    
            return dashboard_data
            
        except asyncio.CancelledError:
            print("Carga de dashboard cancelada por el usuario o entorno.")
            raise

# --- 3. Crear Múltiples Productos (Con Semáforo de Límite 5) ---

async def crear_multiples_productos(lista_productos):
    timeout = aiohttp.ClientTimeout(total=15)
    sem = asyncio.Semaphore(5)  # Máximo 5 peticiones simultáneas
    
    async def tarea_con_semaforo(session, datos):
        async with sem:
            try:
                return await crear_producto(session, datos)
            except Exception as e:
                return e

    async with aiohttp.ClientSession(timeout=timeout) as session:
        tareas = [tarea_con_semaforo(session, prod) for prod in lista_productos]
        
        resultados = await asyncio.gather(*tareas, return_exceptions=True)
        
        productos_creados = []
        productos_fallidos = []
        
        for dato_original, resultado in zip(lista_productos, resultados):
            if isinstance(resultado, Exception):
                productos_fallidos.append({"datos": dato_original, "error": str(resultado)})
            else:
                productos_creados.append(resultado)
                
        return productos_creados, productos_fallidos
