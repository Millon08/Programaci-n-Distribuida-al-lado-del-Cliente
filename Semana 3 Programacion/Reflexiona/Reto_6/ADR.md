Reto 6: CRÍTICO DE DECISIONES DE CONCURRENCIA

Como parte de la simulación del rol entre el desarrollador (yo) y el Revisor de Arquitectura de IA y basándome en el proceso de defender mis elecciones en las estrategias de EcoMarket, entrego documentados formalmente los siguientes **Architecture Decision Records (ADR)** sobre nuestras tres decisiones concurrentes más apremiantes tras someterlas a escrutinio socrático, así como la reflexión metacognitiva obtenida.

---

## 🏛️ ADR 1: Estrategia de Coordinación para el Dashboard

**Contexto:**  
Para levantar la pantalla inicial requeríamos consultar APIs de `/productos`, `/categorias` y `/perfil`. Inicialmente el esquema combinaba todo usando un estricto `asyncio.gather(..., return_exceptions=True)`. La IA revisora me obligó a cuestionar: *¿Qué pasa si necesito mostrar datos progresivamente y evitar pantallas en blanco si `/notificaciones` tarda 10 segundos?*

**Decisión:**  
Cambiar la arquitectura de renderizado inicial de `gather()` a un ciclo observador usando `asyncio.wait(..., return_when=asyncio.FIRST_COMPLETED)`. Se etiquetan las peticiones imprescindibles ("críticas") y al confirmarse su existencia, se notifica y entrega la vista parcial al cliente.

**Alternativas consideradas:**
- *Usar `asyncio.gather()`:* Es excelente en simplicidad de código y recolección controlada, pero "enjaulaba" todo el proceso al tiempo que demorase la petición más lenta. Se sacrifica experiencia de usuario.
- *Usar `asyncio.as_completed()`:* Sirve para procesar las cosas conforme llegan, pero no permite aplicar lógica robusta de sub-grupos (como esperar obligatoriamente juntas dos firmas prioritarias: "perfil" y "productos").

**Consecuencias:**  
Aumentó ligeramente la complejidad y cantidad de líneas del código (state machine, wild data), pero a cambio transformamos la interfaz general a una vista reactiva y progresiva, protegiendo al usuario ante caídas temporales de módulos accesorios.

---

## 🏛️ ADR 2: Ciclo de Vida de la Sesión HTTP (`ClientSession`)

**Contexto:**  
El cliente requiere lanzar distintas invocaciones HTTP en diversos intervalos. Parecía intuitivamente más "encapsulado" instanciar y destruir el objeto HTTP en cada función CRUD. El revisor me incitó a defender esto: *¿Conoces cómo impacta re-declarar los headers o abrir puertos estáticos para cada uno?*

**Decisión:**  
Utilizar un patrón de Inyección de Dependencias, compartiendo **UNA sola `aiohttp.ClientSession`** instanciada al inicio del proceso y pasándola como contenedor (parámetro base) a cualquier método del CRUD que requiera comunicarse con el backend.

**Alternativas consideradas:**
- *Crear una sesión `session()` individual por petición (y usar `async with` interno en el CRUD):* Evita inyectar la dependencia de un framework en la función, pero sacrificamos fatalmente el "Connection Pooling". Cada petición iniciaría un nuevo y pesado *Three-way Handshake TCP*. Despedazaría los descriptores del sistema operativo local.
  
**Consecuencias:**
Garantizamos un rendimiento asíncrono impecable reciclando conexiones abiertas intermitentes con *keep-alive*. 
*Trade-off*: Nos obliga estructuradamente a programar rutinas al apagar el script para garantizar que `session.close()` ocurra, de lo contrario generamos gravísimos _resource leaks_.

---

## 🏛️ ADR 3: Contención con Límites Fijos Arbitrarios (Semáforo)

**Contexto:**  
La función `crear_multiples_productos` puede ser alimentada con colas masivas. Al usar concurrencia asíncrona ciega, 100 request harían 100 vuelos causando *Rate-limit* por parte del servidor API. La IA confrontó la decisión de topar y resolver el problema arbitrariamente: *¿Por qué un semáforo de 10? ¿Qué pasa si tu servidor aguanta 100 pero lo estrangulas localmente?*

**Decisión:**  
Envolver el ciclo iterativo dentro de un bloque `async with asyncio.Semaphore(MAX_CONCURRENCY)` parametrizado globalmente o desde un constructor base.

**Alternativas:**
- *No tener límites en cliente (Dejar que asyncio mande todo):* Causaríamos *DDoS* internos que nos llevarían probablemente a bloqueos 401/403 o la denegación de red.
- *Hacer Retry en Back-off al llegar el rechazo:* En vez de evitar enviarlo, envías y te esperas cuando te gritan. Es inestable.

**Consecuencias:**  
Nos aseguramos de comportarnos como un "buen ciudadano de red" sin sobrecongestionar. Conservamos consistencia en la memoria inyectada. 

---

## 💡 Reflexión: Modificación Cambiada tras el "Review"

**Decisión que cambiaría al admitir la reflexión empujada por la IA:**  
Durante la disertación defensiva caí en cuenta que el uso estático que asigne del "Semáforo = 10" carecía de fundamentación técnica. Se sacrificó innecesariamente potencial. 

Tras el análisis socrático, **cambiaría dicho límite estático a un objeto de calibración dinámica o variable de entorno (`ENV / Config`)**, de forma que, si en el futuro migramos EcoMarket a un clúster *Kubernetes* más fuerte, no sufriremos el cuello de botella invisible provocado por un límite local duro ("quemado en código"). Por otro lado, no implementar `Reintentos (Retry)` combinado con concurrencia es algo que nos queda a deber en robustez real de fallos; es altamente probable que necesite re-agregarlo (mediante decoradores) para no descartar información vital por simples parpadeos milimétricos del servidor al manejar grandes grupos con nuestro Semáforo.
