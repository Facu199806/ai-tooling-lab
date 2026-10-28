# AI Tooling Lab

Laboratorio público para experimentos reproducibles con herramientas de agentes de IA. Solo usa datos inventados.

## Estado

- **PoC 00**: preflight de contenedor remoto, **NO EJECUTADO**.
- **PoC 01**: Headroom, **BLOQUEADO** hasta completar preflight, grafo de dependencias y aprobación separada.
- Sin secretos, inferencias, repositorios privados, instalaciones globales ni conexiones a agentes externos.

## Flujo de trabajo

1. Revisar la PR borrador y la política de seguridad.
2. Revisar el SHA de `actions/checkout` y seleccionar un digest inmutable de la imagen Ubuntu.
3. Tras aprobación explícita, habilitar el workflow manual desde la rama predeterminada.
4. Ejecutar **solo** `headroom-preflight` con un digest `sha256:...` de imagen previamente validado.
5. Revisar los controles y logs; cualquier FAIL detiene la PoC.
6. Autorizar por separado, si corresponde, la futura descarga con hash y benchmark offline.

No hay integración automática demostrada con ningún host de agente. Un resultado compacto seleccionado por una herramienta no equivale a interceptar todo el contexto de un agente.

[Política de seguridad](docs/SECURITY.md) · [Matriz de controles](docs/PREFLIGHT.md) · [Diseño del benchmark](docs/BENCHMARK.md)
