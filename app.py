import json
import datetime
from time import sleep

import pytz
import re

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
            print("\n 0.0.0 - Pedidos iniciado com sucesso!\n\n")
            while True:
                start_time = datetime.datetime.now()
                print("  --------------------------")
                now = datetime.datetime.now(fuso_horario_brasilia)
                formato = "Data: %d/%m/%Y, Horário: %H:%M:%S"
                formatted_timer = now.strftime(formato)
                print(" 0.1.0 - A verificação periódica iniciou! Aguarde os processos subsequentes.")
                print(" 0.2.0 - Executando em: {}.".format(formatted_timer))
                principal = Salesprogram()
                start_time_email = datetime.datetime.now()
                print(" 1.0.0 - Iniciou o processo de checagem de email. Aguarde.")
                email = principal.check_email()
                email_sender = []
                email_sender_name = []
                for order in email:
                    email_sender.append(order.split('<')[1].replace('>', ''))
                    email_sender_name.append(order.split('<')[0])
                if email != "":
                    print(" 1.1.0 - Email foi verificado com sucesso!")
                else:
                    print(" 1.1.0 - O email não obteve êxito ao ser verificado. Investigue causa.")
                end_time_email = datetime.datetime.now()
                orders = principal.get_data_from_excel()
                qtt_orders = len(orders)
                if qtt_orders > 0:
                    print(
                        " 1.2.0 - Existem {} pedidos a serem absorvidos.".format(len(principal.get_data_from_excel())))
                    print(" 2.0.0 - Inicio da recuperação de dados e formatação do json.")
                    for idx, order in enumerate(orders):
                        start_time_data_adm = datetime.datetime.now()
                        cnpj = ""
                        print()
                        print(" - #***#***#***#***#***#***#***#***#***# - ")
                        try:
                            raw_cnpj = order[0]['Pedido'][0]
                            if raw_cnpj.endswith(".0"):
                                raw_cnpj = raw_cnpj.replace(".0", "")
                            cnpj = re.sub(r'[^0-9]', '', raw_cnpj)
                            print(
                                " 2.1.0 - Pedido {} de {}, (CNPJ: {}) em processo de recuperação de dados. Aguarde.".format(
                                    (idx + 1), qtt_orders, cnpj))
                            data_raw = principal.format_json(eid_cliente=cnpj,
                                                             ordem_de_compra_e_desconto=order[0]['Pedido'][1],
                                                             lista_items=order[0]['Items'],
                                                             order_marker=email_sender[idx],
                                                             name_order_maker=email_sender_name[idx])

                            if data_raw is not 0:
                                if data_raw['inactive_items']:
                                    itens_inactive = data_raw['inactive_items']
                                    del data_raw['inactive_items']
                                    print(
                                        " 2.3.12 - Existem itens inativos no pedido, será tomado as medidas necessárias.")
                                    if principal.order_with_inactive_items(json_to_absorve=data_raw,
                                                                           itens_inativo=itens_inactive,
                                                                           order_maker=email_sender[idx],
                                                                           order_maker_name=email_sender_name[idx]):
                                        print(" 2.3.14 - Aviso de itens inativos foi tratado e enviado com sucesso.")
                                else:
                                    print(" 2.3.12 - Não existem itens inativo. O pedido seguirá para a absorção.")

                        except Exception as e:
                            cnpj = "Campo invalido"
                            print(" 2.1.0 - O campo do CNPJ não está correto. Motivo: ".format(e))

                        end_time_data_adm = datetime.datetime.now()

                    print(" - #***#***#***#***#***#***#***#***#***# - ")
                    principal.clean_files()
                else:
                    print(
                        " 1.2.0 - Não existem emails novos. Aguarde {} segundos até que seja executado novamente.".format(
                            INTERVALO))
                end_time = datetime.datetime.now()

                total_time = end_time - start_time
                email_total_time = end_time_email - start_time_email
                percent_email = (email_total_time.total_seconds() / total_time.total_seconds()) * 100
                print(" END - O tempo total de execução foi de: {:.3f} segundos.".format(total_time.total_seconds()))
                print(
                    " END - O tempo gasto na verificação de emails foi de: {:.3f} segundos.".format(
                        email_total_time.total_seconds()))
                print(" END - Porcentagem de tempo gasto na verificação de emails: {:.2f}% do tempo total.".format(
                    percent_email))
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
