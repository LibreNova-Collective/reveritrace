# Publicación de ReveriTrace

El repositorio de preparación se mantiene privado. El commit importado utiliza el nombre de proyecto LibreNova Collective y un dominio de correo reservado `.invalid`. Antes de cambiar la visibilidad, el editor debe comprobar en GitHub la atribución del repositorio, registros de actividad y visibilidad de membresía. El servicio puede asociar un push a la identidad autenticada.

## GitHub Pages con coste adicional de $0

En GitHub Free, Pages está disponible para repositorios públicos. La edición privada se verifica localmente. Los trabajos alojados de estos flujos solo se ejecutan en repositorios públicos y en ejecutores estándar. Confirmar la opción gratuita aplicable antes de habilitar Pages. No contratar planes, dominios ni servicios.

1. El editor revisa la identidad pública de la organización, el derecho a distribuir el código y los recursos, las cuatro páginas y el tratamiento real de datos. Confirma una fecha efectiva y un canal de soporte público con ejemplos sintéticos.
2. Tras revisar atribución, contenidos y metadatos, el editor autoriza la visibilidad pública. En **Settings → Pages → Build and deployment**, elegir **GitHub Actions**. Usar la URL base asignada por GitHub.
3. Registrar la configuración aprobada en `pages-release.json`. Una variable de repositorio `PAGES_RELEASE_CONFIG` con el mismo formato, si está configurada, tiene prioridad. Ambos admiten solo datos destinados a publicación. Campos obligatorios de texto: `publisher`, `base_url`, `support_url` y `effective_date` (AAAA-MM-DD). El editor establece `publisher_verified`, `policies_approved` y `rights_confirmed` como booleanos JSON verdaderos después de sus verificaciones. Para el alcance geográfico, puede usar `all_available_countries: true` o `countries` con los códigos de los países escogidos.
4. Ejecutar manualmente **Publish approved ReveriTrace site** desde `main`. Con una configuración aprobada también se puede generar el resultado localmente con `python build_site.py --approved-config /ruta/config.json --output directorio-limpio`.
5. Sin iniciar sesión, abrir `index.html`, `support.html`, `privacy.html` y `terms.html` en la URL asignada. Comprobar identidad, fecha, enlaces internos, canal de soporte real y los dos ZIP. Comprobar que las cuatro URL coinciden con el manifiesto del paquete y registrar resultados.

[GitHub Pages y planes compatibles](https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages)

## Marketplace de ChatGPT

La candidata es una skill con scripts Python, sin MCP. El ZIP generado incorpora el icono original y las sugerencias de revisión. Probar la ejecución en el entorno de destino para confirmar qué funciones se pueden ofrecer. En el portal, seleccionar y verificar la identidad empresarial, confirmar países y el comportamiento comercial, verificar el dominio cuando se solicite, ejecutar los escaneos y revisar compatibilidad de términos de distribución con AGPL. El editor autorizado realiza las declaraciones legales. El envío a revisión y la publicación son pasos distintos.

[Lista de comprobación](kit/docs/03-SUBMISSION-CHECKLIST.md) · [Portal y proceso oficial](https://developers.openai.com/plugins/deploy/submission)
