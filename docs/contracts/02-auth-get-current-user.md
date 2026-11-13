# CT-02 — `getCurrentUser` (Auth Dependency)

| | |
|---|---|
| **Versión** | 1.1 (2026-11-12) — incorpora hallazgos F-01…F-21 de la auditoría de contratos |
| **Estado** | Propuesto |
| **Trazabilidad** | `REQ-01` · Riesgo de acceso no autorizado · NFR de seguridad y privacidad · `02` §1 (nota transversal: origen del `userId`) · `01` §2.2 (nota de autenticación) |
| **Contratos relacionados** | Lo consumen CT-01, CT-06 y CT-09 |

## 1. Descripción y características del contrato

* **Componentes involucrados:** Solicita `SurveyRouter` (inyección de dependencias de FastAPI, `Depends(get_current_user)`) y provee `Auth Dependency` (`getCurrentUser` en UML / `get_current_user` en Python). No es un componente nuevo: el módulo de autenticación no se diseña en la Entrega 1.
* **Precondiciones (garantiza el solicitante):** Ninguna sobre el contenido. La dependencia se ejecuta en el servidor en **cada** petición HTTP del Módulo `survey`; la `Web App` no la invoca directamente.
* **Validaciones del proveedor (entrada no confiable):** Verifica que la credencial exista, esté bien formada, tenga firma válida, no haya expirado y corresponda a un `client` existente.
* **Postcondiciones (garantiza el proveedor):** Retorna el `userId` del cliente autenticado (equivale a `client.client_id`). La identidad sale **exclusivamente** de la credencial verificada, nunca del cuerpo, la ruta ni los parámetros de la petición.
* **Invariantes:**
  * Ningún endpoint del Módulo `survey` se ejecuta sin un `userId` obtenido por esta dependencia.
  * La causa concreta del rechazo (expirada, mal formada, cliente inexistente) no se revela al cliente HTTP ni se registra junto con PII.
* **Efectos secundarios:** Ninguno (solo verifica el contexto).

## 2. Resultados de fallo

| Condición | Excepción de dominio | HTTP | Estado resultante |
|---|---|---|---|
| Credencial ausente | `UnauthorizedError` | 401 | La petición no llega a `SurveyManager` |
| Credencial mal formada, firma inválida o expirada | `UnauthorizedError` | 401 (mensaje uniforme) | Ídem |
| Credencial válida de un `client` inexistente | `UnauthorizedError` | 401 (mensaje uniforme) | Ídem |

## 3. Estructura esencial (`.json`)

```json
{
  "input": {
    "authorization": "string (requerido; cabecera HTTP `Authorization: Bearer <token>`)"
  },
  "output": {
    "userId": "UUID (requerido; identificador verificado del cliente = client.client_id)"
  }
}
```

## 4. Notas de alineación

* **Supuesto de diseño:** el mecanismo concreto de credencial (Bearer JWT, cookie de sesión u otro) depende del módulo de autenticación, que no está diseñado (`02` §5, "Módulo de autenticación y de Plan"). Este contrato fija la interfaz (credencial → `userId` o 401), no la tecnología.
