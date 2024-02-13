import os
import logging
from azure.core.credentials import AzureNamedKeyCredential
from azure.data.tables import TableServiceClient

def create_entity(entity):
    credential = AzureNamedKeyCredential("sendwhatsappmessages", os.environ["STORAGE_ACESS_KEY"])
    service = TableServiceClient(endpoint="https://sendwhatsappmessages.table.core.windows.net", credential=credential)
    table_name = 'WhatsAppHistory'

    table = service.get_table_client(table_name)
    table.create_entity(entity)


def query_entity(partition_key, row_key):
    credential = AzureNamedKeyCredential("sendwhatsappmessages", os.environ["STORAGE_ACESS_KEY"])
    service = TableServiceClient(endpoint="https://sendwhatsappmessages.table.core.windows.net", credential=credential)
    table_name = 'WhatsAppHistory'

    table = service.get_table_client(table_name)
    entity = table.get_entity(partition_key=partition_key, row_key=row_key)

    return entity


def test_entity():
    entity = {
        'PartitionKey': 'RecentMessages',
        'RowKey': '5511963918057',
        'time': '02/11/2023 16:00:00',
        'last_message': 'Teste'
    }

    create_entity(entity)
    entity = query_entity('RecentMessages', '5511963918057')
    print(entity)

test_entity()