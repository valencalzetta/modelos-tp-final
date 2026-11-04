# Modelo conceptual integrado: operación de cajas de un supermercado

Versión 0.1 - 4 de noviembre de 2026.
Estado: especificación conceptual v0.1 conservada como fundamento. Implementación disponible en `supermercado/`; supuestos de ejecución y diferencias en `implementacion.md`.
No contiene resultados de simulación ni una recomendación experimental ya demostrada.

## 1. Propósito y pregunta de decisión

Estudiar la operación completa de la línea de cajas de un supermercado mediano con cinco cajas físicas instaladas, bajo variabilidad de demanda, tiempos de atención y disponibilidad de recursos. El propósito es comparar políticas de capacidad y atención, medir su desempeño y riesgo, y formular una recomendación condicionada por la evidencia.

Pregunta principal: ¿qué política de apertura de cajas por día y franja, y qué configuración de atención, permite cumplir el objetivo de espera usando eficientemente el personal disponible?

Preguntas complementarias:

- ¿Cuándo resulta conveniente destinar una de las cajas abiertas a compras pequeñas?
- ¿Qué consecuencias tiene esa decisión para compras grandes y clientes prioritarios?
- ¿Cómo cambia la recomendación ante promociones, mayores tiempos de atención, ausencia de personal o incidencias de pago?
- ¿Existe una solución dentro de las cinco cajas disponibles? Si no existe, ¿qué restricción y qué condiciones explican el incumplimiento?
- ¿Qué supuestos influyen más en la decisión y qué datos convendría medir primero?

El indicador de servicio heredado de los bloques es P95 de espera en fila menor que 10 minutos en cada combinación de día y franja. La utilización, las horas de cajero y el riesgo de incumplimiento completan la evaluación. No se establece un porcentaje mínimo de utilización sin justificarlo.

## 2. Fuentes y autoridad de las definiciones

Fuentes locales conservadas en `docs/fuentes/`:

- B1: `bloque_1.pdf`, trabajo conceptual sobre línea de cajas, tres páginas.
- B2: `bloque_2.pdf`, desarrollo de clases 4 a 7, seis páginas de un formulario mayor.
- B3: `bloque_3_y_plantilla_final.pdf`, dieciséis páginas; respuestas del bloque 3 en clases 8 a 11 y campos posteriores sin completar.
- T: `teoria_clases_1_a_10.md`, apuntes teóricos disponibles de clases 1 a 10.
- U: decisiones expresadas por la usuaria en esta conversación: cinco cajas instaladas; trabajo integrador con diseño propio; prácticas anteriores como consulta de implementación.

Prevalece U sobre valores anteriores incompatibles. Cuando B1, B2 y B3 difieren, este documento explica la resolución. Las decisiones adicionales son propuestas de diseño, no contenido textual de los bloques ni observaciones reales.

Las prácticas se pueden consultar para técnicas de programación, trazas y pruebas. Sus distribuciones, tiempos, resultados y números de servidores no calibran este supermercado. Tampoco se toma uno de sus programas como definición del integrador.

No se dispone todavía de la teoría completa posterior a la clase 10. B3 aporta preguntas sobre predicción y una plantilla de clases 12 a 16; los campos vacíos no permiten deducir sus requisitos de evaluación. La cobertura de esas unidades deberá contrastarse con su material o consigna cuando esté disponible.

## 3. Fundamento teórico y naturaleza del modelo

De las clases 1 y 2 se toma la separación entre sistema, entorno y frontera, así como entidades, atributos, recursos, estados, eventos, reglas y trazabilidad. De la clase 3 se toman la calidad de datos, las dependencias y la distinción entre variabilidad e incertidumbre.

El modelo será dinámico, estocástico y de eventos discretos. Representará cada cliente y cada recurso relevante. Las actividades duran intervalos; sus comienzos y finalizaciones son eventos. El reloj de simulación avanzará hasta el próximo evento y conservará el estado entre eventos.

Monte Carlo corresponde a repetir semanas independientes para estimar distribuciones de resultados. No reemplaza la lógica de eventos discretos. El diseño experimental, la sensibilidad, la verificación y la validación son partes del estudio, además del simulador.

La clase 5 fundamenta colas, utilización, latencia, throughput y capacidad. Las clases 6 y 7 fundamentan réplicas, escenarios, riesgo, viabilidad y resiliencia. Las clases 8 a 10 fundamentan experimentos comparables, sensibilidad, calibración y evidencia de validación.

## 4. Sistema, entorno, frontera y alcance

### Sistema representado

La operación de cajas desde que un cliente se presenta para pagar hasta que termina su atención o, en escenarios de abandono, se retira. Incluye clientes, filas, cinco cajas físicas, cajeros, asignaciones, atención, cobro, incidencias incluidas en el escenario y decisiones de capacidad.

### Entorno y entradas externas

El calendario comercial, las promociones, el flujo de clientes que llega a pagar, sus canastas y medios de pago, la disponibilidad programada del personal y los costos unitarios. No se simula la formación de precios ni la decisión de compra producto por producto.

La cantidad de productos y las promociones pueden ser entradas aunque su generación provenga del entorno. Estar fuera de la frontera no significa ignorar sus efectos sobre las cajas.

### Procesos sin representación detallada

Reposición, proveedores, inventario, recorrido por góndolas y contabilidad general no están desarrollados en los tres bloques. Sus efectos se reflejarán en entradas cuando corresponda. Incorporarlos requeriría nuevas preguntas, reglas y datos.

### Cobertura de mecanismos discutidos

- Núcleo definido por los bloques: llegadas por franja y día, productos, medios de pago, filas, prioridades, cajas abiertas, caja rápida, atención, cierre y métricas.
- Mecanismos mencionados que necesitan especificación adicional: turnos, pausas, cambios de cajero, ausencias, pagos rechazados y reintentos.
- Extensiones para contrastar supuestos explícitos de los bloques: abandono, heterogeneidad de cajeros y canastas mayores en promociones.
- Comparaciones estructurales adicionales: filas individuales y caja rápida flexible. B2 y B3 ya establecen fila única como configuración principal; las otras políticas deben identificarse por separado.

La arquitectura debe permitir esas variantes. Una variante sin parámetros acordados se registrará como pendiente o desactivada explícitamente; no se ejecutará con probabilidades ocultas ni se afirmará que fue estudiada.

## 5. Decisiones consolidadas y diferencias entre documentos

| Tema | Antecedente | Definición consolidada |
|---|---|---|
| Capacidad física | B2: hasta ocho; B3: pruebas de hasta seis por la mañana | Cinco cajas instaladas por U; ninguna política puede excederlas |
| Horario | B2: jornada de doce horas; B2/B3: 8 a 22 | 8 a 22, catorce horas de admisión diarias |
| Unidad | B2 menciona días y horas; servicios en minutos | Minutos internos; días y horas para calendario y presentación |
| Horizonte | Una semana | Siete días, cada uno con admisión 8 a 22 y atención posterior de pendientes |
| Referencia | B2: dos cajas; B3: 5/4/3 | Referencia experimental propuesta: 5 mañana, 4 tarde, 3 noche; no se presenta como una operación real observada |
| Colas | B1 abierto; B2/B3 fila única | Fila única con prioridades en la configuración principal |
| Caja rápida | Límite de diez productos; B2 también menciona flexibilidad | Comparar rápida exclusiva y, por separado, rápida flexible |
| Pagos fallidos | B2 los menciona; B3 los excluye de sus límites | Referencia documental sin rechazos; escenario de incidencias con reglas y parámetros explícitos |
| Abandono | B2/B3 lo excluyen | Desactivado en la referencia documental; extensión que debe tener datos o supuestos identificados |
| Velocidad de cajeros | B3 supone igualdad | Igual en referencia; heterogeneidad como contraste si se parametriza |
| Calentamiento | B3 no lo descarta | No se elimina: abrir con filas vacías es parte del sistema diario modelado |

La referencia 5/4/3 sirve para comparar. Su elección no implica que cumpla el objetivo. Tampoco se ajustará la demanda para forzar una alternativa ganadora.

## 6. Entidades, recursos y atributos

### Cliente

Identificador; día y franja de llegada; instante de llegada a pagar; cantidad de productos; medio de pago; categoría de prioridad; elegibilidad para caja rápida; fila y cambios de fila si esa variante está activa; inicio y fin de atención; caja y cajero asignados; duración de escaneo y cobro; incidencias y reintentos; espera acumulada; tiempo total; estado final.

En la extensión de abandono se agregan tolerancia de espera, instante de abandono y motivo. No se confunde retirarse de la fila con finalizar una compra.

### Caja física

Identificador entre 1 y 5; modalidad normal o rápida; estado cerrada, habilitada libre, ocupada, pendiente de cierre o fuera de servicio si esa perturbación está definida; cajero asignado; cliente actual; tiempos de apertura, ocupación, cierre y liberación.

Una caja rápida no es una sexta caja y no recibe una velocidad artificialmente mayor: su ventaja proviene de las canastas admitidas, salvo que exista evidencia de otra tecnología.

### Cajero

Identificador; agenda de disponibilidad; turno; descansos; presencia o ausencia; caja asignada; estado disponible, atendiendo, en pausa o fuera de turno; factor de velocidad si se estudia heterogeneidad; tiempo trabajado y horas adicionales.

En referencia, el factor de velocidad es uno. Las agendas y pausas aún deben definirse. Si se usa una disponibilidad agregada, tiene que declararse como supuesto y no presentarse como una simulación de turnos ya resuelta.

### Cola

Clientes esperando; orden de llegada; categorías de prioridad; elegibilidad por tipo de caja; longitud en el tiempo; política de selección. La fila principal no tiene límite físico en la referencia documental.

### Calendario y política

Día, franja, condición de promoción, tasa de llegada, apertura y cierre comercial, cajas planificadas, modalidad de atención y reglas de contingencia. Una política puede depender del horario o del estado de la fila si es una alternativa experimental explícita.

## 7. Entradas, estado, controles y resultados

| Tipo | Elementos |
|---|---|
| Entradas externas | Llegadas, productos, pago, prioridad, calendario, incidencias y disponibilidad de personal |
| Parámetros | Tasas por franja, distribución de productos, tiempos de escaneo y pago, probabilidades, costos y umbrales |
| Controles | Cajas solicitadas por franja, configuración de colas, modalidad rápida, asignación y reglas de contingencia |
| Estado | Reloj, clientes esperando y atendidos, colas, cajas, personal, servicios en curso y eventos futuros |
| Salidas | Esperas, tiempos totales, P95, utilización, throughput, horas de cajero, sobretiempo, incumplimientos y recuperación |

La cantidad de cajas abiertas es un estado que cambia mediante eventos y también es afectada por una decisión de control. El número de cinco cajas instaladas es una restricción fija del estudio.

## 8. Parámetros heredados y su interpretación

Los siguientes valores son supuestos escritos por el grupo en B2/B3, no mediciones reales:

| Entrada | Referencia | Tratamiento |
|---|---|---|
| Mañana | 8 a 13; un cliente por minuto | Tasa 1/min |
| Tarde | 13 a 18; 0,8 clientes por minuto | Tasa 0,8/min |
| Noche | 18 a 22; 0,5 clientes por minuto | Tasa 0,5/min |
| Promoción | Miércoles, aumento del 40 % | Multiplicar las tasas de ese día por 1,4 |
| Productos | Uniforme entre 1 y 40 | Enteros equiprobables; no cantidad continua |
| Medio de pago | 30 % efectivo y 70 % tarjeta/QR | Clasificación aleatoria; tarjeta y QR agrupados en referencia |
| Escaneo | 0,15 minutos por producto | Actividad dependiente de la canasta |
| Cobro | Un minuto tarjeta/QR; dos efectivo | Actividad posterior al escaneo |
| Caja rápida | Hasta diez productos | Elegibilidad, no prioridad social |
| Servicio objetivo | P95 de espera menor que diez minutos | Evaluado por día y franja de llegada |

La proporción de clientes prioritarios no está cuantificada en los bloques. También faltan agendas de personal, frecuencia y duración de pagos rechazados, reglas de reintento y costos monetarios. No se toman los valores de las prácticas como sustitutos.

En la referencia se propone independencia entre canasta, pago y prioridad, condicionando las llegadas por día y franja. Es un supuesto a documentar y contrastar. La posible asociación promoción-canasta grande está mencionada en B2 y requiere un escenario específico, no una dependencia inventada sin declarar.

La variabilidad de clientes individuales se muestrea dentro de cada corrida. La incertidumbre sobre las tasas, distribuciones y reglas se estudia entre escenarios o mediante un diseño de incertidumbre explícito. Los rangos de sensibilidad no se convierten automáticamente en distribuciones uniformes.

## 9. Dinámica y reglas operativas

### Llegadas y selección

El proceso de llegadas utiliza tiempos entre llegadas exponenciales dentro de cada franja, equivalentes a una tasa constante local. Al cruzar una frontera de franja debe aplicarse la tasa nueva; no se arrastra una llegada generada con una tasa anterior de forma incorrecta. No se generan llegadas fuera del horario comercial.

Al llegar, se registran los atributos y la franja original. Un cliente elegible puede ser atendido por una caja normal. Una compra que excede el límite no puede ir a la rápida exclusiva.

### Prioridades y orden

La prioridad social actúa entre clientes que esperan y son elegibles para el recurso. Dentro de cada categoría se respeta FIFO. No se interrumpe un servicio iniciado y no se desplaza a un cliente que ya está siendo atendido. Se corrige la expresión de B2: la categoría relevante es adulto mayor, no cualquier mayor de edad.

En la fila única todas las cajas normales consultan la misma cola. Para la rápida se mantiene una selección lógica de elegibles. Cuando coinciden cajas libres se propone asignar primero la rápida al primer elegible y luego las normales a los restantes, con desempates documentados. Esta convención debe ser estable y verificable.

### Modalidades de caja rápida

A: todas normales y fila única con prioridad.

B: igual cantidad total de cajas y personal, con una rápida exclusiva para canastas de hasta el límite. La rápida puede quedar ociosa si sólo esperan canastas no elegibles.

C: igual cantidad total, con una rápida flexible. Cuando no haya elegibles esperando, puede iniciar una compra grande de la cola normal. Ese servicio no se interrumpe si luego llega una compra pequeña. La excepción se registra para distinguirla de una infracción de la modalidad exclusiva.

### Atención y cobro

Servicio de referencia, en minutos: `S = 0,15 × productos + tiempo_pago`.

El escaneo y el cobro son actividades. Si se estudia una incidencia, un rechazo al finalizar un intento puede iniciar un reintento o cambio de medio de pago según la regla definida. Mientras la incidencia se resuelve se debe especificar si ocupa la caja; la propuesta inicial es que permanece ocupada. Hacen falta probabilidades, demoras y límite de intentos antes de ejecutar esa variante.

### Capacidad y personal

En todo instante: `0 <= cajas_operativas <= min(5, cajeros_presentes_y_disponibles)`.

Un cajero atiende como máximo una caja y una caja un cliente. Abrir una caja requiere recurso físico habilitado y cajero disponible. Los descansos y ausencias reducen la disponibilidad efectiva. Los cambios de turno deben mantener la trazabilidad de quién opera cada caja.

Al reducir la cantidad planificada, una caja ocupada queda pendiente de cierre y termina su atención antes de cerrar. No toma un nuevo cliente. Una pausa o fin de turno solicitado durante una atención se resuelve al finalizarla, registrando la demora o tiempo adicional. Esta transición puede producir una diferencia temporal entre capacidad solicitada y efectiva; se mide, no se oculta.

Las reglas de apertura reactiva necesitan umbral, duración mínima y personal de reserva. No se supondrá disponibilidad instantánea de un empleado adicional.

### Cierre y continuidad

A las 22 cesan las nuevas llegadas. En referencia se completa la atención de todos los presentes con los recursos que siguen habilitados para el cierre y se contabiliza el trabajo adicional. Una semana incluye siete cierres, no un único vaciado al final del domingo.

No se reinician las filas al cambiar de franja. El día siguiente abre vacío sólo si el vaciado y la disponibilidad de personal lo permiten. Si un escenario extremo extiende la atención hasta la apertura siguiente o viola una restricción de jornada, se registra como operación inviable y se revisa la política; no se borra la cola silenciosamente.

### Eventos

Llegada de cliente; inicio y fin de escaneo; inicio, resultado y reintento de pago si se desagregan; fin de atención; cambio de franja o día; apertura y cierre comercial; entrada y salida de turno; inicio y fin de pausa; apertura y cierre de caja; comienzo y fin de perturbaciones parametrizadas; abandono si está activo.

Los eventos simultáneos requieren un orden explícito: primero registrar finalizaciones y cambios de disponibilidad, después llegadas y finalmente asignar nuevos servicios con el estado actualizado. Los empates dentro de una categoría se resuelven por orden estable. No se pueden eliminar clientes por un cambio de capacidad.

## 10. Métricas y contabilidad

Por cliente se calcula espera `inicio - llegada`, servicio `fin - inicio` y tiempo total `fin - llegada`. Se conservará el detalle de etapas si hay incidencias. El P95 de espera no se reemplaza por el P95 del tiempo total.

Se agrupa principalmente por día y franja de llegada, aunque el servicio termine en otra franja o después del cierre. Por cada celda se informan cantidad de clientes, promedio, mediana, P90, P95, P99, máximo y proporción con espera de diez minutos o más. Se separan además clientes prioritarios, normales, canastas pequeñas y grandes.

Las longitudes medias de cola y utilización se calculan ponderando por tiempo. Las observaciones por evento sin esa ponderación sesgan esas métricas. La longitud máxima es un máximo temporal, no una media.

La utilización de atención es tiempo ocupado dividido por tiempo habilitado, con el intervalo observado claramente definido. Para capacidad cambiante se integra la disponibilidad efectiva. También se mide el trabajo respecto de horas pagadas de cajero para distinguir atención, ociosidad, pausas y disponibilidad.

Se registran throughput por hora de finalización, clientes aún pendientes al cierre, hora de vaciado, sobretiempo, número de aperturas, horas de cajero, cumplimiento por celda y cumplimiento semanal conjunto. La concurrencia se cuenta a partir de servicios en curso.

En perturbaciones se mide tiempo de recuperación y acumulación de cola. El criterio de recuperación requiere umbral y permanencia definidos antes del experimento.

Si hay abandono se reporta su frecuencia y espera por separado. No se celebra un menor P95 entre atendidos sin mostrar que parte de la demanda se retiró. Sin abandono y datos de compra no se estima pérdida monetaria de ventas.

Si no hay clientes en una celda, su percentil es no disponible, no cero. El método de cálculo de percentiles y las reglas de comparación se fijarán y documentarán.

## 11. Comprobación analítica previa

Con la uniforme discreta de uno a cuarenta, la media de productos es 20,5. El pago medio supuesto es 1,3 minutos. El servicio medio de referencia resulta:

`E[S] = 0,15 × 20,5 + 1,3 = 4,375 minutos`.

Cinco cajas idénticas ofrecen aproximadamente `5 × 60 / 4,375 = 68,57` atenciones por hora de capacidad media. La llegada matutina de referencia es 60 clientes/h y la del miércoles 84 clientes/h. La carga ofrecida aproximada de esa mañana es `1,4 × 4,375 / 5 = 1,225`.

En la mañana de descuento la demanda media excede la capacidad de las cinco cajas bajo estos supuestos. Esto anticipa acumulación durante esa franja. No prueba por sí solo un P95 exacto ni supone un régimen estacionario para toda la jornada.

El hallazgo debe orientar los experimentos y la defensa. Puede ocurrir que ninguna alternativa cumpla. Se estudiará la frontera de factibilidad dentro de las cinco cajas, y después cambios operativos explícitos si tienen fundamento, sin alterar silenciosamente los supuestos.

## 12. Diseño experimental

### Hipótesis a contrastar

H1: el efecto de agregar una caja depende de la franja y del nivel de demanda; aumenta cerca de la saturación.

H2: reservar una caja para compras pequeñas puede mejorar a ese segmento y empeorar a otros; el resultado general depende de la proporción de elegibles y de la capacidad restante.

H3: una política conveniente en referencia puede incumplir bajo incertidumbre o perturbaciones; la recomendación requiere evaluar robustez.

Estas afirmaciones son hipótesis, no resultados establecidos.

### Familias de experimentos

E1, capacidad: comparar políticas horarias con entre una y cinco cajas abiertas. La referencia propuesta es 5/4/3. El espacio de políticas constantes por franja tiene 125 combinaciones, algunas deliberadamente insuficientes; puede filtrarse por cotas analíticas antes de una búsqueda detallada. Las decisiones específicas de miércoles se prueban después con reglas y capacidad documentadas.

E2, configuración: comparar A, B y C con exactamente la misma política de personal y capacidad total, así como los mismos clientes dentro de cada réplica. El límite rápido base es diez. Una comparación con una sola caja se define con cuidado: dedicarla de forma exclusiva puede dejar clientes sin recurso elegible y constituye una configuración inviable, no una espera finita.

E3, promoción y escalabilidad: días normales y miércoles con aumentos del 20, 40 y 60 % sobre la tasa normal. Son multiplicadores 1,2; 1,4; 1,6, no aumentos sucesivos sobre 1,4. El doble de demanda es una prueba adicional separada.

E4, sensibilidad: llegadas de referencia +/-20 %, escaneo entre 0,10 y 0,20 minutos por producto, efectivo entre 10 y 50 %, límite rápido de cinco, diez y quince productos. Son rangos propuestos en B3; se deben revisar contra la plausibilidad del caso. Se combina análisis uno por vez con interacciones demanda-escaneo y demanda-capacidad. La dependencia promoción-canasta requiere una distribución alternativa explícita.

E5, riesgo y resiliencia: miércoles con mayor demanda, un cajero menos y mayor proporción de efectivo. Una ausencia completa, una interrupción temporal y una pausa programada son eventos diferentes y se experimentan por separado. Los rechazos de pago se incorporan cuando estén definidos. Se mide degradación y recuperación.

E6, estructura: fila única frente a filas individuales, abandono y heterogeneidad, si se desarrollan los supuestos necesarios. Para filas individuales hacen falta regla de elección, posibilidad de cambio y reglas de cierre de cada fila. No se agregan esas conductas de forma implícita.

No se cruza indiscriminadamente todo con todo. Primero se verifica el mecanismo, luego se exploran políticas, se comparan las candidatas y se someten las finalistas a sensibilidad y estrés. Todo escenario ejecutado tiene un identificador y configuración conservada.

## 13. Réplicas, incertidumbre y comparación estadística

Cada réplica representa una semana y utiliza una realización nueva e independiente respecto de las demás semanas. Se propone un piloto de treinta semanas por configuración, conforme a B3. Treinta no garantiza precisión suficiente; tampoco alcanza con que el promedio cambie poco entre veinte y treinta.

Se propone fijar, antes del estudio definitivo, nivel de confianza y precisión deseada. El 90 % de confianza se considera una opción motivada por el ejemplo de la consigna, pendiente de confirmar como requisito. Una semiamplitud de 0,5 minutos para métricas decisivas sería una propuesta de precisión, no una exigencia de la materia. El piloto sirve para planificar un tamaño de muestra final común para las alternativas comparadas.

Para comparar alternativas se precalculan entradas externas por réplica o se separan flujos aleatorios por mecanismo. Se reutilizan las mismas llegadas, productos, pagos y prioridades al comparar políticas. Una misma semilla no basta si cada alternativa consume números aleatorios en diferente orden. Las réplicas entre sí sí cambian de semilla.

Por réplica r y celda j se calcula `Q[r,j] = P95 de espera`. Además se conserva `Z[r] = máximo_j Q[r,j]` e `I[r] = 1 si todas las celdas evaluables cumplen Q[r,j] < 10`. Así se distingue el cumplimiento por franja del cumplimiento de toda la semana.

Se estima la variación entre semanas, los intervalos de confianza para los resúmenes de interés y la probabilidad semanal de cumplimiento con un intervalo binomial apropiado. Si se publican afirmaciones simultáneas sobre muchas celdas, se debe controlar la multiplicidad o usar un criterio conjunto predefinido.

Al comparar A y B se analiza la diferencia pareada por semana, acompañada de su intervalo y relevancia práctica. Se diferencia incertidumbre de estimación, dispersión entre semanas y dispersión entre clientes. No se tratan todos los clientes de una semana como réplicas independientes del experimento.

El promedio de los P95 semanales no es el P95 de todas las esperas agrupadas. Ambos pueden describirse, pero responden preguntas diferentes. P95 tampoco equivale a horas pico: es un percentil de una distribución definida.

El porcentaje mínimo aceptable de semanas que cumplen debe acordarse. Un 90 % de confianza estadística no implica un 90 % de semanas satisfactorias. Si se adopta una meta probabilística, se declarará como decisión del estudio y se evaluará con su incertidumbre.

## 14. Verificación, calibración y validación

### Verificación conceptual

Revisar consistencia entre cinco cajas físicas, personal disponible, reglas de elegibilidad, prioridades, horizonte, estados y eventos. Ninguna decisión de capacidad debe crear recursos sin disponibilidad ni dejar clientes sin una regla de salida.

### Verificación de implementación

Casos determinísticos con resultados manuales: una caja y dos clientes; llegadas simultáneas; llegada al terminar un servicio; dos cajas; paso entre franjas con fila pendiente; cierre durante atención; pausa y cambio de turno; prioridad que no interrumpe; cliente no elegible para rápida exclusiva; excepción flexible; rechazo y reintento si ese módulo está activo.

Caso analítico de B3: una llegada cada dos minutos, diez productos y tarjeta, servicio de 2,5 minutos y una caja. Para clientes numerados desde cero, la espera esperada es `0,5 × índice` si se comienza con la primera llegada en cero.

Invariantes: `fin >= inicio >= llegada`; esperas no negativas; identidad de cliente conservada; ausencia de atenciones superpuestas por caja y cajero; capacidad física máxima cinco; personal suficiente para nuevas asignaciones; elegibilidad; conservación entre llegados, atendidos, abandonados y pendientes; horas consistentes con la traza.

Con la cola vaciada y sin abandonos, la cantidad atendida debe igualar la cantidad llegada. En una variante con abandono, la conservación es llegados = atendidos + abandonados + pendientes; no se aplica la igualdad anterior de forma incorrecta.

### Comprobaciones de coherencia

Casos sin llegadas, llegadas espaciadas, sobrecarga y capacidad holgada. Un único servidor no implica necesariamente una cola siempre creciente: depende de demanda y servicio. Una proporción mayor de efectivo aumenta el trabajo esperado bajo la regla base, pero no se impone que cada muestra finita muestre un incremento estricto del P95.

La Ley de Little puede usarse en condiciones compatibles o mediante contabilidad de áreas e intervalos correctamente delimitados. No se aplica como identidad estacionaria sin ajustes a cualquier franja transitoria.

### Calibración y validación

Los bloques declaran ausencia de datos reales. Se deben etiquetar los valores actuales como supuestos. Tickets y registros de caja ayudan a estimar canastas, medios de pago y atención, pero sus horas de cobro no identifican por sí solas la llegada a la fila ni la espera. Para validar esperas se requieren observaciones adicionales.

La validez aparente requiere revisión por una persona que conozca la operación; no se declara realizada hasta hacerla. Para validación empírica se separan datos de ajuste y datos de contraste, preferentemente en orden temporal. Se fijan métricas y tolerancias coherentes con su calidad.

La coincidencia con casos manuales o referencias sintéticas verifica procedimientos y consistencia; no demuestra que el supermercado real se comporte igual. Se documentará un expediente de evidencia con pruebas, errores, correcciones y límites.

## 15. Viabilidad, criterios de decisión y recomendación

Viabilidad técnica: cajas físicas, terminales de pago y espacio para filas. Viabilidad operativa: personal, turnos, pausas, control de elegibilidad y ejecución de contingencias. Viabilidad económica: horas normales y adicionales, costos de implementación y costos unitarios cuando se disponga de ellos. Viabilidad temporal: tiempo para implementar cambios de atención y organización.

En ausencia de salarios y otros costos, se comparan horas de cajero y sobretiempo. No se asignan montos ficticios ni se usa la utilización como sustituto exacto del costo. Abrir cinco cajas todo el día suma setenta horas de caja diarias; una agenda real debe explicar cuántas personas y turnos las cubren.

La selección considera primero factibilidad física, operativa y cumplimiento con incertidumbre; luego compara consumo de recursos, equidad entre grupos y robustez. Si varias políticas tienen ventajas distintas, se presenta el compromiso y el criterio explícito de elección.

Una recomendación futura deberá contener: política, condiciones de aplicación, evidencia de mejora, intervalos o probabilidades correctamente identificados, costos o recursos, alternativas descartadas con motivos, riesgo residual y señales que activan revisión.

Si ninguna política con cinco cajas satisface el objetivo bajo las entradas supuestas, la conclusión será esa. Después se podrán estudiar cambios operativos fundamentados o la revisión del objetivo con el destinatario de la decisión. La falta de una alternativa satisfactoria también es evidencia.

## 16. Predicción y contenidos posteriores

B3 plantea predecir clientes por franja usando día, promoción y antecedentes. También decide no incorporar predicción por ahora, porque no hay datos reales de entrenamiento. Se conserva esa justificación: el flujo se genera por escenarios documentados.

Si se obtienen datos, la evaluación predictiva debe incluir baseline, partición temporal, error por tipo de día, incertidumbre y efecto del error sobre la decisión de cajas. Un menor error predictivo no garantiza automáticamente una mejor decisión operativa.

Las secciones de redes neuronales, modelos híbridos y gemelos digitales están vacías en el archivo recibido. No se afirma que deban implementarse todos. Si la consigna completa exige tratarlos, se deberá fundamentar su pertinencia o su exclusión con la teoría correspondiente. Un simulador sin vínculo de actualización con una entidad física no se denominará gemelo digital por tener una visualización.

## 17. Arquitectura prevista del proyecto propio

La separación de responsabilidades propuesta para la implementación es:

- Configuración y validación: parámetros, políticas, escenarios, fuentes y restricciones.
- Generación de entradas: llegadas y atributos reproducibles, dependencias y flujos aleatorios.
- Motor de eventos: reloj, calendario, clientes, cajas, cajeros y transiciones.
- Políticas: selección de clientes, prioridades, rápida, apertura, cierre y contingencias.
- Métricas: trazas, integración temporal, cohortes y contabilidad de recursos.
- Experimentos: combinaciones, réplicas, identificadores y reproducción.
- Análisis: incertidumbre, comparaciones pareadas, sensibilidad, riesgo y decisión.
- Verificación: casos manuales, invariantes y pruebas de mecanismos.

Los nombres de archivos y librerías se definirán al implementar. Esta arquitectura deriva del modelo y de las preguntas del integrador. Las prácticas sólo ofrecen técnicas puntuales.

Productos previstos: código ejecutable, configuración declarada, diccionario de datos, trazas, resultados por réplica y celda, tablas de comparación, gráficos, evidencia de pruebas, análisis de sensibilidad y recomendación. Una animación puede ayudar a comunicar, pero no sustituye la evidencia estadística.

## 18. Definiciones pendientes antes de ejecutar el estudio definitivo

1. Proporción de clientes prioritarios y fundamento del supuesto.
2. Agenda de cajeros, turnos, pausas y disponibilidad de reserva para cada política.
3. Regla completa y parámetros de rechazo, reintento y cambio de medio de pago.
4. Si se estudiarán abandono y cambio de fila, y con qué comportamiento parametrizado.
5. Dependencia entre promoción y tamaño de compra, y eventual heterogeneidad de cajeros.
6. Costos unitarios, restricciones de jornada y criterio para contabilizar horas adicionales.
7. Meta probabilística de cumplimiento, nivel de confianza y precisión final deseada.
8. Reglas y parámetros de apertura reactiva, si se incluye esa política.
9. Acceso a observaciones para validación y teoría de las unidades posteriores si su cobertura es obligatoria.

Estas faltas no impiden diseñar el integrador. Impiden presentar esas variantes como implementadas, calibradas o validadas sin completar sus definiciones. El registro de supuestos identifica qué se hereda, qué se resolvió y qué queda abierto.
