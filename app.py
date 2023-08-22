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
    return {"Response": "It's turned on!"}


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
                orders = principal.get_data_from_excel()
                qtt_orders = len(orders)
                if qtt_orders > 0:
                    print("Existem {} pedidos a serem absorvidos.".format(len(principal.get_data_from_excel())))
                    for idx, order in enumerate(orders):
                        cnpj = ""
                        try:
                            cnpj = str(int(float(order[0]['Pedido'][0])))
                        except Exception as e:
                            print(e)
                        data_raw = principal.format_json(eid_cliente=cnpj, ordem_de_compra_e_desconto=order[0]['Pedido'][1], lista_items=order[0]['Items'])
                        print(data_raw)

                print("  --------------------------")
                print("\n")
                await asyncio.sleep(30)

        task = asyncio.create_task(main_order())
        tasks.append(task)
        return json.dumps({"Reponse": "New task was started."})
    else:
        tasks[0].cancel()
        tasks.pop()
        return json.dumps({"Response": "The task was restarted!"})


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
