from datetime import datetime

from fastapi import FastAPI

from core import *

app = FastAPI()


@app.get("/")
async def root():
    current_datetime = datetime.now()
    formatted_datetime = current_datetime.strftime("dia %d/%m/%Y às %H:%M:%S")
    print("\n ----------------------------------------------")
    print(" Aplicativo iniciado {}.".format(formatted_datetime))
    print(" ----------------------------------------------")

    return {"Aplicativo online": "Aplicativo foi chamado {}.".format(formatted_datetime)}
