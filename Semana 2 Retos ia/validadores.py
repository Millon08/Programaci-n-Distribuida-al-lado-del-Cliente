import datetime

def validar_producto(data: dict) -> dict:
    """
    Valida un diccionario de producto individual.
    Lanza ValueError o TypeError si los datos son inválidos.
    Retorna el diccionario validado si todo está bien.
    """
    
    # 1. Validar que data sea un diccionario
    if not isinstance(data, dict):
        raise TypeError(f"El producto debe ser un objeto (dict), se recibió: {type(data).__name__}")

    # 2. Validar campos requeridos
    campos_requeridos = ['id', 'nombre', 'precio', 'categoria']
    for campo in campos_requeridos:
        if campo not in data:
            raise ValueError(f"Falta el campo requerido: '{campo}'")

    # 3. Validar tipos de datos básicos
    if not isinstance(data['id'], int):
        raise TypeError(f"El 'id' debe ser entero (int), se recibió: {type(data['id']).__name__}")
    
    if not isinstance(data['nombre'], str):
        raise TypeError(f"El 'nombre' debe ser texto (str), se recibió: {type(data['nombre']).__name__}")
        
    # Aceptamos int o float para el precio, pero lo tratamos como número
    if not isinstance(data['precio'], (float, int)):
        raise TypeError(f"El 'precio' debe ser numérico (float), se recibió: {type(data['precio']).__name__}")

    # 4. Validaciones lógicas (Reglas de Negocio)
    if data['precio'] <= 0:
        raise ValueError(f"El precio debe ser mayor a 0. Valor actual: {data['precio']}")

    categorias_validas = ['frutas', 'verduras', 'lacteos', 'miel', 'conservas']
    if data['categoria'] not in categorias_validas:
        raise ValueError(f"Categoría '{data['categoria']}' no válida. Opciones: {categorias_validas}")

    # 5. Validar campos opcionales
    # 'disponible' (bool)
    if 'disponible' in data:
        if not isinstance(data['disponible'], bool):
            raise TypeError(f"El campo 'disponible' debe ser booleano, se recibió: {type(data['disponible']).__name__}")

    # 'productor' (dict anidado)
    if 'productor' in data:
        if not isinstance(data['productor'], dict):
            raise TypeError("El campo 'productor' debe ser un objeto (dict)")
        # Validación básica del anidado
        if 'id' in data['productor'] and not isinstance(data['productor']['id'], int):
             raise TypeError("El ID del productor debe ser int")

    # 'creado_en' (formato fecha ISO 8601)
    if 'creado_en' in data:
        if not isinstance(data['creado_en'], str):
             raise TypeError("La fecha 'creado_en' debe ser string")
        # Intento simple de parseo para verificar formato
        try:
            # Esto valida formatos como '2024-01-15T10:30:00Z'
            datetime.datetime.fromisoformat(data['creado_en'].replace('Z', '+00:00'))
        except ValueError:
            raise ValueError(f"Formato de fecha inválido en 'creado_en': {data['creado_en']}")

    return data

def validar_lista_productos(lista_data: list) -> list:
    """
    Valida una lista completa de productos.
    """
    if not isinstance(lista_data, list):
        raise TypeError(f"Se esperaba una lista de productos, se recibió: {type(lista_data).__name__}")
    
    lista_validada = []
    for index, item in enumerate(lista_data):
        try:
            producto_valido = validar_producto(item)
            lista_validada.append(producto_valido)
        except (ValueError, TypeError) as e:
            # Agregamos contexto de cuál ítem falló
            raise ValueError(f"Error en el producto índice {index}: {str(e)}")
            
    return lista_validada