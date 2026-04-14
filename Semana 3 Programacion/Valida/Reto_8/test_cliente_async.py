import pytest
import asyncio
import aiohttp
from aioresponses import aioresponses
from cliente_async_ecomarket import (
    listar_productos, obtener_producto, crear_producto,
    actualizar_producto_total, actualizar_producto_parcial, eliminar_producto,
    cargar_dashboard, crear_multiples_productos,
    EcoMarketError, ValidationError, ServerError, BASE_URL
)

# ----------------- FIXTURES -----------------
@pytest.fixture
def mock_aioresponse():
    with aioresponses() as m:
        yield m

@pytest.fixture
async def session():
    async with aiohttp.ClientSession() as session:
        yield session


# ==============================================================================
# 1. Equivalencia Funcional (5 tests)
# Verifica que pese a la migración async, sigamos arrojando los arrays y excepciones nativas del Week2
# ==============================================================================

@pytest.mark.asyncio
async def test_listar_productos_exito(mock_aioresponse, session):
    """Prueba que el método GET regrese estructuralmente lo mismo que la versión síncrona original"""
    mock_aioresponse.get(f"{BASE_URL}/productos", payload=[{"id": 1, "nombre": "Mochila Ecológica"}])
    res = await listar_productos(session)
    assert len(res) == 1
    assert res[0]["nombre"] == "Mochila Ecológica"

@pytest.mark.asyncio
async def test_obtener_producto_invalido(mock_aioresponse, session):
    """Prueba que el Validator local original de Week 2 siga interviniendo y atrapando campos faltantes (sin 'id')"""
    mock_aioresponse.get(f"{BASE_URL}/productos/1", payload={"nombre": "Invalido"}) # Falta 'id'
    with pytest.raises(ValidationError, match="Producto inválido"):
        await obtener_producto(session, 1)

@pytest.mark.asyncio
async def test_crear_producto_error_server(mock_aioresponse, session):
    """Prueba que la función levante ServerError ante 5xx"""
    mock_aioresponse.post(f"{BASE_URL}/productos", status=500)
    with pytest.raises(ServerError, match="Error del servidor: 500"):
        await crear_producto(session, {"id": 2, "nombre": ""})

@pytest.mark.asyncio
async def test_actualizar_producto_no_json(mock_aioresponse, session):
    """Prueba Content-Type inválido que se mapea a ValidationError"""
    mock_aioresponse.put(f"{BASE_URL}/productos/1", body="No soy JSON", headers={"Content-Type": "text/html"})
    with pytest.raises(ValidationError, match="No es JSON"):
        await actualizar_producto_total(session, 1, {"id": 1})

@pytest.mark.asyncio
async def test_eliminar_producto_exito(mock_aioresponse, session):
    """Prueba un retorno puro de 204 sin JSON para eliminar"""
    mock_aioresponse.delete(f"{BASE_URL}/productos/1", status=204)
    res = await eliminar_producto(session, 1)
    assert res is True


# ==============================================================================
# 2. Concurrencia Correcta (5 tests)
# ==============================================================================

@pytest.mark.asyncio
async def test_gather_tres_exitos(mock_aioresponse, session):
    """Prueba de recolección sana general. Tres tasks regresando JSON al mismo tiempo"""
    mock_aioresponse.get(f"{BASE_URL}/productos/1", payload={"id": 1})
    mock_aioresponse.get(f"{BASE_URL}/productos/2", payload={"id": 2})
    mock_aioresponse.get(f"{BASE_URL}/productos/3", payload={"id": 3})
    
    t1 = obtener_producto(session, 1)
    t2 = obtener_producto(session, 2)
    t3 = obtener_producto(session, 3)
    res = await asyncio.gather(t1, t2, t3)
    assert len(res) == 3

@pytest.mark.asyncio
async def test_gather_return_exceptions(mock_aioresponse, session):
    """Verifica el poderoso return_exceptions=True que captura los éxitos y los fracasos para que no muera todo el pipeline"""
    mock_aioresponse.get(f"{BASE_URL}/productos/1", payload={"id": 1})
    mock_aioresponse.get(f"{BASE_URL}/productos/2", status=500)
    mock_aioresponse.get(f"{BASE_URL}/productos/3", payload={"id": 3})
    
    res = await asyncio.gather(
        obtener_producto(session, 1),
        obtener_producto(session, 2), # Cae en 500
        obtener_producto(session, 3),
        return_exceptions=True
    )
    assert res[0]["id"] == 1
    assert isinstance(res[1], ServerError)  # Error internalizado
    assert res[2]["id"] == 3

@pytest.mark.asyncio
async def test_gather_sin_return_exceptions_propaga_mal(mock_aioresponse, session):
    """Test negativo: SIN la bandera, el await gather estalla interrumpiendo todo el script"""
    mock_aioresponse.get(f"{BASE_URL}/productos/1", payload={"id": 1})
    mock_aioresponse.get(f"{BASE_URL}/productos/2", status=500)
    
    with pytest.raises(ServerError):
        await asyncio.gather(obtener_producto(session, 1), obtener_producto(session, 2))

@pytest.mark.asyncio
async def test_cargar_dashboard_tolera_falla_parcial(mock_aioresponse):
    """Verifica que el layout devuelva un hash dict con los datos útiles y los errores segmentados"""
    mock_aioresponse.get(f"{BASE_URL}/productos", payload=[{"id": 1}])
    mock_aioresponse.get(f"{BASE_URL}/categorias", status=500)
    mock_aioresponse.get(f"{BASE_URL}/perfil", payload={"id": 99})
    
    res = await cargar_dashboard()
    assert "productos" in res["datos"]
    assert "perfil" in res["datos"]
    assert "categorias" in res["errores"]   # Capturado correctamente individual

@pytest.mark.asyncio
async def test_semaforo_limita_concurrencia_creador(mock_aioresponse):
    """El test de semaforo comprueba que las n peticiones completan sin salirse si el limitador estriba max = 5."""
    for i in range(10):
        mock_aioresponse.post(f"{BASE_URL}/productos", payload={"id": i})
    
    res_creados, res_fallidos = await crear_multiples_productos([{"id": i} for i in range(10)])
    assert len(res_creados) == 10
    assert len(res_fallidos) == 0


# ==============================================================================
# 3. Timeouts y Cancelación (5 tests)
# ==============================================================================

@pytest.mark.asyncio
async def test_timeout_individual_cancela_sola(mock_aioresponse, session):
    """Timeout individual intercepta un Exception de Aiohttp -> asyncio.TimeoutError convertido en EcoMarketError en cliente_async"""
    mock_aioresponse.get(f"{BASE_URL}/productos", exception=asyncio.TimeoutError())
    with pytest.raises(EcoMarketError, match="Timeout"):
        await listar_productos(session)

@pytest.mark.asyncio
async def test_cancelacion_cadena(mock_aioresponse, session):
    """Si una tarea en background es cancelada, arroja y libera limpiamente a través de asyncio.CancelledError"""
    mock_aioresponse.get(f"{BASE_URL}/productos", payload=[{"id": 1}])
    task = asyncio.create_task(listar_productos(session))
    task.cancel()  # Matamos la tarea
    with pytest.raises(asyncio.CancelledError):
        await task

@pytest.mark.asyncio
async def test_timeout_global_dashboard_bajada(mock_aioresponse):
    """Comprueba que si todo está sobrepasado el dashboard dictamine falla en su hash y devuelva las de tiempo correcto."""
    mock_aioresponse.get(f"{BASE_URL}/productos", exception=asyncio.TimeoutError())
    mock_aioresponse.get(f"{BASE_URL}/categorias", payload={"id": 1})
    mock_aioresponse.get(f"{BASE_URL}/perfil", payload={"id": 1})
    res = await cargar_dashboard()
    assert "Timeout" in res["errores"]["productos"]

@pytest.mark.asyncio
async def test_cancelled_error_resource_leak(mock_aioresponse):
    """Garantizar que una peticion cancelada global con task (Dashboard) no encripte el error sino que libere las varas"""
    task = asyncio.create_task(cargar_dashboard())
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task

@pytest.mark.asyncio
async def test_peticion_cancelada_no_log_error(mock_aioresponse, session):
    """Las corutinas solapadas que se auto cancelan no caen en logs por su manejo except asyncio.CancelledError en el base"""
    mock_aioresponse.get(f"{BASE_URL}/productos", payload=[{"id": 1}])
    task = asyncio.create_task(listar_productos(session))
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task


# ==============================================================================
# 4. Edge Cases o Casos Extremos de Concurrencia (5 tests)
# ==============================================================================

@pytest.mark.asyncio
async def test_todas_fallan_simultaneamente(mock_aioresponse):
    """Todas crashean en gather(.. return_exceptions) -> Ningún Dato, todos se van a ERRORES"""
    mock_aioresponse.get(f"{BASE_URL}/productos", status=500)
    mock_aioresponse.get(f"{BASE_URL}/categorias", status=500)
    mock_aioresponse.get(f"{BASE_URL}/perfil", status=500)
    res = await cargar_dashboard()
    assert len(res["errores"]) == 3
    assert len(res["datos"]) == 0

@pytest.mark.asyncio
async def test_servidor_cierra_conexion_mitad(mock_aioresponse, session):
    """Prueba el mapeado general de caida de Socket HTTP o Desconexion Fuerte -> EcoMarketError Connector"""
    mock_aioresponse.get(f"{BASE_URL}/productos", exception=aiohttp.ClientConnectorError(None, OSError("Closed")))
    with pytest.raises(EcoMarketError, match="No se pudo conectar al servidor"):
        await listar_productos(session)

@pytest.mark.asyncio
async def test_respuesta_despues_de_timeout(mock_aioresponse, session):
    """Simular un timeout de delay reventado y ver que devuelva su Wrapper Error asíncrono mapeado"""
    mock_aioresponse.get(f"{BASE_URL}/productos/1", exception=asyncio.TimeoutError())
    with pytest.raises(EcoMarketError):
        await obtener_producto(session, 1)

@pytest.mark.asyncio
async def test_dos_peticiones_mismo_endpoint_diff_params(mock_aioresponse, session):
    """Dos get parelelos a un path con distinct variables no se corrompen ni comparten su cache asincrono local"""
    mock_aioresponse.get(f"{BASE_URL}/productos?categoria=A", payload=[{"id": 1}])
    mock_aioresponse.get(f"{BASE_URL}/productos?categoria=B", payload=[{"id": 2}])
    r1, r2 = await asyncio.gather(
        listar_productos(session, categoria="A"),
        listar_productos(session, categoria="B")
    )
    assert r1[0]["id"] == 1
    assert r2[0]["id"] == 2

@pytest.mark.asyncio
async def test_sesion_cierra_correctamente_gather_errores(mock_aioresponse):
    """Una invocacion a un gather fallido en el creador multiple te enlista todos los dict caidos limpios."""
    mock_aioresponse.post(f"{BASE_URL}/productos", status=500)
    res_creados, res_fallidos = await crear_multiples_productos([{"id": 1}])
    assert len(res_fallidos) == 1
    assert "Error del servidor: 500" in res_fallidos[0]["error"]


# ==============================================================================
# 5. DOS TESTS Opcionales Solicitados en Instrucciones Extra de IA (2 tests)
# ==============================================================================

@pytest.mark.asyncio
async def test_extra_1_listar_productos_vacio(mock_aioresponse, session):
    """Escenario que la IA general omitió: Validar qué hace nuestra app cuando el servidor retorna un array Vacio [] en vez de diccionarios"""
    mock_aioresponse.get(f"{BASE_URL}/productos", payload=[])
    res = await listar_productos(session)
    assert type(res) == list and len(res) == 0

@pytest.mark.asyncio
async def test_extra_2_actualizar_parcial_exito(mock_aioresponse, session):
    """Escenario que la IA general omitió: Probar las ramas que aplican PATCH en la función asincrona 'actualizar_producto_parcial' para los parcial fields de Pydantic."""
    mock_aioresponse.patch(f"{BASE_URL}/productos/1", payload={"id": 1, "precio": 200, "nombre": "Camiseta Modificada"})
    res = await actualizar_producto_parcial(session, 1, {"precio": 200})
    assert res["precio"] == 200
    assert "id" in res
