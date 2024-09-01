import datetime
import logging
import azure.functions as func
from ..Utils.Api import MediciaAPI, WhatsAppAPI, TimeUtils, AzureTableUtils

def main(mytimer: func.TimerRequest) -> None:
    nathan_number = '5511958921707'
    pedro_number = '5521993648826'
    clinica_number = '556295532226'

    whats = WhatsAppAPI()
    med_api = MediciaAPI()
    azure_table = AzureTableUtils()
    time = TimeUtils()

    pacients_id = med_api.get_last_year_pacients()

    for paciente_id in pacients_id:
        pacient_info = med_api.search_pacient_by_id()
        phone = med_api.get_patient_cellphone(paciente_id)
        if phone:
            pacient_info['celular'] = phone[0]['ddi'] + phone[0]['ddd'] + phone[0]['numero']

            component = whats.text_body_component(2, pacient_info['nome'], pacient_info['celular'])
            response = whats.send_template_message(pacient_info['celular'], "agendar_consulta_anual", component)

            if response.status_code == 200:
                logging.info(f'Mensagem de consulta anual enviada para {pacient_info["nome"]} com sucesso! - Numero Celular: {pacient_info["celular"]}')
                
                waID = response.json()['messages'][0]['id']
                status = ''
                entity = {
                        'PartitionKey': 'LastYearConsultMessages',
                        'RowKey': waID,
                        'time': time.today(),
                        'pacient_name': pacient_info['nome'],
                        'status': status
                        }
                
                azure_table.create_entity(entity)

            else:
                logging.info(f'Erro ao enviar mensagem de consulta para {pacient_info["nome"]} - Numero Celular: {pacient_info["celular"]}')
                logging.info(response.text)
        else:
            logging.info(f'Telefone não encontrado para o Paciente {pacient_info["nome"]} - Numero Celular: {pacient_info["celular"]}')
        
