# CT-02 — `getCurrentUser` (Auth Dependency)

| | |
|---|---|
| **Versión** | 1.2 (2026-11-12) — define mecanismo provisional Fase 0 y formato de error 401 |
| **Estado** | Aprobado |
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

| Condición | Excepción de dominio | HTTP | Cuerpo de error | Estado resultante |
|---|---|---|---|---|
| Credencial ausente | `UnauthorizedError` | 401 | `{ "detail": "No autenticado" }` | La petición no llega a `SurveyManager` |
| Credencial mal formada, firma inválida o expirada | `UnauthorizedError` | 401 (mensaje uniforme) | `{ "detail": "No autenticado" }` | Ídem |
| Credencial válida de un `client` inexistente | `UnauthorizedError` | 401 (mensaje uniforme) | `{ "detail": "No autenticado" }` | Ídem |

## 3. Regla Provisional de Fase 0 (Walking Skeleton y Entorno de Desarrollo)

Dado que aún no existe un servicio emisor de tokens (login/JWT), en Fase 0 (`ENVIRONMENT=development`) la dependencia `get_current_user` implementa el siguiente mecanismo explícito, compartido por backend y frontend:

1. **Cabecera principal (`Authorization: Bearer <token>`):**
   - `dev-user-1` $\rightarrow$ resuelve a `UUID("00000000-0000-0000-0000-000000000001")` (Cliente A sembrado en BD). En el frontend (`frontend/src/api/httpClient.ts`), `resolveAuthToken()` utiliza `"dev-user-1"` como fallback provisional de Fase 0 cuando no hay token configurado ni en `localStorage` (desactivable con `VITE_ENABLE_DEV_AUTH=false`), permitiendo que el build de producción en la VM se autentique contra FastAPI.
   - `dev-user-2` $\rightarrow$ resuelve a `UUID("00000000-0000-0000-0000-000000000002")` (Cliente B sembrado en BD, utilizado para pruebas de violación de ownership $\rightarrow$ `404`).
   - `<client_uuid>` $\rightarrow$ si el token tiene formato UUID válido, se toma como `client_id`.
2. **Cabecera de respaldo opcional:** solo si `ALLOW_DEV_USER_HEADER=true` y no se envía `Authorization`, se acepta `X-User-Id: <client_uuid>`.
3. **Verificación obligatoria en BD (`src/core/models.py`):** en todos los casos, `get_current_user` verifica que el `client_id` resuelto exista en la tabla `client` (`ClientModel` en `backend/src/core/models.py`). Si la cabecera falta, el formato es inválido o la fila no existe, lanza `UnauthorizedError` $\rightarrow$ HTTP `401` con `{ "detail": "No autenticado" }`.

## 4. Estructura esencial (`.json`)

```json
{
  "input": {
    "authorization": "string (requerido; cabecera HTTP `Authorization: Bearer <token>`, en Fase 0 acepta `dev-user-1`, `dev-user-2` o `<client_uuid>`)"
  },
  "output": {
    "userId": "UUID (requerido; identificador verificado del cliente = client.client_id)"
  },
  "error401": {
    "detail": "No autenticado"
  }
}
```

## 5. Notas de alineación

* **Supuesto de diseño:** el mecanismo concreto de credencial (Bearer JWT, cookie de sesión u otro) depende del módulo de autenticación, que no está diseñado (`02` §5, "Módulo de autenticación y de Plan"). Este contrato fija la interfaz (credencial → `userId` o 401), no la tecnología.
