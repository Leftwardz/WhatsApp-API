import datetime
import logging
import azure.functions as func
from ..Utils.Api import MediciaAPI, WhatsAppAPI, TimeUtils

def main(mytimer: func.TimerRequest) -> None:
    nathan_number = '5511958921707'

    med_api = MediciaAPI()
    whats = WhatsAppAPI()
    pacients = med_api.agenda_atendidos(TimeUtils.today_dmy())
    
    for pacient in pacients:
        phone = med_api.get_patient_cellphone(pacient['pacienteId'])
        pacient_infos = med_api.search_pacient_by_id(pacient['pacienteId'])

        if phone:
            phone = phone[0]['ddi'] + phone[0]['ddd'] + phone[0]['numero']
            name = pacient_infos['nome'].split()[0].capitalize() # Apenas o primeiro nome com a primeira letra maiscula
            
            component = whats.text_body_component(1, name)
            response = whats.send_template_message(phone, "nota_avaliacao", component)


            if response.status_code == 200:
                logging.info(f'Mensagem de avaliação enviada para {name} com sucesso! - Numero Celular: {phone}')
            else:
                logging.info(f'Erro ao enviar Mensagem de avaliação para {name} - Numero Celular: {phone}')
                logging.info(response.text)

