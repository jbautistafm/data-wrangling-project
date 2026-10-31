# limpieza de mis carreras de strava: de data/raw a data/clean
import json
import pandas as pd

RAW = "../data/raw/"
CLEAN = "../data/clean/"

def cargar_actividades(ruta=RAW + "activities.json"):
    with open(ruta, encoding="utf-8") as f:
        return pd.json_normalize(json.load(f))

def filtrar_carreras(df):
    # solo running y de mas de 1 km (quito pruebas y paseos)
    ritmo = df["moving_time"] / (df["distance"] / 1000)
    # quito paseos que guarde como carrera, mas de 10 min/km
    return df[(df["sport_type"] == "Run") & (df["distance"] > 1000) & (ritmo < 600)].copy()

def añadir_unidades(df):
    df["km"] = (df["distance"] / 1000).round(2)
    df["minutos"] = (df["moving_time"] / 60).round(1)
    df["ritmo_s_km"] = (df["moving_time"] / df["km"]).round(1)
    df["desnivel_m"] = df["total_elevation_gain"]
    return df

def añadir_fechas(df):
    # quito la Z del final, la hora ya es la local
    df["fecha"] = pd.to_datetime(df["start_date_local"].str[:19])
    df["hora"] = df["fecha"].dt.floor("h")
    df["year"] = df["fecha"].dt.year
    df["mes"] = df["fecha"].dt.month
    estaciones = {12: "invierno", 1: "invierno", 2: "invierno", 3: "primavera", 4: "primavera",
                  5: "primavera", 6: "verano", 7: "verano", 8: "verano",
                  9: "otoño", 10: "otoño", 11: "otoño"}
    df["estacion"] = df["mes"].map(estaciones)
    df["franja"] = pd.cut(df["fecha"].dt.hour, bins=[0, 12, 20, 24], right=False,
                          labels=["mañana", "tarde", "noche"])
    return df

def marcar_competicion(df):
    # en strava no marque las carreras, asi que las saco por el nombre
    palabras = r"marat|media|half|10k|15k|silvestre|race|popular|behobia"
    por_nombre = df["name"].str.lower().str.contains(palabras, na=False)
    # "10k de domingo" era un entreno, no una carrera
    por_nombre = por_nombre & ~df["name"].str.lower().str.contains("domingo", na=False)
    df["es_competicion"] = por_nombre | (df["workout_type"] == 1)
    return df

def añadir_clima(df, ruta=RAW + "weather.csv"):
    clima = pd.read_csv(ruta, parse_dates=["time"]).rename(columns={"time": "hora"})
    clima["lat"] = clima["lat"].round(1)
    clima["lon"] = clima["lon"].round(1)
    con_gps = df["start_latlng"].str.len() == 2
    df.loc[con_gps, "lat"] = df.loc[con_gps, "start_latlng"].str[0].round(1)
    df.loc[con_gps, "lon"] = df.loc[con_gps, "start_latlng"].str[1].round(1)
    df = df.merge(clima, on=["lat", "lon", "hora"], how="left")
    return df.rename(columns={"temperature_2m": "temp", "relative_humidity_2m": "humedad",
                              "wind_speed_10m": "viento", "precipitation": "lluvia"})

def añadir_zapatillas(df, ruta=CLEAN + "zapatillas.csv"):
    zap = pd.read_csv(ruta)
    df = df.merge(zap[["gear_id", "marca", "modelo"]], on="gear_id", how="left")
    df["modelo"] = df["modelo"].fillna("sin zapatilla")
    # las de placa son las de competicion, el resto de diario
    df["tipo_zapa"] = "diario"
    df.loc[df["modelo"].str.contains("Vaporfly|Zoom Fly", na=False), "tipo_zapa"] = "competicion"
    df.loc[df["modelo"].str.contains("Trail", na=False), "tipo_zapa"] = "trail"
    df.loc[df["modelo"] == "sin zapatilla", "tipo_zapa"] = "sin dato"
    return df

def quitar_privado(df):
    # rgpd: fuera coordenadas, mapa y nombre (puede decir donde corro)
    columnas = ["id", "fecha", "year", "mes", "estacion", "franja", "km", "minutos",
                "ritmo_s_km", "desnivel_m", "average_heartrate", "es_competicion",
                "temp", "humedad", "viento", "lluvia", "marca", "modelo", "tipo_zapa"]
    return df[columnas].rename(columns={"id": "activity_id", "average_heartrate": "pulso"})

def limpiar_splits(ruta=RAW + "splits.json"):
    with open(ruta, encoding="utf-8") as f:
        s = pd.DataFrame(json.load(f))
    # fuera km rotos: distancia negativa, tiempo 0, el ultimo trozo corto y fallos de gps
    # y los km andando
    s = s[(s["distance"] >= 950) & (s["moving_time"] > 0) & (s["average_speed"] < 7)
          & (s["average_speed"] > 1.5)].copy()
    s["ritmo_s_km"] = (s["moving_time"] / (s["distance"] / 1000)).round(1)
    s = s[["activity_id", "split", "ritmo_s_km", "elevation_difference", "average_heartrate"]]
    return s.rename(columns={"average_heartrate": "pulso"})

def main():
    df = cargar_actividades()
    df = filtrar_carreras(df)
    df = añadir_unidades(df)
    df = añadir_fechas(df)
    df = marcar_competicion(df)
    df = añadir_clima(df)
    df = añadir_zapatillas(df)
    carreras = quitar_privado(df)
    splits = limpiar_splits()
    # solo los splits de las carreras que me quedan
    splits = splits[splits["activity_id"].isin(carreras["activity_id"])]
    carreras.to_csv(CLEAN + "carreras.csv", index=False)
    splits.to_csv(CLEAN + "splits.csv", index=False)
    print(carreras.shape, "carreras |", splits.shape, "splits")
    return carreras, splits

if __name__ == "__main__":
    main()