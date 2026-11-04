# Implementación del integrador

## 1. Correspondencia con el modelo conceptual

El programa está separado por responsabilidades. `config` declara y valida parámetros; `domain` identifica clientes, recursos y resultados; `randomness` produce entradas independientes de las decisiones; `engine` ejecuta las reglas. `metrics`, `statistics` y `experiments` convierten trazas en evidencia. `validation` comprueba invariantes con contabilidad independiente del calendario.

El motor no importa ni adapta el simulador de una práctica. Su diseño deriva del modelo conceptual del integrador. Utiliza biblioteca estándar y un calendario de eventos implementado con `heapq`.

La cobertura incluye los mecanismos de la especificación: algunos quedan desactivados en referencia porque sus probabilidades o conductas no fueron cuantificadas en los bloques. Los ejemplos identifican los supuestos nuevos necesarios para ejecutar. No se entrena un predictor ni se presenta el simulador como gemelo digital.

## 2. Tiempo y orden de eventos

El día 0 es lunes. El tiempo cero de cada día son las 8:00. La admisión termina en el minuto 840, correspondiente a las 22:00. El minuto 1440 es la apertura siguiente. El simulador conserva la fila entre franjas y vacía el día antes de comenzar el siguiente; si invade esa apertura, detiene la semana como inviable.

En cada instante se procesan finalizaciones, cierre y cambios de disponibilidad, llegadas y después asignaciones. Las llegadas simultáneas conservan su orden original dentro de cada prioridad. En empate entre paciencia y recurso libre se permite comenzar la atención; el abandono sólo afecta a quien sigue esperando después de asignar recursos.

Una pausa solicitada durante atención comienza completa después de finalizarla. Si otra pausa se solicita antes de completar una previa, las duraciones pendientes se acumulan. Fin de turno y ausencia no interrumpen servicios. Su prolongación se registra como trabajo adicional cuando supera el fin programado del turno.

Las cajas que deben cerrar terminan el cliente actual sin tomar otro. Las filas individuales de una caja que deja de aceptar clientes se redistribuyen a cajas habilitadas. No se borran entidades por cambios de capacidad.

## 3. Parámetros principales

Todos los tiempos están en minutos. El JSON se convierte a dataclasses inmutables. Los errores de unidades, agendas, probabilidades, intervalos o modalidades detienen la ejecución con un mensaje.

| Campo | Significado |
|---|---|
| `bands` | Nombre, inicio, fin, tasa de llegada normal y cajas solicitadas por franja |
| `promotion_day`, `promotion_multiplier` | Día de promoción y multiplicador sobre la tasa normal |
| `demand_multiplier` | Multiplicador general de demanda; distinto de alargar la corrida |
| `products_min`, `products_max` | Uniforme discreta de productos |
| `promotion_products_multiplier` | Escenario de canasta mayor en promoción; redondea a entero, mínimo uno |
| `cash_fraction`, `priority_fraction` | Probabilidades de efectivo y prioridad; la segunda se exige explícita |
| `scan_minutes` | Tiempo por producto; el factor de cajero sólo modifica esta etapa |
| `digital_payment_minutes`, `cash_payment_minutes` | Duraciones de cobro según medio |
| `mode` | `normal`, `rapida_exclusiva` o `rapida_flexible` |
| `queue_mode` | `unica` o `individuales` |
| `quick_limit` | Máximo de productos elegibles; no acelera artificialmente la caja |
| `switch_threshold` | Opcional: diferencia mínima de longitud, incluyendo ocupados, para cambiar fila voluntariamente; mínimo dos |
| `cashiers` | Agenda explícita de cajeros: identificador, días, inicio, fin, velocidad, pausas y ausencias |
| `rejection_probability` | Probabilidad por intento digital; efectivo no se rechaza en este modelo |
| `max_payment_attempts`, `retry_delay` | Cantidad máxima de intentos digitales y demora entre ellos |
| `payment_exhaustion` | `fallida`: salida con venta fallida; `efectivo`: un cobro final en efectivo |
| `patience_minutes` | Opcional: paciencia fija de ejemplo para quien aún espera; no interrumpe atención |
| `reactive_threshold`, `reactive_extra_boxes` | Cola que solicita reserva y cantidad adicional, respetando cinco cajas y personal disponible |
| `reactive_delay`, `reactive_min_open` | Demora de activación y permanencia mínima de la capacidad extra solicitada |
| `hourly_wage`, `overtime_wage_multiplier` | Costo por hora y multiplicador de tiempo posterior al fin de turno; salario opcional |
| `assumptions` | Procedencia y advertencias concretas de los valores del escenario |

Un cajero tiene pausas `(inicio solicitado, duración)` y ausencias `(día, inicio, fin)`. Los cajeros de un turno son personas distintas de los del siguiente en el ejemplo. El programa no decide si las jornadas cumplen legislación o convenios; eso requiere restricciones acordadas y datos operativos.

La dotación debe estar definida: no se crea un cajero al abrir una caja. En referencia hay personal de reserva ocioso si la política abre menos de cinco. Para comparar dotaciones distintas se puede suministrar otra agenda o activar `--ajustar-dotacion`, que construye cobertura sintética por franja y sustituye turnos, velocidades, pausas y ausencias originales. El manifiesto marca esa sustitución; no se debe interpretar la descripción de la agenda original como la agenda efectiva de esa variante.

## 4. Colas y caja rápida

La prioridad social precede a FIFO entre quienes son elegibles y esperan. La caja 1 es la rápida cuando se activa esa modalidad y se asigna primero, para evitar ocupar una normal si la rápida está libre simultáneamente.

En fila única una normal puede atender cualquier cliente, incluida una compra pequeña. La rápida exclusiva sólo atiende elegibles. La flexible prefiere elegibles y puede tomar una compra grande al quedar sin ellos; no interrumpe ese servicio si después llega alguien con pocos productos. La excepción queda registrada.

En filas individuales se elige la fila habilitada de menor longitud, contando al cliente en atención, y se desempata por número de caja. La prioridad actúa dentro de la fila. La rápida flexible puede tomar clientes de otras filas cuando no tiene elegibles en la propia. Los cambios obligatorios por cierre y los voluntarios habilitados se contabilizan. Esta es una regla de comportamiento propuesta, no una observación real del supermercado.

## 5. Entradas comunes y escenarios

Las semillas se derivan con SHA-256 y no con `hash()` de Python, que cambia entre procesos. Hay flujos separados por día, franja y mecanismo: llegadas, productos, pagos y prioridad. Los sorteos de rechazo se identifican por semilla, cliente e intento. Cambiar la política o el orden de atención no cambia esos sorteos.

Las llegadas se generan por franja y se cortan en cada frontera. No se conserva una llegada futura sorteada con la tasa de una franja anterior. Cambiar sólo prioridad conserva llegadas, canastas y medios de pago; cambiar sólo la modalidad de atención conserva todos los clientes.

Cada réplica es una semana independiente. Dentro de una comparación se usan las mismas semillas entre alternativas. Los cambios en las tasas o canastas conservan flujos comparables, pero producen entradas distintas porque precisamente son factores del experimento.

## 6. Métricas e interpretación

`cohortes.csv` usa día y franja de llegada. Un cliente que llega por la mañana y termina por la tarde pertenece a la cohorte matutina. El P95 de espera se calcula entre quienes comenzaron atención; `p95_total` utiliza quienes terminaron. Pagos fallidos, abandonos y pendientes se informan al lado para evitar sesgo de supervivencia.

`cumple_espera` sólo evalúa el umbral. `cumple_servicio` agrega ausencia de abandonos, pagos fallidos y pendientes. La recomendación automática usa el segundo, como criterio conservador declarado. Si el estudio acepta tolerancias distintas, deben acordarse y cambiarse explícitamente. Las celdas sin clientes no prueban cumplimiento ni se rellenan con un percentil cero.

Las áreas de cola, ocupación, cajas habilitadas y personal presente se integran por tiempo. Se exportan utilización y throughput por franja de finalización, por separado de las cohortes. En una transición puede haber cajas ocupadas pendientes de cierre por encima de las solicitadas, sin exceder las cinco físicas.

`horas_caja` integra cajas habilitadas, incluyendo las que terminan una atención antes de cerrar. `horas_cajero` incluye personal disponible sin caja asignada y pausas pagadas. Las ausencias se excluyen de presencia cuando el cajero no está completando un servicio. `horas_cajero_extra` incluye toda prolongación posterior al fin de un turno; `horas_cajero_post_cierre` sólo el tiempo posterior al cierre comercial. Son cantidades distintas.

La recuperación puede calcularse con `recovery_time` sobre los intervalos de una corrida con traza: necesita fijar fin de perturbación, umbral de cola y permanencia mínima. No se confunde un cruce instantáneo con una recuperación sostenida. Los experimentos masivos no conservan intervalos individuales para limitar memoria; las finalistas se pueden ejecutar con traza.

## 7. Inferencia y decisión

Se calcula primero el P95 en cada día/franja de cada semana. Para resumir el criterio conjunto se registra su máximo semanal. La media de esos máximos no equivale al P95 global de clientes.

Los intervalos de medias usan Student con desviación entre réplicas. La cuantila se calcula numéricamente mediante la beta incompleta y está contrastada con cuantiles tabulados, incluyendo pocos grados de libertad. Wilson estima la proporción de semanas que cumplen; treinta éxitos en treinta réplicas no equivalen a probabilidad verdadera uno.

Las diferencias entre alternativas se emparejan por semilla y se expresan como alternativa menos referencia. Las semanas inviables no tienen una métrica de espera de semana completa: se conserva la observación parcial con otro nombre y se las excluye de los intervalos de medias y las diferencias pareadas. Las estadísticas declaran si quedan condicionadas a semanas completas. El fracaso sí se conserva en la proporción de cumplimiento semanal. Las semanas sin una métrica observable se identifican como excluidas; no se reemplazan por cero. Los experimentos inviables se contabilizan y no califican para una recomendación.

El nivel de confianza y la meta de cumplimiento son parámetros diferentes. Sin meta no se selecciona una política. Con meta, el programa exige límite inferior Wilson suficiente, todas las réplicas observables y ausencia de semanas inviables. Después ordena por horas de cajero y de caja. Es una selección exploratoria con intervalos por alternativa; la confirmación de finalistas requiere otras réplicas y un procedimiento que considere selección múltiple.

Los rangos de sensibilidad son escenarios, no distribuciones de incertidumbre inventadas. La precisión deseada y el tamaño definitivo de muestra deben decidirse después del piloto.

## 8. Pruebas y límites de evidencia

La suite incluye resultados manuales, el caso D/D/1 de diez productos y tarjeta, prioridades, simultaneidad, colas, cambios de capacidad, pausas, ausencias, cambios de turno, elegibilidad, pagos, abandono, apertura reactiva, costos, sobretiempo, continuidad diaria y escenarios inviables.

También comprueba conservación, áreas temporales, no superposición de recursos, comparación con mayor capacidad, independencia de flujos aleatorios, cuantiles estadísticos, exportaciones, CLI y diseños experimentales. Los escenarios aleatorios usan semillas fijas y comprueban invariantes; no exigen que una muestra casual reproduzca exactamente una media teórica.

El verificador de cada corrida contrasta el área de cola con las esperas acumuladas, la ocupación con las duraciones de atención y la capacidad con el personal presente. Una violación detiene la exportación experimental como error; una configuración operativamente inviable es un resultado del modelo y queda identificada como tal.

Estas pruebas verifican la implementación. La calibración y validación con observaciones reales siguen pendientes. No hay un módulo que prometa calibrar automáticamente un supermercado sin datos ni una red neuronal entrenada con observaciones inexistentes.

## 9. Automatización

Se incluye la plantilla `docs/ci-tests.yml` para ejecutar la suite en GitHub Actions con Python 3.11 y 3.12 al subir cambios o abrir una propuesta. Todavía no está activada: GitHub rechazó crear `.github/workflows/tests.yml` porque el token disponible no incluye el permiso `workflow`. Quien administre el repositorio puede instalarla en esa ruta con una sesión autorizada. La plantilla usa las acciones oficiales [checkout](https://github.com/actions/checkout) y [setup-python](https://github.com/actions/setup-python). La suite local funciona sin ese permiso y usa el mismo comando previsto para la automatización.
