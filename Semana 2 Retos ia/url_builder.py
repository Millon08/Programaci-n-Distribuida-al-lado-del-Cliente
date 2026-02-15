import urllib.parse

class URLBuilder:
    """
    Clase encargada de construir URLs de forma segura, escapando caracteres
    especiales y codificando parámetros para evitar inyecciones.
    """
    
    def __init__(self, base_url: str):
        # Aseguramos que la URL base no tenga barra al final para consistencia
        self.base_url = base_url.rstrip('/')

    def build_url(self, endpoint: str, resource_id=None, query_params: dict = None) -> str:
        """
        Construye una URL final segura.
        
        Args:
            endpoint (str): El recurso (ej. "productos").
            resource_id (int|str, opcional): El ID del recurso. Se valida y escapa.
            query_params (dict, opcional): Diccionario de filtros para la URL.
        """
        
        # 1. Limpieza básica del endpoint
        safe_endpoint = endpoint.strip('/')
        
        # 2. Construcción del Path con ID (Protección contra Path Traversal)
        if resource_id is not None:
            # Validamos que el ID sea de un tipo esperado (Entero o String seguro)
            if not isinstance(resource_id, (int, str)):
                raise TypeError(f"ID debe ser int o str, recibido: {type(resource_id)}")
            
            # EL TRUCO DE SEGURIDAD: quote() convierte '/' en '%2F' y '..' en '%2E%2E'
            # Esto inutiliza los intentos de navegar por directorios.
            safe_id = urllib.parse.quote(str(resource_id), safe='')
            path = f"{safe_endpoint}/{safe_id}"
        else:
            path = safe_endpoint

        # Unimos base + path
        full_url = f"{self.base_url}/{path}"

        # 3. Construcción de Query Strings (Protección contra Query Injection)
        if query_params:
            # urlencode() convierte espacios en '+', '&' en '%26', etc.
            safe_query = urllib.parse.urlencode(query_params)
            full_url = f"{full_url}?{safe_query}"

        return full_url

# --- SECCIÓN DE PRUEBAS Y DEMOSTRACIÓN (Requerida por el reto) ---
if __name__ == "__main__":
    base = "https://api.ecomarket.com"
    builder = URLBuilder(base)

    print("--- 🛡️ DEMOSTRACIÓN DE SEGURIDAD URLBUILDER 🛡️ ---\n")

    # CASO 1: Ataque de Path Traversal
    # El atacante intenta subir niveles para leer archivos del servidor
    ataque_traversal = "../../etc/passwd"
    
    print("1. Intento de Path Traversal")
    print(f"   Dato malicioso: '{ataque_traversal}'")
    
    # Forma INSEGURA (lo que hacíamos antes)
    url_insegura = f"{base}/productos/{ataque_traversal}"
    print(f"   ❌ Sin protección: {url_insegura}")
    print("      (El servidor interpretaría esto y podría exponer archivos)")

    # Forma SEGURA (con URLBuilder)
    url_segura = builder.build_url("productos", resource_id=ataque_traversal)
    print(f"   ✅ Con URLBuilder: {url_segura}")
    print("      (Los caracteres '/' se escapan como '%2F', el servidor lo lee como un ID literal)")
    print("-" * 60)

    # CASO 2: Inyección de Query Params
    # El atacante intenta inyectar otro parámetro (admin=true) rompiendo la URL
    filtro_malicioso = "miel&admin=true"
    
    print("\n2. Intento de Inyección en Parámetros")
    print(f"   Dato malicioso: categoría = '{filtro_malicioso}'")
    
    # Forma INSEGURA
    url_insegura = f"{base}/productos?categoria={filtro_malicioso}"
    print(f"   ❌ Sin protección: {url_insegura}")
    print("      (El servidor cree que enviamos DOS parámetros: categoria='miel' y admin='true')")

    # Forma SEGURA
    url_segura = builder.build_url("productos", query_params={"categoria": filtro_malicioso})
    print(f"   ✅ Con URLBuilder: {url_segura}")
    print("      (El '&' se convierte en '%26', todo es parte del valor de 'categoria')")
    print("-" * 60)

    # CASO 3: Caracteres Unicode / Espacios
    # Nombres con caracteres extraños que rompen URLs simples
    nombre_raro = "Café & Postres / Delicia"
    
    print("\n3. Caracteres Especiales y Espacios")
    print(f"   Dato complejo: '{nombre_raro}'")
    
    url_segura = builder.build_url("buscar", query_params={"q": nombre_raro})
    print(f"   ✅ Con URLBuilder: {url_segura}")
    print("      (Espacios y barras codificados correctamente)")
    
    print("\n--- ✅ PRUEBAS FINALIZADAS ---")