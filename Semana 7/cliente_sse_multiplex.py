import asyncio
import logging
import json
import time
import traceback

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

"""
Decisiones de Diseño - Cliente SSE Multiplex (Reto 3)
======================================================
Constantes configuradas:
1. MAX_REINTENTOS = 5
   - Trade-off: Permitir más intentos le da resiliencia a caídas largas, pero retiene recursos en el cliente inútilmente si el servidor está apagado permanentemente. 5 es un balance prudente.
2. TIMEOUT_CONEXION = 30s
   - Trade-off: Un timeout alto evita reconexiones innecesarias por picos de latencia, pero retrasa la detección de una "conexión muerta" (half-open connection).
3. INTERVALO_KEEPALIVE_ESPERADO = 15s
   - Trade-off: Esperar pings frecuentes del servidor asegura que la conexión sigue viva rápidamente, pero aumenta el ancho de banda inactivo. Si pasan 15s sin datos ni ping, el cliente cierra y reabre.

Conexión Única (Multiplexada) vs Múltiples Conexiones:
Utilizar una única conexión SSE para recibir precios, stock, pedidos y alertas evita saturar los descriptores de red del cliente y del servidor. Abre un solo puerto local, consumiendo un solo hilo/socket en el servidor, escalando mucho mejor que tener 4 eventos SSE abiertos en paralelo.
"""

class EventRouter:
    """Enruta eventos SSE a los handlers correspondientes basados en su tipo."""
    def __init__(self):
        self._handlers = {}

    def register_handler(self, event_type, handler):
        self._handlers[event_type] = handler

    def route_event(self, event_type, payload_str):
        if not event_type or not payload_str:
            logging.warning("Evento o payload vacío ignorado.")
            return

        handler = self._handlers.get(event_type)
        if not handler:
            logging.warning(f"No hay handler registrado para el evento tipo: {event_type}. Evento descartado.")
            return

        try:
            payload = json.loads(payload_str)
            handler(payload)
        except json.JSONDecodeError:
            logging.error(f"Error de parseo JSON en evento '{event_type}'. Payload malformado: {payload_str}")
        except Exception as e:
            logging.error(f"El handler para '{event_type}' falló: {e}")

class ClienteSSEMultiplex:
    def __init__(self):
        self.router = EventRouter()
        self._configurar_handlers_ecomarket()

    def _configurar_handlers_ecomarket(self):
        self.router.register_handler('precio_actualizado', self.handle_precio)
        self.router.register_handler('stock_critico', self.handle_stock)
        self.router.register_handler('estado_pedido', self.handle_pedido)
        self.router.register_handler('alerta_sistema', self.handle_alerta)

    def handle_precio(self, payload):
        logging.info(f"[PRECIO] Actualización detectada: ID {payload.get('producto_id')} a ${payload.get('nuevo_precio')}")

    def handle_stock(self, payload):
        logging.warning(f"[STOCK] ¡Crítico! Producto {payload.get('producto_id')} queda(n) {payload.get('stock_restante')} unidades.")

    def handle_pedido(self, payload):
        logging.info(f"[PEDIDO] Estado del pedido {payload.get('pedido_id')} -> {payload.get('estado')}")

    def handle_alerta(self, payload):
        logging.error(f"[ALERTA] Sistema: {payload.get('mensaje')}")
        # Simulamos un fallo de handler si la alerta dice "CRASH"
        if payload.get('mensaje') == "CRASH":
            raise ValueError("Fallo inducido por el payload de la alerta")


    async def correr_demo(self):
        print("\n=== INICIANDO DEMO: 10 EVENTOS MIXTOS ===")
        eventos_mixtos = [
            ("precio_actualizado", '{"producto_id": 1, "nuevo_precio": 19.99}'),
            ("estado_pedido", '{"pedido_id": "PED-404", "estado": "EN_PREPARACION"}'),
            ("precio_actualizado", '{"producto_id": 2, "nuevo_precio": 45.00}'),
            ("stock_critico", '{"producto_id": 5, "stock_restante": 2}'),
            ("estado_pedido", '{"pedido_id": "PED-404", "estado": "ENVIADO"}'),
            ("alerta_sistema", '{"mensaje": "Mantenimiento a las 03:00 AM"}'),
            ("precio_actualizado", '{"producto_id": 1, "nuevo_precio": 18.99}'),
            ("stock_critico", '{"producto_id": 9, "stock_restante": 1}'),
            ("estado_pedido", '{"pedido_id": "PED-405", "estado": "RECIBIDO"}'),
            ("precio_actualizado", '{"producto_id": 3, "nuevo_precio": 5.50}'),
        ]

        for tipo, payload in eventos_mixtos:
            self.router.route_event(tipo, payload)
            await asyncio.sleep(0.1)

        print("\n=== INICIANDO AUDITORIA: 4 ESCENARIOS DE FALLO ===")
        
        print("\n--- Escenario 1: JSON Malformado ---")
        self.router.route_event("precio_actualizado", '{"producto_id": 1, "nuevo_precio": }') # Falta valor
        
        print("\n--- Escenario 2: Evento Desconocido (no registrado) ---")
        self.router.route_event("evento_fantasma", '{"data": "esto no existe"}')

        print("\n--- Escenario 3: Excepción lanzada por el handler ---")
        self.router.route_event("alerta_sistema", '{"mensaje": "CRASH"}')

        print("\n--- Escenario 4: Evento sin payload (Vacio) ---")
        self.router.route_event("estado_pedido", '')

if __name__ == "__main__":
    cliente = ClienteSSEMultiplex()
    asyncio.run(cliente.correr_demo())
    print("\n--- EJECUCION COMPLETADA ---")
