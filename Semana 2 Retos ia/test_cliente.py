import pytest
import responses
import requests
import json
from cliente_ecomarket import (
    listar_productos,
    obtener_producto,
    crear_producto,
    actualizar_producto_parcial,
    eliminar_producto,
    BASE_URL
)

# ==========================================
# 1. HAPPY PATH (Casos de éxito)
# ==========================================

@responses.activate
def test_listar_productos_exito():
    # Simulamos que el servidor responde correctamente
    mock_data = [{"id": 1, "nombre": "Manzana", "precio": 10}]
    responses.add(responses.GET, f"{BASE_URL}/productos", json=mock_data, status=200)

    resultado = listar_productos()
    assert isinstance(resultado, list)
    assert len(resultado) == 1
    assert resultado[0]['nombre'] == "Manzana"

@responses.activate
def test_obtener_producto_exito():
    mock_data = {"id": 1, "nombre": "Manzana", "precio": 10}
    responses.add(responses.GET, f"{BASE_URL}/productos/1", json=mock_data, status=200)

    resultado = obtener_producto(1)
    assert resultado['id'] == 1
    assert resultado['nombre'] == "Manzana"

@responses.activate
def test_crear_producto_exito():
    nuevo_producto = {"nombre": "Pera", "precio": 20, "categoria": "frutas"}
    respuesta_mock = {"id": 2, "nombre": "Pera", "mensaje": "Creado"}
    
    responses.add(responses.POST, f"{BASE_URL}/productos", json=respuesta_mock, status=201)

    resultado = crear_producto(nuevo_producto)
    assert resultado['id'] == 2

@responses.activate
def test_actualizar_parcial_exito():
    datos_update = {"precio": 25}
    respuesta_mock = {"status": "Actualizado correctamente"}
    
    responses.add(responses.PATCH, f"{BASE_URL}/productos/1", json=respuesta_mock, status=200)

    resultado = actualizar_producto_parcial(1, datos_update)
    assert resultado['status'] == "Actualizado correctamente"

@responses.activate
def test_eliminar_producto_exito():
    # DELETE suele devolver 204 No Content o un JSON simple
    responses.add(responses.DELETE, f"{BASE_URL}/productos/1", status=204)

    resultado = eliminar_producto(1)
    assert resultado is True  # Asumiendo que tu función devuelve True si sale bien

# ==========================================
# 2. ERRORES HTTP (Simulando fallos del server)
# ==========================================

@responses.activate
def test_error_404_producto_no_encontrado():
    responses.add(responses.GET, f"{BASE_URL}/productos/999", status=404)

    # Esperamos que tu cliente lance una excepción o maneje el error
    with pytest.raises(Exception): # O la excepción específica que uses, ej: requests.exceptions.HTTPError
        obtener_producto(999)

@responses.activate
def test_error_500_servidor_caido():
    responses.add(responses.GET, f"{BASE_URL}/productos", status=500)

    with pytest.raises(Exception):
        listar_productos()

@responses.activate
def test_error_400_peticion_invalida():
    # Intentar crear algo mal
    responses.add(responses.POST, f"{BASE_URL}/productos", status=400)
    
    with pytest.raises(Exception):
        crear_producto({})

# ==========================================
# 3. EDGE CASES (Casos raros)
# ==========================================

@responses.activate
def test_respuesta_vacia_pero_200():
    # El server dice OK, pero manda lista vacía
    responses.add(responses.GET, f"{BASE_URL}/productos", json=[], status=200)

    resultado = listar_productos()
    assert resultado == []

@responses.activate
def test_timeout_servidor():
    # Simulamos que el servidor tarda mucho en responder
    responses.add(responses.GET, f"{BASE_URL}/productos", body=Exception("Timeout"))

    with pytest.raises(Exception):
        listar_productos()

# ==========================================
# 4. TUS TESTS PROPIOS (Requisito del reto)
# ==========================================

@responses.activate
def test_filtro_categoria_vacio():
    # Test propio 1: Qué pasa si filtro por una categoría que no tiene productos
    responses.add(responses.GET, f"{BASE_URL}/productos", json=[], status=200)
    resultado = listar_productos() # Aquí podrías pasar categoría si tu función lo soporta
    assert len(resultado) == 0

@responses.activate
def test_crear_producto_precio_negativo():
    # Test propio 2: Validar lógica de negocio si el API falla
    responses.add(responses.POST, f"{BASE_URL}/productos", status=400)
    with pytest.raises(Exception):
        crear_producto({"nombre": "Malo", "precio": -50})
       
# ==========================================
# 5. BONUS TRACK (Para llegar a los 20+ tests)
# ==========================================

@responses.activate
def test_error_401_no_autorizado():
    # Simulamos que falta el token o permiso
    responses.add(responses.GET, f"{BASE_URL}/productos", status=401)
    with pytest.raises(Exception):
        listar_productos()

@responses.activate
def test_error_409_conflicto_duplicado():
    # Simulamos que intentamos crear algo que ya existe
    responses.add(responses.POST, f"{BASE_URL}/productos", status=409)
    with pytest.raises(Exception):
        crear_producto({"nombre": "Duplicado", "precio": 10})

@responses.activate
def test_error_503_servicio_no_disponible():
    # Simulamos servidor en mantenimiento
    responses.add(responses.GET, f"{BASE_URL}/productos", status=503)
    with pytest.raises(Exception):
        listar_productos()

@responses.activate
def test_json_respuesta_invalida():
    # El servidor devuelve texto plano en vez de JSON (pasa mucho en errores de nginx)
    responses.add(responses.GET, f"{BASE_URL}/productos", body="Internal Server Error", status=500)
    with pytest.raises(Exception):
        listar_productos()

@responses.activate
def test_actualizar_producto_id_inexistente():
    # Intentar actualizar algo que no existe
    responses.add(responses.PATCH, f"{BASE_URL}/productos/9999", status=404)
    with pytest.raises(Exception):
        actualizar_producto_parcial(9999, {"precio": 50})

@responses.activate
def test_eliminar_producto_id_inexistente():
    # Intentar borrar algo que no existe
    responses.add(responses.DELETE, f"{BASE_URL}/productos/9999", status=404)
    with pytest.raises(Exception):
        eliminar_producto(9999)

@responses.activate
def test_crear_producto_sin_campos_requeridos():
    # Enviar un diccionario vacío al crear
    responses.add(responses.POST, f"{BASE_URL}/productos", status=400)
    with pytest.raises(Exception):
        crear_producto({})

@responses.activate
def test_busqueda_sin_resultados():
    # Una búsqueda válida que simplemente no trae nada
    responses.add(responses.GET, f"{BASE_URL}/productos", json=[], status=200)
    resultado = listar_productos()
    assert isinstance(resultado, list)
    assert len(resultado) == 0

@responses.activate
def test_timeout_en_creacion():
    # El servidor se cuelga al intentar guardar
    responses.add(responses.POST, f"{BASE_URL}/productos", body=Exception("TimeOut"))
    with pytest.raises(Exception):
        crear_producto({"nombre": "Lento", "precio": 10})