# Contract: Autenticación (Historia 1)

Todas las rutas de este contrato son públicas (no requieren JWT), excepto donde se indique.
Cubre FR-001 a FR-006.

## POST /api/auth/registro

Alta de un nuevo usuario (FR-003).

**Request**:
```json
{ "email": "usuario@dyp.com", "password": "string, mínimo 8 caracteres" }
```

Sin otro requisito de composición (no exige mayúscula, número ni símbolo — ver Clarifications
2026-07-22 en `spec.md`).

**Response 201**:
```json
{ "id": 1, "email": "usuario@dyp.com" }
```

**Response 409** (email ya registrado, FR-003):
```json
{ "detail": "El email ya está registrado" }
```

**Response 422**: validación de formato de email o password con menos de 8 caracteres.

## POST /api/auth/login

**Request**:
```json
{ "email": "usuario@dyp.com", "password": "string" }
```

**Response 200**:
```json
{ "access_token": "jwt...", "token_type": "bearer", "expires_at": "2026-07-22T12:00:00Z" }
```

Token JWT con claim `exp` a 24 h desde la emisión (FR-006, ver `research.md` §6).

**Response 401**: credenciales inválidas. No hay bloqueo de cuenta ni rate limiting ante intentos
fallidos repetidos (ver Clarifications 2026-07-22 en `spec.md`) — cada intento fallido responde
401 de forma independiente.

## Todas las demás rutas del sistema

MUST requerir header `Authorization: Bearer <token>` válido y no expirado (FR-002, FR-004).

**Response 401** ante token ausente, inválido o expirado — el frontend MUST redirigir a la
pantalla de login al recibir un 401 en cualquier request (FR-002).
