from celery import shared_task

from gpon.services.subscriber_data import get_all_subscriber_connections
from gpon.services.tech_data import get_all_tech_data


@shared_task(ignore_result=True)
def set_tech_data_to_cache():
    get_all_tech_data(from_cache=False)


@shared_task(ignore_result=True)
def set_subscriber_connections_data_to_cache():
    get_all_subscriber_connections(from_cache=False)
