# main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Tuple
import os
import osmnx as ox
import networkx as nx
from geopy.distance import geodesic

app = FastAPI()

GRAPH_PATH = "data/lima.graphml"

class RutaRequest(BaseModel):
    origen: Tuple[float, float] 
    destino: Tuple[float, float] 
    peligros: List[Tuple[float, float]] 

def cargar_o_descargar_grafo():
    if os.path.exists(GRAPH_PATH):
        return ox.load_graphml(GRAPH_PATH)
    else:
        G = ox.graph_from_place("Lima, Lima Metropolitan Area, Peru", network_type="drive")
        ox.save_graphml(G, GRAPH_PATH)
        return G

def penalizar_grafo(G, puntos_peligrosos, radio_m=100):
    G_mod = G.copy()
    nodos_a_eliminar = set()

    for nodo, datos in G_mod.nodes(data=True):
        coord_nodo = (datos["y"], datos["x"])
        for lat, lon in puntos_peligrosos:
            if geodesic(coord_nodo, (lat, lon)).meters < radio_m:
                nodos_a_eliminar.add(nodo)
                break

    G_mod.remove_nodes_from(nodos_a_eliminar)
    return G_mod

@app.post("/ruta_segura")
def calcular_ruta_segura(req: RutaRequest):
    try:
        G = cargar_o_descargar_grafo()
        G_mod = penalizar_grafo(G, req.peligros)

        nodo_origen = ox.distance.nearest_nodes(G_mod, req.origen[1], req.origen[0])
        nodo_destino = ox.distance.nearest_nodes(G_mod, req.destino[1], req.destino[0])

        ruta = nx.shortest_path(G_mod, nodo_origen, nodo_destino, weight="length")

        coordenadas = [(G_mod.nodes[n]["y"], G_mod.nodes[n]["x"]) for n in ruta]
        return {"ruta": coordenadas}

    except nx.NetworkXNoPath:
        raise HTTPException(status_code=404, detail="No se encontró ruta evitando zonas peligrosas")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
