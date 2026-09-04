# Momento de Retroalimentación: Redefinición de los datos

- **Fecha de entrega:** vie 4 de sep de 2026, 23:59
- **Estado:** En progreso — SIGUIENTE: Presentar tarea
- **Intentos:** Ilimitados
- **Disponible:** 31 de ago de 2026, 0:00 — 4 de sep de 2026, 23:59

## Instrucciones

**Entregable:** Implementación de una técnica de aprendizaje máquina sin el uso de un framework.

En este proyecto nos interesa entrenar modelos de aprendizaje de máquina para el dataset asignado. Para ello, y después de haber realizado tu EDA y, en caso de ser necesario, tu ETL, ahora deberás crear un nuevo dataset apropiado para ser empleado con una técnica clásica de ML.

1. Define una estructura para los datos, tal que extraiga información del dataset original (ya sea el raw o el preprocesado).
2. Explica esa estructura y sube en tu repositorio de GitHub tu nueva versión del dataset.
3. Programa uno de los algoritmos vistos en el módulo (o que tu profesor de módulo autorice) sin usar ninguna biblioteca o framework de aprendizaje máquina, ni de estadística avanzada. Lo que se busca es que implementes manualmente el algoritmo, no que importes un algoritmo ya implementado.
4. Prueba tu implementación con tu set de datos y realiza algunas predicciones. Las predicciones las puedes correr en consola o las puedes implementar con una interfaz gráfica apoyándote en lo visto en otros módulos.
5. Tu implementación debe poder correr por separado solamente con un compilador; no debe depender de un IDE o de un "notebook". Por ejemplo, si programas en Python, tu implementación final se espera que esté en un archivo `.py`, no en un Jupyter Notebook.
6. Después de la entrega intermedia se te darán correcciones que puedes incluir en tu entrega final.

## Especificaciones

- **Modalidad:** Individual
- **Formato de entrega:** Sube el link del repositorio del proyecto de GitHub a la actividad en Canvas.

## Evaluación

En esta actividad se te dará retroalimentación sobre el siguiente indicador que se evalúa al final de bloque. Recuerda que la entrega final donde se califica es en la evidencia del portafolio de implementación.

| Subcompetencia | Indicador | Descripción |
| --- | --- | --- |
| — | SMA0401A | Implementa una técnica o algoritmo de aprendizaje máquina, sin uso de marco de trabajo o framework como regresiones, árboles, clusters, etc. |

Se evalúa correcto si y solo si el algoritmo aprende de un dataset correctamente y el programa puede hacer predicciones. El profesor del módulo puede determinar el nivel de *accuracy* o de *R²* esperado del dataset en turno, tomando en cuenta su complejidad y la capacidad del algoritmo implementado.
