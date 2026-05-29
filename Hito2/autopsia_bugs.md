###### **# Autopsia de Bugs (Reto 3)**

###### 

###### **## Bug 1: Ausencia de Inicio de Sesión Inicial (Token Nulo)**

###### \* \*\*Síntoma\*\*: La aplicación fallaba inmediatamente al arrancar en la primerísima petición, enviando datos vacíos a la red y arrojando errores de acceso denegado.

###### \* \*\*Causa Raíz\*\*: El método `getToken()` daba por hecho que el sistema ya tenía un pase de acceso guardado. No revisaba si el token estaba en `null` antes de intentar leerlo.

###### \* \*\*Corrección\*\*: Se introdujo un escudo protector al inicio del método: si el sistema detecta que no tiene un token guardado, frena y ejecuta automáticamente el método `login()` para conseguir uno.

###### \* \*\*Principio Vulnerado\*\*: Programación Defensiva (asumir erróneamente que las variables obligatorias siempre vendrán con datos válidos).

###### 

###### **## Bug 2: Reloj Invertido en la Condición de Expiración**

###### \* \*\*Síntoma\*\*: El sistema intentaba renovar el token en cada segundo y en cada petición, lo que volvía la aplicación extremadamente lenta debido al exceso de solicitudes de refresco innecesarias.

###### \* \*\*Causa Raíz\*\*: La fórmula matemática para verificar la caducidad del token tenía el signo de comparación al revés. El código interpretaba que un token recién creado y totalmente válido ya estaba caducado.

###### \* \*\*Corrección\*\*: Se corrigió el operador matemático para comparar de forma correcta si la hora actual ya superó la fecha límite permitida (`Date.now() > this.tiempoExpiracion`).

###### \* \*\*Principio Vulnerado\*\*: Corrección Lógica Básica y Validación de Límites.

###### 

###### **## Bug 3: Olvido de Renovación de Tiempo tras el Refresco**

###### \* \*\*Síntoma\*\*: Después de que el token caducaba por primera vez, el sistema entraba en un bucle infinito de errores de autenticación, a pesar de que el proceso de refresco decía ser exitoso.

###### \* \*\*Causa Raíz\*\*: El método `refresh()` generaba una nueva clave de texto para el token, pero se le olvidaba por completo actualizar la variable `this.tiempoExpiracion`, dejando el reloj con la hora vieja del pasado.

###### \* \*\*Corrección\*\*: Se aseguró que al generar un nuevo token dentro de `refresh()`, también se calcule y asigne la nueva hora de expiración sumándole los minutos correspondientes al reloj actual.

###### \* \*\*Principio Vulnerado\*\*: Consistencia de Datos (si actualizas un recurso, debes actualizar obligatoriamente sus propiedades vinculadas).

