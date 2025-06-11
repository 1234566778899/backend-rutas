from fastapi import FastAPI, Query
from pydantic import BaseModel
from typing import List
import osmnx as ox
import networkx as nx
import pathlib
from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv
import os
import logging
logging.basicConfig(level=logging.INFO)
logging.info("La app ha iniciado correctamente")

load_dotenv()
print("Verificando si el grafo está descargado 3...")
AZURE_CONNECTION_STRING = os.getenv("AZURE_CONNECTION_STRING")
CONTAINER_NAME = "grafo"
BLOB_NAME = "lima.graphml"
LOCAL_PATH = pathlib.Path("data/lima.graphml")

LOCAL_PATH.parent.mkdir(parents=True, exist_ok=True)

try:
    if not LOCAL_PATH.exists():
        print("Descargando grafo desde Azure...")
        blob_service_client = BlobServiceClient.from_connection_string(AZURE_CONNECTION_STRING)
        blob_client = blob_service_client.get_blob_client(container=CONTAINER_NAME, blob=BLOB_NAME)

        with open(LOCAL_PATH, "wb") as f:
            f.write(blob_client.download_blob().readall())
        print("Grafo descargado.")
except Exception as e:
    print("❌ Error al descargar el grafo:", e)


app = FastAPI()
print("Cargando grafo...")
if os.path.exists("data/lima.graphml") and os.path.getsize("data/lima.graphml") > 0:
    G = ox.load_graphml("data/lima.graphml")
else:
    print("El archivo lima.graphml está vacío o no existe.")
print("Grafo cargado.")

class Coordinate(BaseModel):
    latitude: float
    longitude: float

@app.get("/route", response_model=List[Coordinate])
def get_route(origen_lat: float = Query(...), origen_lon: float = Query(...), destino_lat: float = Query(...), destino_lon: float = Query(...)):
    
    origen_nodo = ox.nearest_nodes(G, origen_lon, origen_lat)
    destino_nodo = ox.nearest_nodes(G, destino_lon, destino_lat)

    ruta = nx.shortest_path(G, origen_nodo, destino_nodo, weight="length")

    coordenadas = []
    for nodo in ruta:
        punto = G.nodes[nodo]
        coordenadas.append({
            "latitude": punto["y"],
            "longitude": punto["x"]
        })

    return coordenadas

@app.get("/")
def ping():
    return {"message": "Backend operativo"}