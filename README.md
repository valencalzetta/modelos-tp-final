# Trabajo integrador - Modelos y Simulación

Simulación de eventos discretos de la operación de cajas de un supermercado con **cinco cajas instaladas**. Diseño propio basado en los tres bloques integradores y la teoría disponible. Las prácticas anteriores son consulta de implementación.

## Requisitos y ejecución

Python 3.11 o superior. El modelo y sus tests usan únicamente la biblioteca estándar: no hace falta instalar dependencias para ejecutar desde esta carpeta.

Una semana, con trazas y comprobaciones:

```bash
python3 -m supermercado simular --config ejemplos/base.json --semilla 2026 --salida resultados/corrida_base
```

Tests:

```bash
python3 -m unittest discover -s tests -t . -v
```

Comparación de seis políticas, treinta semanas por política, con entradas comunes por semilla:

```bash
python3 -m supermercado experimentar --config ejemplos/base.json --plan comparacion --replicas 30 --semilla 2026 --salida resultados/comparacion_30
```

Ayuda:

```bash
python3 -m supermercado --help
python3 -m supermercado experimentar --help
```

## Qué representa

- Llegadas por franja, miércoles de promoción, canastas y medios de pago.
- Cinco cajas físicas, cajeros con agendas, pausas, ausencias y velocidades de escaneo.
- Prioridades sin interrumpir atenciones; fila única o filas individuales.
- Cajas normales, rápida exclusiva y rápida flexible, manteniendo el límite físico.
- Apertura y cierre por horario o apertura reactiva con demora y reserva de personal.
- Escaneo, cobro, rechazo digital, reintento y salida fallida o respaldo en efectivo.
- Abandono y cambios de fila configurables, con trazas y contabilidad de sus consecuencias.
- Fin de admisión a las 22, vaciado diario y horas adicionales. Una operación que invade la apertura siguiente se declara inviable y no se reinicia silenciosamente.

## Configuraciones y supuestos

[Base](ejemplos/base.json) conserva las tasas, canastas y tiempos de B2, con política 5/4/3 de B3 y cinco cajas físicas. Los bloques no daban proporción prioritaria ni agendas: el ejemplo propone **10 % prioritarios**, dos turnos sintéticos de siete horas con cinco cajeros cada uno y una pausa pagada de quince minutos escalonada. Estos valores están identificados como supuestos ilustrativos nuevos y necesitan revisión del grupo. No son datos observados ni una planificación laboral validada.

[Incidencias](ejemplos/incidencias.json) activa rechazos, reintentos y abandono con valores ilustrativos declarados. [Apertura reactiva](ejemplos/reactiva.json) muestra una regla de reserva y sus umbrales. Todas las opciones están en [la guía de implementación](docs/implementacion.md).

En referencia no hay rechazos ni abandono, como en B3. Sus mecanismos sí están implementados y cubiertos por tests. El salario es `null`: se informan horas sin inventar montos.

**Horas de caja y horas pagadas de cajero son diferentes.** Si se conserva la misma agenda, cerrar una caja no elimina el costo de un empleado que sigue presente. `--ajustar-dotacion` cambia explícitamente las agendas por cobertura sintética por franja y elimina las pausas y ausencias originales; sirve para explorar dotación, no para validar turnos reales.

## Experimentos

| Plan | Diseño |
|---|---|
| `comparacion` | Referencia y cinco cajas toda la jornada, cada una con normales, rápida exclusiva y rápida flexible |
| `capacidad` | Las 125 políticas de 1 a 5 cajas en las tres franjas, todas normales |
| `factorial` | 3 niveles de capacidad × 3 aumentos de promoción × 3 modalidades = 27 combinaciones |
| `sensibilidad` | Demanda, escaneo, efectivo, promoción, límite rápido e interacción demanda-escaneo |
| `estres` | Referencia, doble demanda, ausencia matutina en promoción y adverso combinado |

Los planes grandes pueden tardar: cantidad de combinaciones × réplicas × siete días. Treinta réplicas son un piloto; la precisión se evalúa con los intervalos, no por el número de corridas solamente.

`--confianza 0.90` controla los intervalos. `--meta-cumplimiento 0.90` es una decisión diferente: exigir evidencia sobre la proporción de semanas que cumplen. Si se omite la meta, el programa informa resultados sin inventar una alternativa ganadora. La selección automática es exploratoria; las finalistas requieren confirmación con nuevas réplicas y validación del caso.

## Resultados y evidencia

La corrida exporta clientes, cohortes por día y franja de llegada, recursos ponderados por tiempo, días, eventos, intervalos y un informe de invariantes. Los experimentos exportan resultados por réplica, estadísticas, intervalos t de Student, intervalos Wilson de cumplimiento semanal y diferencias pareadas por semilla.

Se distingue P95 de espera de P95 del tiempo total. Se muestran abandonos y pagos fallidos por separado; un bajo P95 entre atendidos no oculta esos resultados. El cumplimiento de espera y el cumplimiento completo del servicio son indicadores separados.

Cada ejecución conserva configuración completa, semillas, versión de Python y huella SHA-256 del código. `resultados/` queda fuera de Git; se regenera con los comandos anteriores.

## Organización

```text
supermercado/
  config.py         # Parámetros, agendas, validación y políticas de capacidad
  domain.py         # Clientes, registros y resultados
  randomness.py     # Entradas y flujos aleatorios separados por mecanismo
  engine.py         # Calendario de eventos y operación de clientes y recursos
  metrics.py        # Cohortes, recursos, costos y recuperación
  statistics.py     # Percentiles e inferencia entre réplicas
  validation.py     # Invariantes y comprobaciones de contabilidad
  experiments.py    # Diseños experimentales y exportación de evidencia
  __main__.py       # Interfaz de consola
 tests/             # Casos manuales, analíticos, aleatorios e integración
 ejemplos/          # Escenarios configurables con supuestos identificados
 docs/              # Modelo conceptual, fuentes, trazabilidad y guía
```

## Documentación del estudio

- [Modelo conceptual integrado](docs/modelo_conceptual.md).
- [Registro de supuestos](docs/registro_supuestos.csv).
- [Evidencia de verificación y corrida piloto](docs/verificacion.md).
- [Matriz de trazabilidad](docs/matriz_trazabilidad.csv).
- [Implementación, parámetros y alcance de las pruebas](docs/implementacion.md).
- [Plantilla opcional de CI](docs/ci-tests.yml): pendiente de activación con permiso `workflow` en GitHub.
- [Fuentes originales](docs/fuentes/).

La implementación y sus pruebas verifican reglas y consistencia. **Todavía no existe validación empírica del supermercado:** faltan observaciones reales, revisión de supuestos por el grupo y la meta probabilística final. Las unidades teóricas posteriores a la clase 10 requieren su material si se exige tratarlas.
