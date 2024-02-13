import requests
import json
import os
from datetime import datetime, timedelta
import logging
from azure.core.credentials import AzureNamedKeyCredential
from azure.core.exceptions import ResourceNotFoundError
from azure.data.tables import TableServiceClient


class AzureTableUtils:
    def get_service(self):
        credential = AzureNamedKeyCredential("sendwhatsappmessages", os.environ["STORAGE_ACESS_KEY"])
        service = TableServiceClient(endpoint="https://sendwhatsappmessages.table.core.windows.net", credential=credential)

        return service

    def create_entity(self, entity, table_name='WhatsAppHistory'):
        table = self.get_service().get_table_client(table_name)
        table.create_entity(entity)

    def query_entity(self, partition_key, row_key, table_name='WhatsAppHistory'):
        table = self.get_service().get_table_client(table_name)
        try:
            entity = table.get_entity(partition_key=partition_key, row_key=row_key)
            return entity
        except:
            return None    

    def update_entity(self, entity, table_name='WhatsAppHistory'):
        table = self.get_service().get_table_client(table_name)
        table.update_entity(mode="replace", entity=entity)


class TimeUtils:
    def today(self):
        return datetime.now().strftime('%d/%m/%Y %H:%M:%S')
    
    @staticmethod
    def today_dmy():
        return datetime.now().strftime('%Y-%m-%d')

    @staticmethod
    def tomorrow_dmy():
        tomorrow = datetime.now() + timedelta(days=1)
        return tomorrow.strftime('%Y-%m-%d')

    def diference(self, time1, time2):
        """
        :param time1: '02/11/2023 16:00:00'
        :param time2: '02/11/2023 16:00:00'
        :return: Diferença entre time1 e time2 em milisegundos
        """
        time1 = datetime.strptime(time1, '%d/%m/%Y %H:%M:%S')
        time2 = datetime.strptime(time2, '%d/%m/%Y %H:%M:%S')

        return (time1 - time2).total_seconds() * 1000


class MediciaAPI:
    def __init__(self):
        self.login_data = {
            'Login': os.environ['LOGIN'],
            'Senha': os.environ['SENHA']
        }

        self.__token__ = ''
        self.__token_duration__ = ''

    @staticmethod
    def get_date():
        """
        Função pode ser utilizada para fazer filtros de datas com o '$filter='
        :return: Data atual no formato exemplo'2023-09-05'
        """
        return [datetime.now().strftime('%m'), datetime.now().strftime('%d')]

    def __get_token__(self):
        url = 'https://api.medicinadireta.com.br/odata/Token/'
        header = {
            'Content-Type': 'application/json'
        }
        body = json.dumps(self.login_data)

        response = requests.post(url, headers=header, data=body)

        if response.status_code == 200:
            self.__token__ = response.json()['chave']

            # Converter duração token em objeto datetime, valor exemplo: '2023-09-05T05:04:53Z'
            self.__token_duration__ = datetime.strptime(response.json()['duracao'], '%Y-%m-%dT%H:%M:%SZ')
        else:
            logging.info(f'Erro na solicitação do Token: Código de status {response.status_code}')
            logging.info(response.text)

    def get_patient_cellphone(self, patient_id):
        self.__get_token__()

        url = f"https://api.medicinadireta.com.br/odata/pacienteTelefone/PacienteId(PacienteID={patient_id})"

        header = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.__token__}'
        }

        response = requests.get(url, headers=header)

        if response.status_code == 200:
            return response.json()['value']
        else:
            return []


    def search_today_birthdays(self):
        """
        :return: lista de pacientes que fazem aniversário hoje
        """
        self.__get_token__()

        url = "https://api.medicinadireta.com.br/odata/paciente?" \
              f"$select=id, nome, dataNascimento, idade" \
              f"&$filter=ativado eq 'S' and month(dataNascimento) eq {self.get_date()[0]} and " \
              f"day(dataNascimento) eq {self.get_date()[1]}"

        header = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.__token__}'
        }

        response = requests.get(url, headers=header)

        if response.status_code == 200:
            return response.json()['value']
        else:
            logging.info(f'Erro na solicitação: Código de status {response.status_code}')
            return []

    def search_pacient_by_id(self, pacient_id):
        self.__get_token__()

        url = f"https://api.medicinadireta.com.br/odata/paciente({pacient_id})?" \
              f"$select=id, nome, dataNascimento, idade"

        header = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.__token__}',
        }

        response = requests.get(url, headers=header)

        if response.status_code == 200:
            return response.json()
        else:
            logging.info(f'Erro na solicitação: Código de status {response.status_code}')
            logging.info(response.text)
            return []


    def search_professional_by_id(self, professional_id):
        self.__get_token__()

        url = f"https://api.medicinadireta.com.br/odata/Usuario({professional_id})?"
              # f"$select=id, nome, dataNascimento, idade"

        header = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.__token__}',
        }

        response = requests.get(url, headers=header)

        if response.status_code == 200:
            return response.json()
        else:
            logging.info(f'Erro na solicitação: Código de status {response.status_code}')
            logging.info(response.text)
            return []

    def agenda_atendidos(self, data):
        self.__get_token__()

        url = "https://api.medicinadireta.com.br/odata/Agenda?" \
              "$filter=agendaStatus/descricao eq 'ATENDIDO'" \
              "&$select=pacienteId, agendaStatus, horaInicio, dataInicio" \


        header = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.__token__}',
            "datainicio": data,
            "datafim": data
        }

        response = requests.get(url, headers=header)

        if response.status_code == 200:
            return response.json()['value']
        else:
            logging.info(f'Erro na solicitação: Código de status {response.status_code}')
            logging.info(response.text)
            return []
        
    def agenda_agendados(self, data):
        self.__get_token__()

        url = "https://api.medicinadireta.com.br/odata/Agenda?" \
              "$filter=agendaStatus/descricao eq 'AGENDADO'" \
              "&$select=id, pacienteId, profissionalId, horaInicio, dataInicio"
        

        header = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.__token__}',
            "datainicio": data,
            "datafim": data
        }

        response = requests.get(url, headers=header)

        if response.status_code == 200:
            return response.json()['value']
        else:
            logging.info(f'Erro na solicitação: Código de status {response.status_code}')
            logging.info(response.text)
            return []
    
    def confirm_agenda(self, id_agenda):
        """

        :param id_agenda: Id da agenda
        :return:
        """
        self.__get_token__()

        url = 'https://api.medicinadireta.com.br/odata/Agenda/Confirmar'
        header = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.__token__}'
        }

        body = {
            'id': id_agenda
        }
        body = json.dumps(body)

        response = requests.post(url, headers=header, data=body)

        if response.status_code == 200:
            return True
        else:
            logging.info(f'Erro na solicitação do Token: Código de status {response.status_code}')
            logging.info(response.text)

    def cancel_agenda(self, id_agenda):
        """

        :param id_agenda: Id da agenda
        :return:
        """
        self.__get_token__()

        url = f'https://api.medicinadireta.com.br/odata/Agenda/{id_agenda}/Desmarcar'
        header = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.__token__}'
        }

        body = {
            "desmarcar": {
                "Liberar": "N",
                "Justificativa": "Desmarcado pela Automação do WhatsApp"
            }
        }
        body = json.dumps(body)

        response = requests.post(url, headers=header, data=body)

        if response.status_code == 200:
            return True
        else:
            logging.info(f'Erro na solicitação do Token: Código de status {response.status_code}')
            logging.info(response.text)

        

class WhatsAppAPI:
    def __init__(self):
        self.url = f"https://graph.facebook.com/v17.0/{os.environ['PHONE_ID']}/messages"

    def header(self, body):
        header = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {os.environ["TOKEN"]}'
        }

        body = json.dumps(body)

        response = requests.post(self.url, headers=header, data=body)

        return response


    def send_default_reply(self, phone_number):
        body = {"messaging_product": "whatsapp",
                "to": str(phone_number),
                "type": "text",
                "text": {
                    "preview_url": False,
                    "body": "Olá! Esta é a nossa central de notificações da Clínica Olha.\n"
                            "Se precisar falar conosco, por favor, entre em contato utilizando o número abaixo.\n"
                            "Estamos aqui para ajudar.💙"
                }
                }

        self.header(body)

        body = {"messaging_product": "whatsapp",
                "to": str(phone_number),
                "type": "contacts",
                "contacts": [{
                    "name": {
                        "formatted_name": "Clinica Olha",
                        "first_name": "Clinica Olha"
                    },
                    "phones": [
                        {
                            "phone": "55 62 9830-9902",
                            "type": "MAIN",
                            "wa_id": "556298309902"
                        }]
                }]
                }

        response = self.header(body)

        return response

    def send_custom_message(self, phone_number, text):
        body = {"messaging_product": "whatsapp",
             "to": str(phone_number),
             "type": "text",
             "text": {
                         "preview_url": False,
                         "body": text
                     }
             }

        response = self.header(body)

        return response

    def text_body_component(self, qtd_parameters, *args):
        component = [{"type": "body",
                      "parameters": []}]

        for i in range(qtd_parameters):
            component[0]['parameters'].append({"type": "text",
                                               "text": args[i]})

        return component

    def send_template_message(self, phone_number, template, component):
        body = {"messaging_product": "whatsapp",
             "to": str(phone_number),
             "type": "template",
             "template": {"name": template,
                          "language": {"code": "pt_BR"},
                          "components": component
                          }
                }

        response = self.header(body)

        return response
        