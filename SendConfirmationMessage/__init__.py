from datetime import datetime
import logging
import azure.functions as func
from ..Utils.Api import MediciaAPI, WhatsAppAPI, TimeUtils, AzureTableUtils

def main(mytimer: func.TimerRequest) -> None:
    nathan_number = '5511958921707'

    med_api = MediciaAPI()
    whats = WhatsAppAPI()
    time = TimeUtils()
    azure_table = AzureTableUtils()

    agendados = med_api.agenda_agendados(TimeUtils.tomorrow_dmy())

    for agenda_info in agendados:
        pacient_infos = med_api.search_pacient_by_id(agenda_info['pacienteId'])        
        phone = med_api.get_patient_cellphone(agenda_info['pacienteId'])

        if phone:
            phone = phone[0]['ddi'] + phone[0]['ddd'] + phone[0]['numero']
            nome = pacient_infos['nome'].split()[0].capitalize()
            data = datetime.strptime(agenda_info['dataInicio'], '%Y-%m-%dT%H:%M:%SZ').strftime('%d/%m/%Y')
            
            hora_completa = agenda_info['horaInicio'].replace('PT', '').replace('M', '').split('H')
            hora = hora_completa[0]
            minuto = hora_completa[1] if len(hora_completa) == 2 and hora_completa[1] != '' else "00"
            hora_formatada = f'{hora}:{minuto}'

            professional_name = med_api.search_professional_by_id(agenda_info['profissionalId'])['nome'].title()
            professional_name = f'Dr(a). {professional_name}'

            component = whats.text_body_component(4, nome, data, hora_formatada, professional_name)
            response = whats.send_template_message(phone, "lembrete_agendamento", component)

            if response.status_code == 200:
                logging.info(f'Mensagem de lembrete enviada para {nome} com sucesso! - Numero Celular: {phone}')

                waID = response.json()['messages'][0]['id']
                agenda_id = agenda_info['id']
                status = ''
                entity = {
                        'PartitionKey': 'ConfirmationMessages',
                        'RowKey': waID,
                        'time': time.today(),
                        'agenda_id': agenda_id,
                        'status': status
                        }

                azure_table.create_entity(entity)
            else:
                logging.info(f'Erro ao enviar lembrete de agendamento para {nome} - Numero Celular: {phone}')
                logging.info(response.text)