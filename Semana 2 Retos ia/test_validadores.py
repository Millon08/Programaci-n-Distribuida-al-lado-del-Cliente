from validadores import validar_producto

# Definimos 5 casos de prueba que DEBEN fallar (Casos Maliciosos/Erróneos)

casos_falla = [
    {
        "nombre_prueba": "CASO 1: Falta campo requerido (id)",
        "data": {
            "nombre": "Manzanas",
            "precio": 20.5,
            "categoria": "frutas"
        }
    },
    {
        "nombre_prueba": "CASO 2: Precio negativo",
        "data": {
            "id": 2,
            "nombre": "Peras",
            "precio": -5.00,  # <-- Error aquí
            "categoria": "frutas"
        }
    },
    {
        "nombre_prueba": "CASO 3: Categoría inválida",
        "data": {
            "id": 3,
            "nombre": "Teclado Gamer",
            "precio": 1500.0,
            "categoria": "electronica" # <-- Error aquí
        }
    },
    {
        "nombre_prueba": "CASO 4: Tipo de dato incorrecto (disponible no es bool)",
        "data": {
            "id": 4,
            "nombre": "Miel",
            "precio": 50.0,
            "categoria": "miel",
            "disponible": "SÍ" # <-- Error aquí (debería ser True/False)
        }
    },
    {
        "nombre_prueba": "CASO 5: Productor mal formado (no es dict)",
        "data": {
            "id": 5,
            "nombre": "Jalea",
            "precio": 30.0,
            "categoria": "conservas",
            "productor": ["Granja", 123] # <-- Error aquí (debería ser dict)
        }
    }
]

print("--- INICIANDO TEST DE VALIDADORES ---\n")

exitos = 0
for caso in casos_falla:
    print(f"Probando {caso['nombre_prueba']}...")
    try:
        validar_producto(caso['data'])
        print("❌ FALLÓ: El validador aceptó datos inválidos.")
    except (ValueError, TypeError) as e:
        print(f"✅ ÉXITO: Error detectado correctamente -> {e}")
        exitos += 1
    print("-" * 50)

print(f"\nResumen: {exitos}/{len(casos_falla)} pruebas pasadas.")