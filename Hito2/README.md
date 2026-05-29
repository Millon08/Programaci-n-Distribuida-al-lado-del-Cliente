# Proyecto Integrador - Semana 10 (Hito 2)

## Requisitos Previos
- **Node.js**: v18.x o superior (usa `node -v` para comprobarlo)

## Instalación
Este proyecto ha sido desarrollado utilizando **JavaScript puro** sin dependencias externas (cero librerías, sin framework de testing de terceros). 
Por lo tanto, **no es necesario** ejecutar `npm install`.

## Comandos Disponibles

### 1. Ejecutar el Cliente Integrado y Generar Log
Demuestra el funcionamiento orquestado del Circuit Breaker y Token Manager:
```bash
node cliente-integrado.js > demo_resiliencia.log
```
*(Puedes revisar el archivo `demo_resiliencia.log` para ver la salida con las 3 fases del circuito).*

### 2. Ejecutar Pruebas (Tests)
Para ejecutar las pruebas automatizadas (basadas en el módulo nativo `node:assert`):
```bash
node circuit-breaker.test.js
```
**Salida esperada:**
Verás en consola cómo pasan todos los casos (INV-A2, apertura del circuito, rechazo rápido y TC-X2) imprimiendo "✅ Todas las pruebas pasaron correctamente."

## Estructura de Archivos (Hito 2)
- `circuit-breaker.js`: Lógica base del Circuit Breaker.
- `token-manager.js`: Lógica de autenticación.
- `cliente-robusto.js`: Coordinador principal.
- `cliente-integrado.js`: Punto de entrada y simulación.
- `circuit-breaker.test.js`: Pruebas.
- `*.md / *.txt`: Documentación requerida (ver archivos adyacentes).
