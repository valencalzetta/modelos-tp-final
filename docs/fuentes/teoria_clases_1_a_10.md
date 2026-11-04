# Modelos y Simulación

## Clase 1 - Sistemas, modelos y simulación

Un **sistema** es un conjunto de elementos que interactúan y producen determinados comportamientos o resultados. Antes de modelarlo, es necesario definir qué se quiere estudiar y con qué propósito.

La **frontera del sistema** separa aquello que será representado explícitamente de lo que se considerará parte del entorno. Dentro de esa frontera se identifican los componentes relevantes y, sobre todo, sus **interacciones**, dependencias, flujos y retroalimentaciones.

El **modelo conceptual** describe entidades, reglas, procesos y supuestos sin depender todavía de un lenguaje de programación. El **modelo computacional** traduce ese modelo conceptual a estructuras, algoritmos y datos ejecutables. El código no debería incorporar comportamientos que no estén justificados en el modelo conceptual.

La **simulación** consiste en ejecutar el modelo, mientras que un **experimento** determina qué condiciones se modifican, cuántas veces se ejecuta y qué métricas se observarán.

En todo modelo conviene distinguir:

- **Entradas**: variables que afectan al sistema.
- **Estado**: información mínima necesaria para describir su condición en un momento y determinar cómo puede evolucionar.
- **Salidas**: resultados observables producidos por el modelo.

Las transiciones permiten pasar de un estado a otro y, en modelos dinámicos, suelen estar asociadas a eventos. Es importante no confundir variables de entrada o controlables con resultados derivados.

Los modelos pueden ser **descriptivos, explicativos, predictivos o prescriptivos**; también pueden clasificarse como **estáticos o dinámicos** y **determinísticos o estocásticos**.

La **abstracción** determina qué aspectos de la realidad se conservan en el modelo, mientras que la **granularidad** indica con qué nivel de detalle se representa cada elemento. Más detalle no siempre implica un mejor modelo: debe incorporarse únicamente cuando afecta las decisiones o la validez del análisis.

<aside>
💡

La modelización es una práctica de selección, argumentación y contraste. El simulador no reemplaza el conocimiento del sistema ni decide por la organización: permite experimentar sobre una representación explícita. La calidad depende de la coherencia entre propósito, frontera, variables, datos, reglas, implementación, experimentos y conclusiones. Cada número producido debe poder explicarse mediante esa cadena.

</aside>

## Clase 2 - Construcción del modelo conceptual

Una situación problemática suele mezclar **síntomas, interpretaciones y propuestas de solución**. La primera tarea de modelización es separarlos y formular con claridad qué pregunta debe responder el modelo.

Una **entidad** es un objeto distinguible que participa del proceso y posee atributos relevantes para su comportamiento. Las **reglas** determinan cómo se comportan y relacionan las entidades frente a distintas condiciones; por ejemplo, una regla FIFO establece qué entidad será atendida primero.

Los **flujos** representan el recorrido de entidades, información o trabajo entre componentes. Pueden existir dependencias secuenciales, paralelas, opcionales o de retroceso.

Los **recursos** brindan un servicio y poseen una **capacidad** limitada o una disponibilidad condicionada. El modelo debe indicar si esa capacidad es fija, variable, compartida o afectada por fallas.

Los **diagramas** ayudan a representar la estructura y dinámica del sistema, pero no reemplazan las definiciones, reglas y supuestos escritos.

Las **métricas** convierten el propósito del modelo en resultados observables y comparables. El **alcance** establece qué procesos, usuarios, condiciones y horizontes serán representados, y también qué queda explícitamente fuera del modelo.

La **trazabilidad** conecta la pregunta original con variables, reglas, datos, código, experimentos y resultados. Antes de programar se realiza una **verificación conceptual**, buscando contradicciones, omisiones o supuestos mal definidos.

En síntesis, construir el modelo conceptual significa decidir **qué representar, cómo funciona y qué se medirá**, antes de comenzar con la implementación.

## Clase 3 - Datos, variabilidad e incertidumbre

Un modelo puede estar bien planteado y aun así producir resultados poco útiles si utiliza datos o parámetros inadecuados. Por eso es importante entender de dónde provienen los **datos**, cómo fueron generados y si son apropiados para el propósito del estudio.

La calidad de los datos puede analizarse en términos de **completitud, consistencia, exactitud, oportunidad, unicidad y adecuación al propósito**. También debe evaluarse su **representatividad**, es decir, si permiten razonar razonablemente sobre la población y las condiciones que realmente interesan.

La **granularidad temporal** determina con qué nivel de agregación se observan los fenómenos. Un promedio puede ocultar comportamientos importantes, como picos breves de demanda.

Para describir los datos no alcanza con una sola medida. **Media, mediana y moda** resumen el centro de maneras diferentes; **rango, varianza, desvío estándar y rango intercuartílico** describen dispersión; y los **percentiles** indican qué proporción de observaciones se encuentra por debajo de determinado valor. También deben observarse características como **asimetría, multimodalidad y colas pesadas**, que pueden quedar ocultas detrás de un promedio.

Otro aspecto importante es la **dependencia** entre variables: si dos variables tienden a cambiar conjuntamente, asumir que son independientes puede alterar los resultados de la simulación.

Finalmente, conviene distinguir dos ideas:

- **Variabilidad**: el fenómeno realmente presenta diferencias o cambios.
- **Incertidumbre**: nosotros no conocemos con precisión un valor, parámetro o incluso parte de la estructura del sistema.

Esta diferencia será importante más adelante para decidir qué debe modelarse como comportamiento variable y qué representa falta de conocimiento.

## Clase 4 - Fundamentos de simulación de eventos discretos

La **simulación de eventos discretos** representa sistemas cuyo estado cambia cuando ocurren sucesos identificables. Es especialmente útil cuando queremos modelar llegadas, colas, asignación de recursos, fallas, recuperaciones o procesos que ocurren en momentos determinados.

El **tiempo de simulación** representa la evolución temporal del sistema modelado y no tiene por qué coincidir con el tiempo real de ejecución. Por ejemplo, el programa puede simular meses de funcionamiento en pocos segundos. Para interpretarlo correctamente deben definirse la unidad de tiempo y el horizonte de simulación de forma coherente con los datos.

Un **evento** ocurre en un instante y puede modificar el estado del sistema, crear entidades o programar eventos futuros. Una **actividad**, en cambio, tiene una duración y puede consumir recursos. Esta diferencia es central: **el evento sucede en un punto del tiempo; la actividad ocupa un intervalo**.

Las **demoras** representan esperas que no corresponden directamente a un servicio, mientras que el **servicio** describe el tiempo y los recursos necesarios para atender una entidad.

Durante el desarrollo puede utilizarse una **traza** (registro de eventos, tiempos y estados) para reconstruir paso a paso la ejecución y comprobar que la lógica del modelo sea correcta.

En síntesis, este tipo de simulación representa la evolución del sistema como una secuencia de eventos que modifican su estado a lo largo del tiempo.

## Clase 5 - Colas y rendimiento informático

Muchos sistemas informáticos comparten **recursos limitados**, por lo que es necesario analizar qué ocurre cuando la demanda se acerca o supera la capacidad disponible.

Una **cola** aparece cuando una entidad solicita un recurso que no puede atenderla inmediatamente. Para modelarla hay que conocer cómo llegan las entidades, cuánto tarda su atención y qué regla determina quién será atendido primero.

La **tasa de llegada** indica cuántas entidades ingresan por unidad de tiempo. El **tiempo de servicio** indica cuánto tarda en atenderse una entidad y, en un sistema simple, su inversa representa la **tasa de servicio**. Además del tiempo efectivo de procesamiento, pueden existir bloqueos y tiempos externos.

La **utilización** indica qué proporción de la capacidad disponible está ocupada. Una utilización cercana al máximo no necesariamente es deseable: cuando un sistema se aproxima a la saturación, las colas y los tiempos de espera pueden crecer rápidamente.

La **latencia** es el tiempo total entre una solicitud y su respuesta, e incluye espera, procesamiento, comunicación y posibles bloqueos. El **throughput** representa cuántas entidades se completan por unidad de tiempo. La **concurrencia** indica cuántas entidades se encuentran activas simultáneamente.

Las **disciplinas de cola** determinan qué entidad será atendida primero, por ejemplo FIFO o prioridades. Una política de prioridades también puede generar **starvation** (una entidad espera indefinidamente porque otras reciben prioridad continuamente).

La **Ley de Little** establece que, en un sistema estable, el número promedio de elementos dentro del sistema es igual a la tasa promedio de llegada multiplicada por el tiempo promedio que permanecen en él. Puede utilizarse como comprobación de coherencia del modelo.

Finalmente, la **escalabilidad** describe cómo cambia el desempeño cuando aumenta la demanda o se agregan recursos. No debe suponerse que esa relación es lineal: la simulación permite detectar saturaciones, cuellos de botella y umbrales de capacidad.

En síntesis, analizar rendimiento implica estudiar conjuntamente **demanda, capacidad, espera, utilización, latencia y throughput**, ya que mejorar una métrica puede afectar a las demás.

## Clase 6 - Monte Carlo y generación de escenarios

La **simulación de Monte Carlo** se usa cuando un sistema tiene variables que no conocemos con certeza. En vez de asignarles un único valor, las representamos mediante **distribuciones de probabilidad** (formas de describir qué valores puede tomar una variable y con qué probabilidad) o mediante distintos escenarios posibles. Luego, el programa genera valores **pseudoaleatorios** y ejecuta el modelo muchas veces.

Cada ejecución o **corrida** produce un resultado distinto. Al repetir el proceso muchas veces mediante **réplicas independientes** (ejecuciones separadas del mismo modelo con nuevas realizaciones aleatorias), se obtiene una distribución de resultados posibles. Esto permite analizar no solo el promedio, sino también la variabilidad, la probabilidad de superar cierto límite y escenarios más conservadores mediante **percentiles**, como por ejemplo el P90.

Para que la simulación sea confiable, es importante elegir correctamente las distribuciones de entrada, considerar posibles **dependencias entre variables** y utilizar buenos generadores de números pseudoaleatorios. Estos generadores parten de una **semilla** (valor inicial que determina la secuencia de números generados), que puede registrarse para repetir exactamente una simulación si es necesario.

También es necesario realizar suficientes réplicas hasta alcanzar cierta **convergencia** (momento en que las estimaciones comienzan a estabilizarse al aumentar la cantidad de simulaciones).

Por último, no toda la incertidumbre se representa únicamente cambiando valores numéricos. A veces existen **escenarios estructurales** distintos, es decir, situaciones donde cambia directamente la estructura o las reglas del modelo, y conviene analizarlos por separado aplicando Monte Carlo dentro de cada uno.

En síntesis, Monte Carlo permite **transformar la incertidumbre de las entradas en una distribución de resultados**, para entender no solo qué puede pasar, sino también con qué probabilidad y con qué nivel de riesgo.

## Clase 7 - riesgo y variabilidad de proyectos

La **viabilidad** de una alternativa no depende de una sola cosa, sino de varias dimensiones que deben analizarse en conjunto. Una solución puede ser técnicamente posible, pero no necesariamente viable si resulta demasiado costosa, difícil de operar o imposible de implementar en los tiempos disponibles.

Por eso, normalmente se analiza:

- **viabilidad técnica:** si la solución puede cumplir los requisitos de rendimiento, compatibilidad, seguridad y mantenimiento
- **viabilidad operativa:** si puede sostenerse con los procesos, personas y capacidades disponibles
- **viabilidad económica:** si sus costos y beneficios son aceptables
- **viabilidad temporal:** si puede implementarse y producir resultados dentro de los plazos necesarios

A esto se suma el análisis de **riesgo**, entendido como la combinación entre la posibilidad de que ocurra un evento y la magnitud de sus consecuencias. La **exposición** representa cuánto se podría perder considerando tanto el impacto como la frecuencia de esos eventos. Sin embargo, no todos los impactos tienen que expresarse necesariamente en dinero: también pueden analizarse pérdidas de servicio, tiempo, información o reputación.

Para decidir qué riesgos son aceptables se utilizan conceptos como **apetito de riesgo** (nivel general de riesgo que una organización está dispuesta a asumir) y **tolerancia al riesgo** (límites concretos de desviación que se aceptan respecto de un objetivo).

El análisis también debe considerar **escenarios adversos**  y realizar **pruebas de estrés**  para identificar puntos de quiebre y entender cómo se degrada el sistema.

Otro concepto importante es la **resiliencia,** la capacidad del sistema de resistir, adaptarse y recuperarse frente a fallas o perturbaciones. No importa solamente evitar una falla, sino también cuánto afecta al sistema y cuánto tarda en recuperarse.

Finalmente, cuando existen **varias alternativas, deben compararse utilizando los mismos escenarios, métricas y supuestos**. La decisión no debería reducirse a elegir una opción como “la mejor” en términos absolutos, sino formular una **recomendación condicionada**: indicar qué alternativa resulta conveniente bajo determinadas condiciones, qué riesgos siguen existiendo y qué indicadores deberían monitorearse.

En síntesis, este capítulo busca mostrar que evaluar una alternativa implica analizar conjuntamente **viabilidad, riesgo y resiliencia**, para determinar no solo si una solución puede funcionar, sino también si puede implementarse, sostenerse y responder adecuadamente ante situaciones desfavorables.

## Clase 8 - Diseño de experimentos de simulación

→ Un simulador no produce conocimiento automáticamente. Hay que diseñarlo para que después los resultados realmente permitan sacar una conclusión defendible.

Antes de ejecutar una simulación, es necesario definir una **pregunta experimental** clara, es decir, qué cambio queremos estudiar y qué resultado queremos observar. La pregunta debería ser concreta y medible, por ejemplo analizar cómo cambia una métrica determinada cuando se modifica alguna característica del sistema.

A partir de esa pregunta se plantea una **hipótesis,** una afirmación o expectativa sobre qué efecto debería producir un cambio y que luego puede contrastarse mediante el experimento.

En el experimento se definen **factores** (variables que se modifican deliberadamente) y sus **niveles** (los distintos valores o configuraciones que puede tomar cada factor). Por ejemplo, si la cantidad de servidores es un factor, sus niveles podrían ser 1, 2 o 4 servidores.

Los efectos de esos cambios se observan mediante **variables de respuesta** (métricas utilizadas para medir el resultado del experimento), como tiempo de respuesta, costo o cantidad de errores. Al mismo tiempo, otras variables deben mantenerse constantes como **variables controladas**, para que las diferencias observadas puedan atribuirse realmente a los factores modificados.

Para comparar alternativas se define un **escenario base** (situación de referencia contra la cual se comparan las demás) y distintos **escenarios alternativos** (configuraciones o decisiones posibles). También pueden incluirse **escenarios extremos** para analizar los límites del sistema y detectar fragilidades.

Cuando existe aleatoriedad, una sola ejecución no es suficiente. Se deben realizar suficientes **réplicas** para distinguir efectos reales de variaciones causadas por el azar.

También es necesario elegir un **horizonte de simulación** coherente con la pregunta experimental. En algunos modelos se utiliza además un **período de calentamiento** (fase inicial que se descarta para evitar que las condiciones iniciales artificiales influyan en los resultados).

Finalmente, para que las comparaciones sean confiables, los experimentos deben ser **reproducibles**: se deben registrar configuraciones, datos, semillas, versiones del modelo y procedimientos utilizados.

En síntesis, la idea central es que **simular no consiste simplemente en ejecutar un programa muchas veces**. Primero hay que formular una buena pregunta, decidir qué variables modificar y medir, establecer escenarios comparables y después interpretar los resultados. La calidad del estudio depende más de estas decisiones metodológicas que de la herramienta utilizada para programar la simulación.

## Clase 9 - Análisis de sensibilidad

Un resultado de simulación depende de valores, reglas y estructuras elegidos por el equipo. La sensibilidad es especialmente importante cuando existen datos insuficientes o parámetros estimados con incertidumbre.

El **análisis de sensibilidad** estudia cómo cambian los resultados de un modelo cuando modificamos deliberadamente sus entradas, parámetros o supuestos. Su objetivo principal es identificar qué variables influyen realmente en las conclusiones y cuáles tienen poco impacto.

Es importante distinguir **sensibilidad** de **incertidumbre**. La sensibilidad indica cuánto cambia la salida cuando cambia una entrada, mientras que la incertidumbre indica cuánto desconocemos el valor real de esa entrada. Una variable puede ser muy incierta pero afectar poco al resultado, o estar bien medida y ser extremadamente influyente. Por eso conviene analizar ambas cosas en conjunto.

Una forma simple de hacerlo es mediante **análisis local** (modificar una variable alrededor de un valor de referencia) o mediante el enfoque **uno por vez** (cambiar un solo factor mientras los demás permanecen constantes). Estos métodos permiten interpretar fácilmente el efecto individual de cada variable, aunque pueden ocultar relaciones entre ellas.

Los cambios analizados deben realizarse dentro de **rangos plausibles** (intervalos de valores razonables según datos, conocimiento o escenarios posibles). No tiene sentido probar valores extremos sin justificación, porque pueden producir resultados llamativos pero poco útiles.

También puede utilizarse la **elasticidad** (medida que compara el cambio porcentual de una salida frente al cambio porcentual de una entrada), lo que permite comparar la influencia de variables expresadas en unidades diferentes.

El análisis de sensibilidad es especialmente importante cuando existen **umbrales** (valores a partir de los cuales el comportamiento del sistema cambia significativamente) o **no linealidades** (cuando un pequeño cambio en una entrada puede producir un cambio mucho mayor en la salida). Por eso no siempre alcanza con analizar variaciones pequeñas o asumir relaciones lineales.

Además, pueden existir **interacciones**, es decir, situaciones en las que el efecto de una variable depende del valor de otra. Para estudiar esto se utiliza un **análisis de sensibilidad global**, donde varias entradas cambian simultáneamente dentro de sus rangos y se observa su efecto conjunto sobre los resultados.

Una herramienta frecuente para comunicar resultados es el **diagrama tornado** (gráfico que ordena las variables según cuánto modifican una determinada salida). Sirve para identificar rápidamente los factores más influyentes, aunque no muestra bien interacciones complejas.

Finalmente, el análisis permite evaluar la **robustez** de una decisión (qué tan estable sigue siendo una conclusión cuando cambian los supuestos). También ayuda a determinar el **valor de la información**, es decir, sobre qué variables conviene obtener mejores datos o realizar nuevas mediciones.

En síntesis, el análisis de sensibilidad sirve para responder una pregunta central: **¿de qué depende realmente el resultado del modelo?** Permite identificar variables críticas, detectar puntos de quiebre y verificar si una conclusión se mantiene cuando cambian los supuestos.

## Clase 10 - Verificación, calibración y validación

Un simulador puede ejecutar sin errores visibles y representar incorrectamente el sistema.

La **verificación** busca comprobar que el modelo esté correctamente construido y que el programa implemente lo que se definió conceptualmente. Retoma la **verificación conceptual** realizada antes de programar y luego incluye la **verificación del código**, que comprueba que el programa ejecute correctamente las reglas definidas.

Para detectar errores se utilizan herramientas como las **pruebas unitarias** (tests sobre componentes pequeños del programa), los **invariantes** (condiciones que siempre deben cumplirse durante la ejecución), las **trazas** para reconstruir ejecuciones y los **casos determinísticos** (ejecuciones sin aleatoriedad cuyo resultado puede calcularse de antemano). Estas técnicas permiten encontrar fallas antes de trabajar con simulaciones más complejas.

Una vez que el modelo funciona correctamente, comienza la **validación**, que busca determinar si representa adecuadamente el sistema real para el objetivo del estudio. Para eso puede ser necesario realizar una **calibración** (ajustar parámetros del modelo para que reproduzca datos observados).

Sin embargo, hay que evitar la **sobrecalibración** (ajustar tanto el modelo a un conjunto específico de datos que luego no funcione bien en otras situaciones). Por eso, los datos utilizados para ajustar el modelo deberían separarse de aquellos utilizados posteriormente para validarlo.

La validación puede realizarse de distintas formas. La **validez aparente** consiste en comprobar, con ayuda de personas que conocen el sistema, si su comportamiento parece razonable. La **validación con datos** compara los resultados simulados con observaciones reales que no se utilizaron durante la calibración. También puede hacerse una **validación extrema**, probando situaciones límite para verificar que el modelo responda de manera lógica.

Finalmente, la **validez operacional** analiza si el modelo es suficientemente confiable para la decisión concreta que se quiere tomar. Un modelo no tiene que reproducir perfectamente toda la realidad: debe ser adecuado para el propósito para el cual fue construido.

Toda esta evidencia debe documentarse en un **expediente de evidencia** (registro de pruebas, comparaciones, errores encontrados, correcciones y limitaciones), ya que la validación no debería entenderse simplemente como “válido” o “inválido”.

En síntesis, **que el código funcione no significa necesariamente que el modelo sea válido**. La verificación comprueba que el modelo fue implementado correctamente; la validación evalúa si ese modelo representa suficientemente bien la realidad para responder la pregunta planteada.