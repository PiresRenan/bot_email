# import uvicorn
import json
from time import sleep

from fastapi import FastAPI
import asyncio

from core import Salesprogram


app = FastAPI()
tasks = []


@app.get("/on")
async def index():
    global tasks
    if not tasks:
        async def main_order():
            print("\nPedidos iniciado com sucesso!\n\n")
            while True:
                print("  --------------------------")
                print("O programa foi iniciado")
                principal = Salesprogram()
                if principal.check_email():
                    print("Arquivos enbcontrados e tratados")
                else:
                    print("Não foram encontrados emails.")

                if len(principal.get_data_from_excel()) > 0:
                    print("zsd~gfn")

                print("  --------------------------")
                print("\n")
                await asyncio.sleep(30)

        task = asyncio.create_task(main_order())
        tasks.append(task)
        return json.dumps({"Resposta": "Nova tarefa iniciada."})
    else:
        tasks[0].cancel()
        tasks.pop()
        return json.dumps({"Resposta": "Tarefa foi reiniciada!"})


@app.get("/off")
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
