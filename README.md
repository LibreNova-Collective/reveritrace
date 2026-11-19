# ReveriTrace – entrega de publicación sin coste

Licencia del código original y del generador: AGPL-3.0-only. El texto oficial está en `plugin/LICENSE`; modelos externos no incluidos. No publicar la vista previa como política definitiva.

## Vista previa
`python build_site.py` genera `dist/site/`. Abrir `index.html` o ejecutar `python -m http.server 8000 --directory dist/site`. No hay servidor de historial ni backend. `ReveriTrace-source.zip` contiene código correspondiente, scripts de generación y documentación. `ReveriTrace-plugin.zip` contiene la skill.

## Publicación gratuita
1. Crear o seleccionar una organización GitHub Free con nombre público aprobado para el proyecto. No usar una cuenta personal identificable sin autorización. Revisar la visibilidad de membresía y configurar el correo noreply para futuros commits. No se garantiza anonimato frente al proveedor ni frente a metadatos ya públicos.
2. Crear un repositorio público independiente (sin historial personal, DB, tokens o modelos) y habilitar Issues. Usar un canal de soporte que no solicite datos de reproducciones. Revisar los términos y prácticas reales; el editor debe aprobar las políticas, derechos de distribución, identidad y fecha.
3. Guardar localmente una configuración JSON con `publisher`, `base_url` (URL real asignada por GitHub Pages), `support_url` (canal real del proyecto), `effective_date` (YYYY-MM-DD), `publisher_verified`, `policies_approved`, `rights_confirmed` (booleanos verdaderos solo tras confirmar), y opcionalmente `all_available_countries` o `countries` (ISO alpha-2). No usar valores inventados. No incluir el archivo de configuración en repositorio si contiene información privada.
4. `python build_site.py --approved-config /ruta/config.json`. Subir solo `dist/site/` al origen de Pages, por ejemplo raíz de la rama main. Activar Settings > Pages > Deploy from a branch. Validar las cuatro páginas index.html, support.html, privacy.html, terms.html sin iniciar sesión. Verificar que el enlace de soporte y ambos ZIP funcionan. No prometer disponibilidad hasta comprobarla. Si el portal exige token de dominio, publicar exactamente el archivo/token pedido por el portal (no credenciales).
5. Descargar y revisar `ReveriTrace-plugin.zip` del sitio o usar la copia local. Crear borrador en portal de OpenAI con identidad verificada, ejecutar validaciones y confirmar personalmente declaraciones legales, disponibilidad geográfica y política. No equivale a aprobación. El directorio público requiere revisión. No se incluye un MCP remoto: esta versión usa archivos propios y ejecución compatible.

## Sin gastos
GitHub Pages para repositorios públicos y organizaciones GitHub Free no requiere dominio de pago. No activar funciones de pago, servicios de IA alojados ni evaluaciones de seguridad pagadas. Google Data Portability API requiere verificación adicional para actividad YouTube; puede requerir auditoría. No desplegar OAuth hasta confirmar requisitos y coste cero. Mantener Takeout como alternativa explícitamente autorizada.

Referencias oficiales:
- https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages
- https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site
- https://developers.openai.com/plugins/deploy/submission
- https://developers.openai.com/plugins/plugin-guidelines
- https://developers.google.com/data-portability

Estado: sitio local y paquete de vista previa. Alojamiento, identidad verificada, publicación de políticas y aprobación del marketplace pendientes. No se ha creado una cuenta pública ni aceptado acuerdos en nombre del editor.
