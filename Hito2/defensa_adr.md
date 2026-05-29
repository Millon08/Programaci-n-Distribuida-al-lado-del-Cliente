# Defensa de ADR (Reto 5)

## Contexto y Problema

* El comité de revisión solicita justificar cómo el sistema maneja la pausa de enfriamiento del Circuit Breaker al pasar de estado ABIERTO a SEMI-ABIERTO. El reto técnico consiste en controlar este tiempo sin introducir componentes complejos (como alarmas en segundo plano o librerías externas) que dificulten las pruebas automatizadas, consuman memoria innecesaria o vuelvan confusa la explicación del flujo de datos durante la auditoría del Hito.

## Decisión Arquitectónica

* Se decidió implementar el control del tiempo de espera de forma pasiva y determinista utilizando una resta matemática simple basada en marcas de tiempo nativas (`Date.now()`). El circuito guarda de forma exacta el momento en el que se abre y, únicamente cuando ingresa una nueva petición, calcula el tiempo transcurrido. Se rechazan casi por completo los temporizadores automáticos del lenguaje (`setTimeout`/`setInterval`) y las dependencias externas de terceros se rechazan completamente.

## Consecuencias y Justificación

* \* \*\*Simplicidad y claridad absoluta (+):\
*\* El código se lee como mirar un reloj de pulsera: si la hora actual menos la hora del fallo supera el límite, el circuito se evalúa como listo. No hay procesos ocultos "corriendo en el fondo", facilitando que cualquier persona (incluido un evaluador o un CTO) entienda la lógica de inmediato de forma verbal.
* \* \*\*Pruebas 100% predecibles (+):\
*\* Al no depender de hilos o cronómetros asíncronos que actúan a la espalda del programa, las pruebas en `circuit-breaker.test.js` son rápidas, estables y no sufren de retrasos aleatorios por culpa del procesador.
* \* \*\*Comportamiento reactivo (-):\
*\* El circuito no cambia de estado "por sí solo" en el milisegundo exacto en que termina el castigo; requiere obligatoriamente que entre una petición para revisar el reloj y actualizarse.
* \* \*\*Lógica manual (-):\
*\* Al evitar librerías especializadas (como \*Opossum\*), nos vemos obligados a mantener, calcular y escribir la lógica matemática de las transiciones por nuestra propia cuenta en el archivo `circuit-breaker.js`.

