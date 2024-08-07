import datetime
import logging
import azure.functions as func
from ..Utils.Api import MediciaAPI, WhatsAppAPI

def main(mytimer: func.TimerRequest) -> None:
    image_link = "https://sendwhatsappmessages.blob.core.windows.net/public/Imagem aniversario.jpg"
    video_link = "https://sendwhatsappmessages.blob.core.windows.net/public/video_institucional.mp4"

    image_component = [{"type": "header",
                        "parameters": [{"type": "image",
                                        "image": {"link": image_link}}]}
                       ]
    video_component = [{"type": "header",
                        "parameters": [{"type": "video",
                                        "video": {"link": video_link}}]}
                       ]


    nathan_number = '5511958921707'
    pedro_number = '5521993648826'
    clinica_number = '556295532226'

    whats = WhatsAppAPI()
    med_api = MediciaAPI()

    pacients = med_api.search_today_birthdays()

    for pacient in pacients:
        phone = med_api.get_patient_cellphone(pacient['id'])
        if phone:
            pacient['celular'] = phone[0]['ddi'] + phone[0]['ddd'] + phone[0]['numero']

            birthday_img = whats.send_template_message(pacient['celular'], "imagem_feliz_aniversario", image_component)
            birthday_video = whats.send_template_message(pacient['celular'], "video_institucional", video_component) 

            if birthday_img.status_code == 200 and birthday_video.status_code == 200:
                logging.info(f'Mensagem de aniversário enviada para {pacient["nome"]} com sucesso! - Numero Celular: {pacient["celular"]}')
                
            else:
                logging.info(f'Erro ao enviar mensagem de aniversário para {pacient["nome"]} - Numero Celular: {pacient["celular"]}')
                logging.info(birthday_img.text)
                logging.info(birthday_video.text)
        
