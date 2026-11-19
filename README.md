# ReveriTrace 1.0.1

ReveriTrace busca vídeos y pistas de YouTube Music en archivos de historial que el usuario tiene autorización para tratar. Usa SQLite en un entorno de ejecución compatible y admite filtros de fechas, repeticiones y pistas en español, inglés y japonés. El código original se distribuye bajo AGPL-3.0-only. Los pesos de modelos y las dependencias externas se instalan por separado.

## Uso y compilación

- [Manual de usuario](kit/docs/01-GUIA-USUARIO.md)
- [Arquitectura y mantenimiento](kit/docs/02-TECHNICAL-AND-MAINTENANCE.md)
- [Publicación y verificación](PUBLISHING.md)
- [Licencias de terceros](kit/docs/08-THIRD-PARTY.md) y [modelos externos](kit/docs/09-EXTERNAL-MODELS.md)

Con Python 3.11 o posterior, ejecuta `python build_site.py` y sirve la vista previa con `python -m http.server 8000 --bind 127.0.0.1 --directory dist/site`. La salida contiene el sitio estático, el ZIP de la skill y el ZIP de código correspondiente. Los enlaces de políticas del ZIP de vista previa se incorporan al generar la edición aprobada.

```sh
python -m unittest discover -s plugin/skills/youtube-history/scripts -v
python -m unittest -v test_site
```

Alojamiento público y distribución oficial pendientes de las aprobaciones y verificaciones de [publicación](PUBLISHING.md).
