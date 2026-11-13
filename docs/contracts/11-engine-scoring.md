# CT-11 — `ScoringEngine.calculateScore` / `ScoringEngine.determineCategory`

| | |
|---|---|
| **Versión** | 1.1 (2026-11-12) — incorpora hallazgos F-01…F-21 de la auditoría de contratos |
| **Estado** | Propuesto |
| **Trazabilidad** | `REQ-01` · AC-01.1 · `BR-05` · NFR de precisión numérica · `02` §1.1 (`calculateScore`, `determineCategory`), §2.3 · `01` §3.2 (Diagrama A), §3.4 · `ADR-0001` |
| **Contratos relacionados** | Lo invoca CT-10 |

Este archivo documenta **dos operaciones independientes** del motor de dominio en memoria. Ninguna lee ni escribe en base de datos ni en red, y ninguna importa `repository`, `models` ni `service` (`docs/estructura_repositorio.md` §4.1).

## 1.A `calculateScore(answers) -> Decimal`

* **Componentes involucrados:** Solicita `CategorizationService` y provee `ScoringEngine` (en Python, `calculate_score(self, answers: list[ScoredAnswerDTO]) -> Decimal`).
* **Precondiciones (garantiza el solicitante):** `answers` no está vacía. Cada elemento trae `optionValue: Decimal` y `weight: Decimal >= 0`, ambos creados desde `str` o `NUMERIC`, **nunca** desde `float` (`docs/code_style.md` §4.1).
* **Postcondiciones (garantiza el proveedor):** Retorna `totalScore = Σ (optionValue × weight)` calculado solo con aritmética `Decimal`, sin conversiones a `float`.
* **Invariantes:** Determinista (mismas entradas → mismo resultado) y sin efectos secundarios. Si todos los `optionValue` son `>= 0`, `totalScore >= 0`.
* **Fallos:** Lista vacía o algún valor que no sea `Decimal` → `InvalidInputError`. Esa excepción la captura CT-10 y la convierte en el flujo `BR-06`.

## 1.B `determineCategory(score) -> FinancialCategory`

* **Componentes involucrados:** Solicita `CategorizationService` y provee `ScoringEngine` (en Python, `determine_category(self, score: Decimal) -> FinancialCategory`).
* **Precondiciones (garantiza el solicitante):** `score` es un `Decimal >= 0` producido por 1.A.
* **Precondiciones de configuración (garantiza quien construye el motor):** Umbrales internos `conservativeThreshold < moderateThreshold`, ambos `Decimal`. Sus valores numéricos dependen de producto/finanzas (`02` §5). Los umbrales son conocimiento oculto del motor y no se persisten (`02` §2.1).
* **Postcondiciones (garantiza el proveedor), con desempate conservador `BR-05`:**
  * `score <= conservativeThreshold` → `CONSERVATIVE`
  * `conservativeThreshold < score <= moderateThreshold` → `MODERATE`
  * `score > moderateThreshold` → `AGGRESSIVE`
  
  Un puntaje exactamente igual a un umbral cae siempre en la banda de **menor** riesgo.
* **Invariantes:** Determinista y sin efectos secundarios. **Nunca** devuelve `UNDER_EVALUATION`: esa categoría solo la asigna CT-10 en el flujo `BR-06`.
* **Fallos:** `score` negativo o que no sea `Decimal` → `InvalidInputError` (capturada por CT-10 → `BR-06`).

## 2. Estructura esencial (`.json`)

```json
{
  "calculateScore": {
    "input": {
      "answers": [
        { "questionId": "int", "optionValue": "Decimal", "weight": "Decimal >= 0" }
      ]
    },
    "output": { "totalScore": "Decimal" }
  },
  "determineCategory": {
    "input": { "score": "Decimal >= 0" },
    "output": { "assignedCategory": "FinancialCategory (CONSERVATIVE | MODERATE | AGGRESSIVE)" }
  }
}
```

## 3. Ejemplos verificables (umbrales ilustrativos: `conservativeThreshold = 50.00`, `moderateThreshold = 80.00`)

| `score` | Resultado esperado | Motivo |
|---|---|---|
| `Decimal("49.99")` | `CONSERVATIVE` | Banda inferior |
| `Decimal("50.00")` | `CONSERVATIVE` | Empate en umbral → menor riesgo (`BR-05`) |
| `Decimal("50.01")` | `MODERATE` | Banda intermedia |
| `Decimal("80.00")` | `MODERATE` | Empate en umbral → menor riesgo (`BR-05`) |
| `Decimal("80.01")` | `AGGRESSIVE` | Banda superior |

*Los valores de los umbrales son solo de ejemplo: los reales los definirá producto/finanzas (`REQ-01`, Dependencias).*

## 4. Notas de alineación con `01`

* `01` §3.2 define `ScoringEngine.weightMatrix : Dict`. Como los pesos ya se persisten en `question.weight` y llegan dentro de cada `ScoredAnswerDTO`, ese atributo debería guardar **solo los umbrales** (por ejemplo, renombrarlo a `thresholds`). Así se evitan dos fuentes de verdad para los pesos (`02` §2.3, §6).
