# Extra: fila única frente a filas individuales

## Pregunta y diseño

¿Cambiar la organización de filas mejora la espera del conjunto de clientes,
conservando demanda, capacidad y personal?

El plan `filas` evalúa doce escenarios: referencia 5/4/3 y cinco cajas toda la
jornada, cada una con cajas normales, rápida exclusiva y rápida flexible, y
cada combinación con fila única o filas individuales. Se ejecutan treinta
semanas por escenario (360 semanas), con semillas 2026 a 2055 y confianza del 90 %.
Dentro de cada par se generan exactamente las mismas llegadas, canastas,
medios de pago y prioridades. La mezcla de compras sigue siendo la uniforme
supuesta de 1 a 40 productos; no se conoce la composición real.

## Reglas que se comparan

- Fila única: selección global por prioridad y después orden de llegada,
  respetando elegibilidad y preferencia de la rápida.
- Individuales: elección de la fila habilitada de menor longitud, incluyendo
  al cliente en atención; empate por número de caja. No se estima trabajo
  pendiente ni se permite cambiar voluntariamente de fila.
- Al cerrar una caja, sus clientes pendientes se redistribuyen. La prioridad
  es local a la fila. La rápida flexible puede tomar clientes de otras filas
  cuando no tiene compras pequeñas en la propia: se conserva esa regla del motor.
- Se mantienen agendas, pausas, promoción, tiempos de servicio y límite rápido
  de diez productos. No se agrega personal ni una sexta caja.

La comparación estudia estas políticas completas. Una fila individual con
cambios voluntarios o elección según trabajo pendiente sería otro experimento.
No se supone de antemano que las filas individuales sean inferiores.

## Reproducción

Desde la raíz del proyecto:

```bash
python3 -m supermercado experimentar --config ejemplos/base.json --plan filas --replicas 30 --semilla 2026 --salida resultados/filas_30
```

`estadisticas.json` resume cada escenario. `comparaciones_pareadas.json`
compara el máximo P95 semanal de cada alternativa con su equivalente de fila
única, usando diferencias individuales menos única y semillas compartidas.
Un valor positivo indica un aumento de espera en individuales.
Los CSV y el manifiesto completo se regeneran en `resultados/filas_30/`, fuera de Git.

## Lectura de los indicadores

La espera media se calcula por semana sobre todos los clientes que comenzaron
atención, y luego se promedia entre semanas completas. El máximo P95 semanal
es el mayor P95 de espera entre las cohortes de día y franja de llegada; su
media entre réplicas no es el P95 global de clientes.

Las semanas inviables cuentan como fracaso del servicio, pero no se mezclan
con semanas completas para inferir esperas semanales. Las diferencias pareadas
usan sólo semillas completas en ambas alternativas, por lo que pueden diferir
de la resta de medias calculadas con muestras distintas. Los intervalos son
exploratorios, por comparación, sin ajuste por comparaciones múltiples.

## Resultados del piloto

La ejecución completó las 360 semanas previstas (incluidas las declaradas
operativamente inviables), sin errores de invariantes. Ninguno de los doce
escenarios logró una semana que cumpliera servicio en todas sus franjas.

Las medias siguientes usan únicamente semanas completas de cada escenario.
Todos los tiempos se expresan en minutos.

| Política | Espera media única | Espera media individuales | Máximo P95 medio única | Máximo P95 medio individuales | Inviables única / individuales |
|---|---:|---:|---:|---:|---:|
| 5/4/3 normales | 26.19 | 27.49 | 253.27 | 368.11 | 0 / 0 |
| 5/4/3 rápida exclusiva | 49.32 | 47.58 | 503.47 | 722.73 | 4 / 24 |
| 5/4/3 rápida flexible | 22.67 | 23.82 | 273.32 | 395.96 | 0 / 0 |
| 5/5/5 normales | 13.15 | 14.12 | 104.17 | 247.46 | 0 / 0 |
| 5/5/5 rápida exclusiva | 19.70 | 20.86 | 173.00 | 337.10 | 0 / 0 |
| 5/5/5 rápida flexible | 11.51 | 12.26 | 114.91 | 243.00 | 0 / 0 |

**Advertencia sobre 5/4/3 con rápida exclusiva:** la media de fila única usa
26 semanas y la de individuales sólo 6. La aparente menor espera media en
individuales no indica mejora: excluye 24 semanas inviables. Comparando las
mismas 6 semanas completas, individuales aumenta la espera media en 3.20
minutos (IC 90 %: 2.37 a 4.03). La inviabilidad aumenta de 4/30 a 24/30.

## Diferencias pareadas

Diferencia = individuales menos única. Cada intervalo usa semanas completas
en ambos miembros del par; valores positivos indican mayor espera en individuales.

| Política | Pares completos | Aumento de espera media [IC 90 %] | Aumento del máximo P95 [IC 90 %] |
|---|---:|---:|---:|
| 5/4/3 normales | 30 | 1.30 [1.22, 1.38] | 114.84 [108.08, 121.60] |
| 5/4/3 rápida exclusiva | 6 | 3.20 [2.37, 4.03] | 280.57 [254.49, 306.65] |
| 5/4/3 rápida flexible | 30 | 1.14 [1.06, 1.23] | 122.64 [114.01, 131.27] |
| 5/5/5 normales | 30 | 0.96 [0.90, 1.03] | 143.29 [136.47, 150.11] |
| 5/5/5 rápida exclusiva | 30 | 1.16 [1.05, 1.28] | 164.10 [154.18, 174.01] |
| 5/5/5 rápida flexible | 30 | 0.75 [0.69, 0.82] | 128.09 [117.62, 138.56] |

## Interpretación y decisión

En las seis políticas, las diferencias pareadas muestran mayor espera media
y mayor máximo P95 con filas individuales. Los intervalos exploratorios del
90 % quedan por encima de cero. En rápida exclusiva 5/4/3 esta conclusión
sobre esperas está condicionada a los seis pares completos; la mayor
frecuencia de inviabilidad es evidencia adicional y no se descarta del análisis.

Para cinco cajas normales durante toda la jornada, la espera media pasa de
13.15 a 14.12 minutos, mientras la media del máximo P95 sube de 104.17 a
247.46 minutos. Un cambio relativamente pequeño del promedio general puede
acompañarse de un deterioro importante de las franjas más críticas.

El resultado es coherente con las reglas: una menor cantidad de personas en
fila no garantiza menor trabajo pendiente; las filas pueden quedar desbalanceadas
y no se redistribuyen voluntariamente. Además, en individuales la prioridad
se resuelve dentro de cada fila, de modo que una fila puede acumular más espera
para clientes no prioritarios mientras otras avanzan. Estas son explicaciones
compatibles con el mecanismo, no una descomposición experimental de cuánto
aporta cada causa.

**Se mantiene fila única como referencia apoyada por este piloto.** Las filas
individuales no mejoraron el servicio del conjunto de clientes bajo las reglas
ensayadas, y con rápida exclusiva y capacidad decreciente agravaron la
inviabilidad. La fila única tampoco resolvió el incumplimiento del objetivo:
la sobrecarga del escenario sigue requiriendo análisis de demanda y atención.

No se concluye que toda organización de filas individuales sea inferior.
Permitir cambios voluntarios, elegir por trabajo pendiente, cambiar la regla
de prioridad o revisar la mezcla de compras requiere otros experimentos.
Tampoco se estudiaron aquí doble demanda, ausencia u otros escenarios del plan
`estres`: la promoción semanal se mantiene, pero este extra compara organización
de filas. La recomendación sigue condicionada a los parámetros supuestos y
no constituye validación empírica.

## Evidencia conservada

[Registro del piloto](evidencia/comparacion_filas.json): manifiesto completo,
estadísticas por escenario, diferencias pareadas del máximo P95 y diferencias
pareadas de espera media. Estas últimas se calculan de `replicas.csv`,
emparejando por semilla las semanas completas y usando `paired_interval`
del módulo `supermercado.statistics` con confianza 0.90.

La suite actual ejecutó 108 tests, todos satisfactorios. La nueva prueba
comprueba igualdad de entradas dentro de cada par, recursos compartidos,
ausencia de cambios voluntarios y elección de la referencia correcta para
las diferencias, además de ejecutar un experimento pequeño de punta a punta.
