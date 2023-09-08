
import json
import datetime
import pytz

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
    # INTERVALO = 240
    INTERVALO = 10
    fuso_horario_brasilia = pytz.timezone('America/Sao_Paulo')
    if not tasks:
        async def main_order():
            print("\nPedidos iniciado com sucesso!\n\n")
            while True:
                start_time = datetime.datetime.now()
                print("  --------------------------")
                now = datetime.datetime.now(fuso_horario_brasilia)
                formato = "Data: %d/%m/%Y, Horário: %H:%M:%S"
                formatted_timer = now.strftime(formato)
                print("A verificação periódica iniciou! Aguarde os processos subsequentes.")
                print("Executando em: {}.".format(formatted_timer))
                principal = Salesprogram()
                start_time_email = datetime.datetime.now()
                email = principal.check_email()
                if email != "":
                    print("Email foi verificado com sucesso!")
                else:
                    print("O email não obteve êxito ao ser verificado. Investigue causa.")
                email_sender = ""
                end_time_email = datetime.datetime.now()
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
                else:
                    print("Não existem emails novos. Aguarde {} segundos até que seja executado novamente.".format(INTERVALO))
                end_time = datetime.datetime.now()

                total_time = end_time - start_time
                email_total_time = end_time_email - start_time_email
                percent_email = (email_total_time.total_seconds()/total_time.total_seconds()) * 100

                print()
                print("O tempo total de execução foi de: {:.3f} segundos.".format(total_time.total_seconds()))
                print(
                    "O tempo gasto na verificação de emails foi de: {:.3f} segundos.".format(email_total_time.total_seconds()))
                print("Porcentagem de tempo gasto na verificação de emails: {:.2f}% do tempo total.".format(percent_email))
                print("  --------------------------")
                print("\n")
                await asyncio.sleep(INTERVALO)

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
