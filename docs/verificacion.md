# Evidencia de verificación de la implementación

Versión del código: `cc191f2ec21abb6f5b9ec3362ee8d1f613d32fa5`. Python 3.12.3.

La suite ejecutó **107 tests y todos pasaron**. La corrida completa de referencia atendió a sus 4.765 clientes y pasó las comprobaciones de invariantes y contabilidad. También se ejecutaron de punta a punta los ejemplos de incidencias y apertura reactiva.

Se compararon seis alternativas, con treinta semanas independientes por alternativa (180 semanas en total), semillas 2026 a 2055 y entradas comunes por semilla. Nivel de confianza: 90 %.

La siguiente tabla muestra la media del máximo P95 entre las franjas de cada semana completa. No es el P95 global de clientes. Los intervalos son por alternativa.

| Política | Semanas completas para la media | Máximo P95 medio (min) | IC 90 % (min) | Semanas inviables | Semanas que cumplen servicio |
|---|---:|---:|---|---:|---:|
| referencia_normal | 30 | 253.27 | [240.16, 266.38] | 0 | 0/30 |
| referencia_rapida_exclusiva | 26 | 503.47 | [486.89, 520.05] | 4 | 0/30 |
| referencia_rapida_flexible | 30 | 273.32 | [260.76, 285.87] | 0 | 0/30 |
| cinco_todas_franjas_normal | 30 | 104.17 | [96.79, 111.54] | 0 | 0/30 |
| cinco_todas_franjas_rapida_exclusiva | 30 | 173.00 | [163.40, 182.60] | 0 | 0/30 |
| cinco_todas_franjas_rapida_flexible | 30 | 114.91 | [106.77, 123.04] | 0 | 0/30 |

En rápida exclusiva con referencia 5/4/3 hubo cuatro semanas que invadieron la apertura siguiente. Esas semanas siguen contando como fracasos del servicio, pero no se usan para estimar una distribución de espera de semana completa. Su intervalo queda condicionado a las 26 semanas operativamente completas; no describe las semanas inviables.

Ninguna de estas alternativas cumplió el objetivo en todas las franjas de alguna de las treinta semanas ensayadas. Eso es un resultado bajo los parámetros supuestos, no una recomendación definitiva sobre un supermercado real. El programa no seleccionó ganadora porque falta acordar la meta probabilística.

La evidencia detallada, los intervalos y las diferencias pareadas están en [el registro JSON](evidencia/prueba_integracion.json). Las trazas y CSV completos se regeneran con los comandos del README y quedan en `resultados/`, fuera de Git.

La verificación acredita implementación y consistencia. Siguen pendientes datos observados, revisión de supuestos y validación empírica. La plantilla de automatización está disponible, pero su activación requiere el permiso `workflow` de GitHub.
