# Third-party inventory and compliance checklist
SPDX-License-Identifier: AGPL-3.0-only (this document only)

No third-party library code, pre-trained weights, runtimes, package caches, credentials or dataset exports are bundled. Original software is AGPL-3.0-only. Dependencies are independently installed by the executor; their own licenses and notices continue to apply. Compatibility is not a substitute for checking all transitive and platform-specific dependencies and provenance at the exact release being distributed.

| Component | Role | Declared / upstream license | Version observed in local test |
|---|---|---|---|
| Python | CLI runtime | PSF-2.0 (check full notices) | Python runtime; see test environment |
| SQLite | local index | public domain dedication | runtime SQLite |
| NumPy | LSA | BSD-3-Clause (bundled components have separate notices) | 2.3.5 |
| SciPy | LSA dependency | BSD-3-Clause (check bundled notices) | 1.17.0 |
| scikit-learn | LSA | BSD-3-Clause | 1.8.0 |
| joblib | LSA dependency | BSD-3-Clause | 1.5.3 |
| threadpoolctl | LSA dependency | BSD-3-Clause | 3.6.0 |
| tzdata | optional timezone database | Apache-2.0 | 2026.2 |
| sentence-transformers | optional neural runtime | Apache-2.0 upstream | not installed |
| transformers | optional neural runtime | Apache-2.0 upstream | not installed |
| PyTorch | optional neural runtime | BSD-3-Clause plus third-party notices | 2.10.0+cpu; neural inference not tested |
| safetensors | optional model format library | Apache-2.0 | 0.7.0; neural inference not tested |

References: https://www.gnu.org/licenses/license-compatibility.en.html ; https://www.gnu.org/licenses/license-list.html ; https://github.com/huggingface/sentence-transformers/blob/main/LICENSE ; https://github.com/huggingface/transformers/blob/main/LICENSE ; https://github.com/pytorch/pytorch/blob/main/LICENSE ; https://github.com/huggingface/safetensors/blob/main/LICENSE ; https://www.python.org/about/legal/ ; https://sqlite.org/copyright.html .

Before distribution: confirm ownership/permission for original code and assets; preserve full license and notices; make Corresponding Source (including build/install scripts needed by recipients) available in accordance with AGPL; if deploying a modified network service, comply with section 13; do not add terms restricting AGPL freedoms; retain exact dependency and model notices and sources where required; review marketplace terms for conflicts. If publishing a bundled distribution, re-audit the entire dependency closure, native libs and model artifacts. No commercial restrictions on AGPL code, required donations, or additional conditions on downstream recipients. This is a technical license inventory, not a formal legal audit or a vulnerability certification.

## Revisión técnica de preparación 1.0.1

Sin dependencias obligatorias de PyPI: búsqueda léxica, importación, base SQLite, pruebas y generador funcionan con la biblioteca estándar. PSF-2.0, BSD-3-Clause y Apache-2.0 son compatibles con GPLv3 para este análisis de integración con AGPLv3, preservando los avisos y condiciones de cada licencia. SQLite declara dominio público. La distribución revisada contiene código original y recursos del proyecto, sin ruedas, bibliotecas nativas ni pesos.

En el entorno opcional observado se consultó pip-audit para NumPy 2.3.5, SciPy 1.17.0, scikit-learn 1.8.0, joblib 1.5.3, threadpoolctl 3.6.0 y tzdata 2026.6. Sin avisos reportados para esas versiones en el momento de la consulta. Las pruebas del cargador neuronal usan dobles de prueba. La licencia y procedencia de un modelo real dependen del artefacto y su revisión exacta. La distribución futura de un runtime o sus pesos requiere revisar la cadena completa, incluyendo las dependencias nativas y las obligaciones de avisos y fuente.
