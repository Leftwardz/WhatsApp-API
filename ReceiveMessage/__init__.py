import os
import logging
import azure.functions as func
from ..Utils.Api import MediciaAPI, WhatsAppAPI, TimeUtils, AzureTableUtils


def main(req: func.HttpRequest) -> func.HttpResponse:
    nathan_number = '5511958921707'
    pedro_number = '5521993648826'
    clinica_number = '556295532226'

    logging.info(f'Método HTTP: {req.method}')

    req_body = req.get_body().decode('utf-8')
    logging.info(f'Corpo da solicitação HTTP: {req_body}')
    
    logging.info(f'Headers: {req.headers}')
    logging.info(f'Parametros HTTP: {req.params}')
        
    try:
        if req.method == 'GET':
            hub_challenge = req.params.get('hub.challenge')
            if hub_challenge:
                return func.HttpResponse(hub_challenge, status_code=200)
            else:
                return func.HttpResponse('Método Get não reconhecido', status_code=401)
        elif req.method == 'POST':
            med_api = MediciaAPI()
            whats = WhatsAppAPI()
            azure_table = AzureTableUtils()
            time = TimeUtils()

            info = req.get_json()
            had_message = False

            for entry in info['entry']:
                for change in entry['changes']:
                    message = change['value'].get('messages', None)
                    logging.info(f'MESSAGE: {message}')
                    if message:
                        message = message[0]
                        number = message['from']

                        if message['type'] == 'text':    
                            text = message['text'].get('body', 'Nenhuma mensagem no body')
                            
                            entity = azure_table.query_entity('WhatsAppContacts', number)
                            logging.info('Essa linha foi executada')
                            if not entity:
                                name = 'Alguém'
                            else:
                                # Get the name from entity
                                logging.info(entity)
                                name = entity['Name']
                            
                            component = whats.text_body_component(3, name, number, text)
                            whats.send_template_message(nathan_number, "message_notification_v2", component)
                            whats.send_template_message(clinica_number, "message_notification_v2", component)

                            entity = azure_table.query_entity('RecentMessages', number)
                            if entity:
                                if time.diference(time.today(), entity['time']) > 60000:
                                    whats.send_default_reply(number)
                                    entity['time'] = time.today()

                                entity['last_message'] = text
                                azure_table.update_entity(entity)
                            else:
                                entity = {
                                    'PartitionKey': 'RecentMessages',
                                    'RowKey': number,
                                    'time': time.today(),
                                    'last_message': text
                                }
                                azure_table.create_entity(entity)
                                whats.send_default_reply(number)

                            
                        elif message['type'] == 'button':
                            message_wa_id = message['context']['id']
                            button_text = message['button']['text']

                            confirmation_message_entity = azure_table.query_entity('ConfirmationMessages', message_wa_id)
                            last_year_consult_message_entity = azure_table.query_entity('LastYearConsultMessages', message_wa_id)

                            if confirmation_message_entity:
                                agenda_id = confirmation_message_entity['agenda_id']
                                if not confirmation_message_entity['status']:
                                    if button_text == 'CONFIRMAR':
                                        sucess_message = 'Seu agendamento foi confirmado com sucesso!\n'\
                                        'Se surgir alguma dúvida, não hesite em entrar em contato.'
                                        
                                        if MediciaAPI.confirm_agenda(agenda_id):
                                            entity = {
                                                'PartitionKey': 'ConfirmationMessages',
                                                'RowKey': message_wa_id,
                                                'time': time.today(),
                                                'agenda_id': agenda_id,
                                                'status': 'Confirmado'
                                            }

                                            azure_table.update_entity(entity)

                                            whats.send_custom_message(number, sucess_message)
                                    elif button_text == 'CANCELAR':
                                        cancel_message = 'Entendemos que imprevistos acontecem. \n'\
                                        'Se desejar reagendar sua consulta, estamos disponíveis para ajudar a encontrar uma nova data que funcione para você.'

                                        if MediciaAPI.cancel_agenda(agenda_id):
                                            entity = {
                                                'PartitionKey': 'ConfirmationMessages',
                                                'RowKey': message_wa_id,
                                                'time': time.today(),
                                                'agenda_id': agenda_id,
                                                'status': 'Cancelado'
                                            }

                                            azure_table.update_entity(entity)

                                            whats.send_custom_message(number, cancel_message)

                            if last_year_consult_message_entity:
                                if not last_year_consult_message_entity['status']:
                                    if button_text == 'SIM':
                                        return_message = 'Notificamos nossos atendentes,\n'\
                                        'entraremos em contato em breve para agendar uma consulta.\n Ficamos à disposição para qualquer dúvida.'
                                        
                                        whats.send_custom_message(number, return_message)

                                        entity = {
                                                'PartitionKey': 'LastYearConsultMessages',
                                                'RowKey': message_wa_id,
                                                'time': time.today(),
                                                'pacient_name': last_year_consult_message_entity['nome'],
                                                'status': 'Cliente aceita agendar consulta anual'
                                            }

                                        azure_table.update_entity(entity)

                                        component = whats.text_body_component(2, entity['pacient_name'], number)
                                        whats.send_template_message(nathan_number, "msg_notification_consulta_anual", component)
                                        whats.send_template_message(clinica_number, "msg_notification_consulta_anual", component)

                                    elif button_text == 'NÃO':
                                        return_message = 'Ficamos a disposição caso queira marcar uma consulta futuramente.'
                                        
                                        whats.send_custom_message(number, return_message)

                                        entity = {
                                                'PartitionKey': 'LastYearConsultMessages',
                                                'RowKey': message_wa_id,
                                                'time': time.today(),
                                                'pacient_name': last_year_consult_message_entity['nome'],
                                                'status': 'Cliente não aceitou agendar consulta anual'
                                            }

                                        azure_table.update_entity(entity)    
                                

                        had_message = True

                    message = None
            
            if had_message:
                return func.HttpResponse(f"Sucesso!", status_code=200)
            else:
                return func.HttpResponse(f"Erro!", status_code=500)
            
    except ValueError as e:
        return func.HttpResponse(f"Erro! {e}", status_code=500)
