# Problema de Regresión — Parkinsons Telemonitoring

## Instrucciones

Resuelve de manera grupal (equipos de ML) el siguiente ejercicio en un cuaderno de Jupyter Notebook y responde a los planteamientos indicados.

## Ejercicio

Considere el conjunto de datos de seguimiento telemétrico de la enfermedad de Parkinson (*Parkinsons Telemonitoring* — UCI Machine Learning Repository), el cual contiene 19 características entre las cuales hay varias derivadas de grabaciones de voz de pacientes con Parkinson. La idea es crear un modelo que prediga a partir de la voz de un paciente la severidad de su enfermedad, la cual es cuantificada con una escala estándar médica llamada **UPDRS**.

### Características

| Variable | Descripción    | Variable | Descripción     |
| -------- | -------------- | -------- | --------------- |
| X1       | age            | X11      | Shimmer: APQ5   |
| X2       | test_time      | X12      | Shimmer: APQ11  |
| X3       | Jitter (%)     | X13      | Shimmer: DDA    |
| X4       | Jitter (Abs)   | X14      | NHR             |
| X5       | Jitter: RAP    | X15      | HNR             |
| X6       | Jitter: PPQ5   | X16      | RPDE            |
| X7       | Jitter: DDP    | X17      | DFA             |
| X8       | Shimmer        | X18      | PPE             |
| X9       | Shimmer (dB)   | X19      | sex             |
| X10      | Shimmer: APQ3  |          |                 |

El dataset tiene 2 variables dependientes, `motor_UPDRS` y `total_UPDRS`. **Para este ejercicio usa `total_UPDRS`.**

## Realiza

### 1. Modelo lineal (20 puntos)

- Entrena un modelo de regresión lineal con las variables asignadas.
- Evalúa su desempeño usando validación cruzada.

### 2. Selección de características (features) (20 puntos)

- Aplica un método sencillo de selección de variables (por ejemplo, selección secuencial hacia adelante).
- Reporta cuántas y cuáles fueron las variables óptimas seleccionadas.

### 3. Curva de aprendizaje (20 puntos)

- Genera una curva de aprendizaje para el modelo de regresión lineal. Pueden usar `learning_curve` de scikit-learn.
- Responde:
  - ¿El modelo se beneficiaría de más datos?
  - ¿Se observan indicios de overfitting o underfitting al usar todos los datos de entrenamiento? Puedes usar como baseline `DummyRegressor`.

### 4. Modelo no lineal (KNN) (20 puntos)

- Entrena un modelo de K-vecinos más cercanos (KNN).
- Evalúa con validación cruzada.
- Crea una curva de validación para el valor de `k` (ej. de 1 a 20) y determina cuál produce el mejor desempeño.

### 5. Otro modelo no lineal (10 puntos)

- Elige un modelo adicional (por ejemplo, Random Forest o SVR).
- Repite los pasos 2 a 3 para este modelo.

### 6. Conclusiones (10 puntos)

- ¿El modelo lineal fue adecuado para los datos? ¿Por qué?
- ¿Qué variables resultaron más relevantes según la selección de features?
- ¿Los modelos no lineales funcionaron mejor que el lineal? Explica.
- ¿Qué aprendizajes generales obtienes al modelar este conjunto de datos con regresión?
