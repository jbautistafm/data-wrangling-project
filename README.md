# ¿Qué me hace correr más rápido?

## Introducción

Llevo años corriendo y registrando todo en Strava, pero nunca me había parado a mirar mis datos de verdad. Hay días que voy volando y otros que no hay manera, y siempre le echaba la culpa a algo distinto: el calor, las zapatillas, la hora o la época del año. En este proyecto quería comprobarlo con datos en lugar de con sensaciones.

También tenía curiosidad por compararme con los mejores. Si a mí el calor me frena, ¿a los ganadores de las grandes maratones les pasa lo mismo?

## Datos y fuentes

He usado tres fuentes distintas:

| Fuente | Cómo la consigo | Qué saco |
|---|---|---|
| [API de Strava](https://developers.strava.com/docs/reference/) | API con autenticación OAuth (token de refresco) | Mis 318 carreras desde 2020: distancia, tiempo, ritmo, desnivel, pulso, hora, zapatillas y los parciales de cada kilómetro |
| [API de Open-Meteo](https://open-meteo.com/en/docs/historical-weather-api) | API histórica, sin clave | Temperatura, humedad, viento y lluvia a la hora exacta de cada carrera |
| Wikipedia: [ganadores del maratón de Berlín](https://en.wikipedia.org/wiki/List_of_winners_of_the_Berlin_Marathon) y [del de Londres](https://en.wikipedia.org/wiki/List_of_winners_of_the_London_Marathon) | Web scraping con `requests` y `pandas.read_html` | 195 ganadores (hombres y mujeres) con su tiempo y la fecha de la carrera, que luego cruzo con el clima de ese día |

## Preguntas de investigación

Antes de tocar los datos me planteé cinco hipótesis:

1. **H1.** Por encima de 20 °C mi ritmo empeora más de 10 segundos por kilómetro.
2. **H2.** Con zapatillas de competición voy más rápido que con las de diario a igual distancia.
3. **H3.** En otoño e invierno corro más rápido que en verano.
4. **H4.** Las salidas por la mañana son más rápidas que las de por la tarde.
5. **H5.** Si creo un índice de sensibilidad al calor del 1 al 5, a la élite le afecta menos que a mí.

## Metodología

### 1. Extracción

- **Strava.** Creé una app en Strava y guardé el ID, el secreto y el token de refresco en un archivo `.env`, que no se sube a GitHub (dejo un `.env.example` vacío como plantilla). La función `get_access_token()` pide un token nuevo cada vez, porque caducan a las 6 horas. Las actividades vienen paginadas de 200 en 200. Strava solo deja hacer 200 peticiones cada 15 minutos, así que cuando devuelve un error 429 el código espera y sigue. Para los parciales por kilómetro tuve que pedir cada carrera una a una, y la descarga guarda el progreso para poder retomarla si se corta.
- **Open-Meteo.** En vez de pedir el clima carrera a carrera, agrupé las salidas por zona (redondeando las coordenadas a un decimal, unos 10 km). Así pasé de unas 300 llamadas a 18. Luego cruzo cada carrera con su zona y con su hora redondeada.
- **Scraping.** Las páginas principales de los maratones ya no tienen la tabla de ganadores, así que uso las páginas "List of winners". La de Berlín trae la fecha exacta, pero la de Londres no, y tuve que sacar las fechas de otra página y unirlas por año. Para el clima de la élite me quedo con la media de 9 a 11 de la mañana, que es cuando se corre.

Todo lo que se descarga se guarda en `data/raw`, y cada celda comprueba si el archivo ya existe antes de volver a pedirlo. Así el notebook se ejecuta entero en segundos y no gasta llamadas.

### 2. Limpieza

`src/cleaning.py` tiene una función `main()` que llama en orden a las funciones de limpieza:

1. Cargar las actividades y quedarme solo con las carreras a pie de más de 1 km.
2. Quitar lo que en realidad eran paseos (ritmos por encima de 10 min/km).
3. Pasar las unidades a km, minutos y segundos por kilómetro.
4. Sacar el mes, la estación y la franja del día.
5. Marcar las competiciones. Nunca las había marcado en Strava, así que las detecto por palabras del nombre (media, 10K, maratón, San Silvestre…).
6. Añadir el clima y las zapatillas (clasificadas en competición, diario, trail o sin dato).
7. Quitar todo lo privado: coordenadas GPS y nombres de las actividades.

En los parciales quito los kilómetros incompletos, los de tiempo cero y los que tienen velocidades imposibles. El resultado son 312 carreras y 2.828 kilómetros limpios en `data/clean`.

Por privacidad (RGPD), `data/raw` no se sube al repo porque lleva mis coordenadas. Lo que hay en `data/clean` no tiene datos personales.

### 3. Análisis y visualización

El análisis está en `notebooks/eda.ipynb`. Para no mezclar entrenos con carreras a tope, uso solo los 293 entrenos que tienen clima.

- Agrupo la temperatura en tramos con `pd.cut` y comparo el **ritmo mediano** de cada tramo. Uso la mediana porque un día malo la mueve menos que la media.
- Para el índice de calor uso la **correlación de Pearson** entre temperatura y ritmo, y la paso a una nota del 1 al 5. Con la **pendiente de una regresión lineal** calculo cuántos segundos por kilómetro se pierden por cada 5 °C.
- A los tiempos de la élite les quito antes la tendencia de cada época con una mediana móvil de 9 ediciones. Si no, el calor se mezclaría con que hoy se corre mucho más rápido que en los 80.
- Gráficos con `matplotlib`: barras por tramo de temperatura, zapatilla, estación y franja horaria, y gráficos de dispersión temperatura-ritmo (míos y de la élite).

## Hallazgos principales

- **H1 se cumple.** Con más de 20 °C voy 11,5 s/km más lento. Donde mejor corro es entre 10 y 15 °C (5:03/km de mediana).
- **El calor no me sube el pulso, me baja el ritmo.** Mi pulso mediano es de unos 138 lpm haga el tiempo que haga. Pero con el mismo pulso voy 16 s/km más lento por encima de 20 °C. Sin darme cuenta, aflojo para mantener el mismo esfuerzo.
- **H2 se cumple, pero con matices.** Con zapatillas de competición voy 32 s/km más rápido en general, pero solo tengo 19 carreras con ellas y me las pongo los días de series. En tiradas largas la diferencia baja a 6 s/km.
- **H3 no se cumple.** Entre estaciones la diferencia es de 2,6 s/km. Importa la temperatura del día, no el calendario.
- **H4 no se cumple.** Por la tarde voy incluso un poco más rápido (5:10 frente a 5:13).
- **H5 se cumple.** Mi índice de sensibilidad al calor es 2 sobre 5: pierdo 4,5 s/km por cada 5 °C. El de la élite es 1, porque su ritmo prácticamente no cambia con la temperatura (aunque es verdad que esos maratones se corren con días de 7 a 23 °C).

### Calculadora web

Con la misma fórmula del índice hice una calculadora para que cualquier corredor meta sus carreras y vea dónde está entre un corredor popular y la élite:
**https://jbautistafm.github.io/data-wrangling-project/**

## Siguientes pasos

- Ampliar el scraping a otros maratones (Madrid y el resto de Majors) para tener más días de calor en la élite.
- Añadir la humedad al índice, porque el calor húmedo seguramente cuesta más que el seco.
- Con más carreras de competición, intentar predecir el tiempo de una carrera según la temperatura prevista.
- Probar el análisis con datos de otros corredores (con su permiso) para ver si lo mío es lo normal.

## Estructura del repo

```
data-wrangling-project/
├── data/
│   ├── raw/          # datos en bruto (no se suben)
│   └── clean/        # carreras.csv, splits.csv, elite.csv, zapatillas.csv
├── docs/             # calculadora web (GitHub Pages)
├── notebooks/
│   ├── proyecto.ipynb   # extracción de Strava y del clima
│   ├── scraping.ipynb   # ganadores de Berlín y Londres
│   └── eda.ipynb        # análisis de las hipótesis
├── src/
│   ├── strava_api.py
│   ├── weather_api.py
│   ├── scraping.py
│   └── cleaning.py      # main() con toda la limpieza
├── .env.example
└── README.md
```

## Cómo ejecutarlo

1. Clona el repo e instala las librerías:
   ```
   pip install pandas numpy matplotlib requests lxml python-dotenv
   ```
2. Si solo quieres ver el análisis, abre `notebooks/eda.ipynb` y ejecuta todo. Lee los CSV de `data/clean`, así que no necesitas cuenta de Strava.
3. Si quieres descargar tus propios datos, crea una app en Strava, copia `.env.example` como `.env` y rellena tus claves. Después ejecuta `proyecto.ipynb`, `scraping.ipynb` y `python src/cleaning.py`.

## Enlaces

- Tablero de Trello: https://trello.com/b/9gKDPVWY/data-wrangling-proyect
- Slides de la presentación: https://docs.google.com/presentation/d/1h23rBtCd28P2LlKN4bCKq5zKODI--J9wtZM7plETv5A/edit?usp=sharing
- Calculadora web: https://jbautistafm.github.io/data-wrangling-project/
- Fuentes: [API de Strava](https://developers.strava.com/docs/reference/) · [Open-Meteo](https://open-meteo.com/en/docs/historical-weather-api) · [Ganadores de Berlín](https://en.wikipedia.org/wiki/List_of_winners_of_the_Berlin_Marathon) · [Ganadores de Londres](https://en.wikipedia.org/wiki/List_of_winners_of_the_London_Marathon)

## Autor

[@jbautistafm](https://github.com/jbautistafm)
