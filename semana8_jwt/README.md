# Entregable Semana 8: JWT y Manejo de Sesión

Este documento consolida las decisiones de diseño del manejo de autenticación del cliente y los reportes de validación de escenarios requeridos.

---

## 1. Decisiones de Diseño (Comprende - Reto 1)

### Decodificación de Payload en el Cliente
**Concepto:** Se decodifica el token (base64url) en el cliente sin verificar la firma criptográfica porque el propósito de esto es **exclusivamente predictivo y de rendimiento**, no de seguridad. 
**Justificación:** Extraemos el claim `exp` (fecha de expiración) para ejecutar *Preemptive Refreshes* (refrescos proactivos) antes de enviar peticiones destinadas al fracaso. La validación real, que asegura que el token no ha sido manipulado, sigue ocurriendo siempre del lado del servidor usando su clave secreta o llave pública.

### Almacenamiento Local
La clase `TokenManager` mantiene los tokens en memoria (`self.access_token`). Esto reduce drásticamente el impacto de ataques XSS frente a usar `localStorage`. Si el cliente fuera una aplicación nativa, se delegaría a un keystore seguro, pero para los propósitos del cliente CLI / Python esto emula el estado seguro en memoria.

---

## 2. Decisiones de Diseño UI y Propagación de Estado (Diseño UI - Reto 2)

### Notificación Múltiple de Expiración de Sesión
**Mecanismo Elegido:** Patrón Observer (Publicador/Suscriptor).
**Justificación:** En una aplicación moderna (ej. frontend basado en componentes o aplicación de escritorio multicomponente), es común que el interceptor HTTP global intercepte el 401 y force un `logout`. Sin embargo, múltiples piezas de la interfaz de usuario (el menú lateral, la foto de perfil, un modal abierto) necesitan enterarse simultáneamente para actualizarse. 
En `token_manager.py` implementé un sistema simple de `add_observer()`. Cuando `logout()` se ejecuta (sea por botón o por interceptor HTTP), invoca `_notify_logout()`, lo cual dispara una señal global a todos los suscriptores. En el simulador, puedes ver cómo el "Componente UI" reacciona automáticamente lanzando un aviso sin estar directamente acoplado a las peticiones HTTP.

---

## 3. Reflexiones sobre Escenarios Fallidos (Reflexiona - Reto 3)

1. **¿Qué hacer si múltiples requests disparan el refresh al mismo tiempo?**
   **Reflexión:** Si 5 requests concurrentes detectan que el token expiró, los 5 intentarían enviar el refresh token simultáneamente. Esto causaría un "Refresh Token Reuse" y el backend invalidaría la familia de tokens. **Solución:** Se implementó `asyncio.Lock()` en `refresh_access_token()`. La primera petición toma el lock, realiza la llamada a red, y las 4 restantes esperan. Cuando despiertan, chequean `is_expiring_soon()` y notan que ya fue refrescado, prosiguiendo con el nuevo token de forma segura sin hacer otra llamada.

2. **¿Qué hacer cuando falla el endpoint de refresh?**
   **Reflexión:** Si la llamada al endpoint de `/refresh` devuelve un error (ej. porque el refresh token ya expiró o el administrador revocó la sesión del usuario), **no debe haber reintentos infinitos**. El cliente asume la sesión como totalmente muerta. Llama internamente a la rutina de `logout()`, limpia credenciales y emite el evento global para que la interfaz eche al usuario a la pantalla de login.

---

## 4. Reporte de Validación (Valida)

El archivo `simulador_jwt.py` implementa los 5 escenarios solicitados mediante Mocks.

| Escenario Evaluado | Resultado Observado en Simulador | Veredicto |
|---|---|---|
| **1. Login Exitoso** | El `TokenManager` decodifica correctamente y el estado cambia a `True`. | Pasó |
| **2. Token Válido** | El cliente procesa la petición enviando el header de Autorización sin alterar nada. | Pasó |
| **3. Expiración Inminente (Proactivo)** | El interceptor nota la expiración calculada (< 60s), lanza el refresh usando el Lock, guarda nuevo token y realiza la llamada final exitosamente. | Pasó |
| **4. Expiración Inesperada 401 (Reactivo)** | El servidor responde 401. El interceptor lo atrapa, ejecuta refresh, vuelve a intentarlo con nuevo token y logra éxito. | Pasó |
| **5. Expiración de Refresh Token** | El servidor rechaza el refresh. El TokenManager limpia credenciales, dispara evento a UI y niega la llamada. | Pasó |

## Correcciones Aplicadas Post-Auditoría
* El manejo de errores de decodificación JSON del Base64 (`decode_payload()`) no existía inicialmente. Si el usuario alteraba el string y no era un JSON válido, el simulador crasheaba en el `json.loads()`. Se implementó un manejo de excepciones controlado que rechaza amablemente los payloads malformados sin crashear el proceso.
