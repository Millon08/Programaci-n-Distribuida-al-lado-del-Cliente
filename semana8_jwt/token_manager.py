import asyncio
import base64
import json
import time
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class TokenManager:
    def __init__(self):
        self.access_token = None
        self.refresh_token = None
        self.expires_at = 0
        self._refresh_lock = asyncio.Lock()
        self.is_logged_in = False
        self._observers = []

    def add_observer(self, observer_callback):
        """Para notificar a la UI sobre cambios de sesión (Logout)."""
        self._observers.append(observer_callback)

    def _notify_logout(self):
        for obs in self._observers:
            obs("LOGOUT_EVENT")

    def store_tokens(self, access_token, refresh_token):
        self.access_token = access_token
        self.refresh_token = refresh_token
        payload = self.decode_payload()
        if payload and 'exp' in payload:
            self.expires_at = payload['exp']
        else:
            # Si no hay 'exp', asumimos 5 minutos por defecto para seguridad
            self.expires_at = time.time() + 300
        self.is_logged_in = True
        logging.info("Tokens almacenados exitosamente.")

    def decode_payload(self):
        """
        Decodifica el payload JWT sin verificar la firma criptográfica.
        Explicación: Esto se hace exclusivamente del lado del cliente para leer 
        información pública como la fecha de expiración ('exp') y hacer un refresh 
        preventivo. La validación real y segura del token SIEMPRE ocurre en el servidor.
        """
        if not self.access_token:
            return None
        
        parts = self.access_token.split('.')
        if len(parts) != 3:
            logging.error("El token no tiene las 3 partes (Header.Payload.Signature).")
            raise ValueError("Token JWT malformado")
        
        payload_b64 = parts[1]
        # Añadir padding requerido para base64
        payload_b64 += "=" * ((4 - len(payload_b64) % 4) % 4)
        
        try:
            decoded = base64.b64decode(payload_b64).decode('utf-8')
            return json.loads(decoded)
        except Exception as e:
            logging.error(f"Error parseando el payload del token: {e}")
            raise ValueError("El payload no es un JSON válido o base64 incorrecto")

    def is_expiring_soon(self, buffer_seconds=60):
        """Verifica si el token expira dentro del buffer estipulado."""
        if not self.access_token:
            return True
        return time.time() > (self.expires_at - buffer_seconds)

    async def refresh_access_token(self):
        """Refresca el token evitando requests duplicados usando un Lock."""
        if not self.refresh_token:
            self.logout()
            return False

        # El uso del lock asegura que si hay N peticiones concurrentes esperando un refresh,
        # solo la primera hace el request de red, y las demás se benefician de ese nuevo token.
        async with self._refresh_lock:
            # Doble comprobación por si otro hilo ya hizo el refresh mientras esperábamos el lock
            if not self.is_expiring_soon():
                logging.info("Refresh cancelado: El token ya fue refrescado por otra corrutina.")
                return True

            logging.info("Realizando petición HTTP al endpoint de refresh...")
            await asyncio.sleep(0.5) # Simulación de red
            
            # Simulamos si el refresh token está expirado o es inválido
            if "expired_refresh" in self.refresh_token:
                logging.error("Refresh token expirado/inválido devuelto por servidor. Rechazado.")
                self.logout()
                return False

            # Generar un mock token nuevo
            exp_time = int(time.time()) + 3600
            mock_payload = base64.b64encode(json.dumps({"sub": "user123", "exp": exp_time}).encode()).decode().rstrip('=')
            nuevo_access = f"header.{mock_payload}.signature"
            
            self.store_tokens(nuevo_access, self.refresh_token)
            logging.info("Refresh exitoso. Nuevo token almacenado.")
            return True

    def get_auth_header(self):
        """Retorna el header de Authorization si existe token."""
        if self.access_token:
            return {"Authorization": f"Bearer {self.access_token}"}
        return {}

    def logout(self):
        self.access_token = None
        self.refresh_token = None
        self.expires_at = 0
        self.is_logged_in = False
        logging.warning("LOGOUT ejecutado. Credenciales eliminadas localmente.")
        self._notify_logout()


class HttpClientBase:
    """Cliente HTTP que incluye el Interceptor de Autorización."""
    def __init__(self, token_manager: TokenManager):
        self.tm = token_manager

    async def fetch(self, url, method="GET", data=None, simular_error=None):
        """
        Envía una petición. 
        - Comprobación preventiva: Refresca antes de enviar si 'is_expiring_soon' es True.
        - Comprobación reactiva (Interceptor): Si a pesar de todo recibimos 401, refresca y reintenta.
        """
        # 1. Proactivo (Preemptive Refresh)
        if self.tm.is_expiring_soon():
            logging.info("Interceptor: Token expirando pronto (Proactivo). Intentando refresh antes de request.")
            exito = await self.tm.refresh_access_token()
            if not exito:
                return {"error": "Session expired (Refresh failed)"}, 401

        headers = self.tm.get_auth_header()
        
        logging.info(f"Interceptor: Enviando request a {url} con token...")
        respuesta, status = await self._mock_network_call(url, headers, simular_error)

        # 2. Reactivo (Interceptor ante 401 inesperado)
        if status == 401:
            logging.warning("Interceptor: 401 recibido del servidor. Intentando refresh de recuperación...")
            exito = await self.tm.refresh_access_token()
            if exito:
                headers = self.tm.get_auth_header()
                logging.info(f"Interceptor: Reintentando request a {url}...")
                respuesta, status = await self._mock_network_call(url, headers, simular_error=None)
                if status == 401:
                    logging.error("Interceptor: El servidor sigue rechazando con 401 a pesar del refresh. Forzando logout.")
                    self.tm.logout()
            else:
                logging.error("Interceptor: Falló el refresh de recuperación. Request denegado.")
                return {"error": "Session expired"}, 401

        return respuesta, status

    async def _mock_network_call(self, url, headers, simular_error=None):
        await asyncio.sleep(0.2)
        if simular_error == "401":
            return {"error": "Unauthorized"}, 401
        
        if "Authorization" not in headers:
            return {"error": "Missing Token"}, 401
            
        return {"data": f"Respuesta exitosa de {url}"}, 200
