# import uvicorn
import json
from time import sleep

from fastapi import FastAPI
import asyncio

from core import Salesprogram


app = FastAPI()
tasks = []


@app.get("/")
async def index():
    global tasks
    if not tasks:
        async def main_order():
            print("\nPedidos iniciado com sucesso!\n\n")
            while True:
                print("Executando...")
                getter_data = Salesprogram()
                print(getter_data.get_data())
                print("\n")
                await asyncio.sleep(1)

        task = asyncio.create_task(main_order())
        tasks.append(task)
        return json.dumps({"Resposta": "Nova tarefa iniciada."})
    else:
        tasks[0].cancel()
        tasks.pop()
        return json.dumps({"Resposta": "Tarefa foi reiniciada!"})


@app.get("/test/")
async def pause_task():
    global tasks
    if tasks:
        tasks[0].cancel()
        tasks.pop()
        return json.dumps({"Resposta": "Tarefa pausada!"})
    else:
        return json.dumps({"Resposta": "Sem tarefas sendo executadas!"})

# if __name__ == '__main__':
#     uvicorn.run('app:app', host='0.0.0.0', port=8000)
