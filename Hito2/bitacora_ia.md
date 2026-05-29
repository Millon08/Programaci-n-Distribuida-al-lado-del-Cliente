# Bitácora IA

## Decisiones Aceptadas

\* \*\*Decisión 1\*\*: Diseñar el Circuit Breaker usando marcas de tiempo (`Date.now()`) en lugar de temporizadores asíncronos (`setTimeout`).

&#x20; \* \*Por qué se aceptó\*: Hace que el código sea plano, fácil de leer y permite probar las transiciones de estado de forma completamente matemática y predecible, sin lidiar con los retrasos o la complejidad del reloj interno de Node.js.



\* \*\*Decisión 2\*\*: Crear un simulador de red local (Mock) dentro de `cliente-integrado.js` en lugar de levantar un servidor con Express.js.

&#x20; \* \*Por qué se aceptó\*: Mantiene el proyecto con cero dependencias externas, es 100% reproducible en cualquier computadora sin instalar nada y permite controlar de forma exacta cuándo ocurren los errores 503 para demostrar el escudo de resiliencia.

## Decisiones Rechazadas

\* \*\*Decisión 1\*\*: Instalar el framework `Jest` para realizar las pruebas automatizadas del Circuit Breaker.

&#x20; \* \*Por qué se rechazó\*: Introducía dependencias externas innecesarias en el proyecto. Se prefirió usar aserciones nativas de Node.js (`node:assert`) porque cumple el mismo objetivo de certificar el código pero manteniendo el proyecto limpio, ligero y fácil de explicar.



\* \*\*Decisión 2\*\*: Usar eventos dinámicos (`EventEmitter`) para avisar a la aplicación en el milisegundo exacto en que el circuito cambia de estado.

&#x20; \* \*Por qué se rechazó\*: Añadía lógica asíncrona oculta y código anidado difícil de rastrear. Se rechazó en favor de un enfoque reactivo: el circuito solo revisa la hora y actualiza su estado cuando el cliente intenta hacer una petición real.

