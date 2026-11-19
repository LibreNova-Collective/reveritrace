# Evidencia de validación de ReveriTrace 1.0.1

| Comprobación | Resultado |
|---|---|
| ZIP recibido y bundle Git | CRC de las tres entradas, verificación del bundle y `git fsck --full --strict` correctos |
| Commit original | bf07784c7aa9cf4ee471d644c9c67dd53f075427, autor y committer con identidad del proyecto |
| Historial con LSA disponible | 37 pruebas correctas, incluyendo fallos de importación, seguridad y regresión |
| Historial con biblioteca estándar | 35 pruebas correctas y 2 omitidas por ausencia de scikit-learn; el retorno a búsqueda léxica sí se probó |
| Sitio y paquete | 8 pruebas correctas; cuatro páginas y ambos ZIP se verificaron por HTTP local |
| Automatización | actionlint v1.7.12 validó la sintaxis de ambos flujos |
| Dependencias opcionales | pip-audit sin avisos para las seis versiones registradas en el inventario de terceros |
| Privacidad del repositorio | Revisión de autoría, archivos de texto, inventario, iconos PNG y patrones de secretos con Gitleaks |

SHA-256 del ZIP recibido: `ab5a1d6305c5559c34d7d06e6abb3ad80c183cfd10c0e793ce0b870b54bfc5bb`.

SHA-256 del bundle importado: `0553e409fd3735f89dbad5e63932f175f159a5a02bbcf0542cb4404bcb1fd06f`.

El generador guarda las sumas de cada build en `dist/build-status.json` o en el directorio escogido con `--output`. El ZIP de la skill es de vista previa. Se verificaron el inventario, el CRC, el manifiesto y el icono de 512 × 512. Las cuatro URL públicas, la identidad del editor, los escaneos del portal y la ejecución con modelos reales quedan pendientes.

El ensayo de publicación utiliza datos sintéticos. Comprueba identidad y fecha visibles, soporte, destino geográfico, las cuatro rutas y la igualdad de manifiestos en ambos ZIP.
