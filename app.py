from fastapi import FastAPI
import logging
logging.basicConfig(level=logging.INFO)
logging.info("La app ha iniciado correctamente")

app = FastAPI()


@app.get("/")
def ping():
    return {"message": "Backend operativo"}