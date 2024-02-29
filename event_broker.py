from rasa.core.brokers.broker import EventBroker
from rasa.utils.endpoints import EndpointConfig
from typing import Any, Dict
import logging
import graypy
import json

class GreylogClient:
    def __init__(self, url, port):
        self.graylog_handler = graypy.GELFUDPHandler(url, port)
        self.logger = logging.getLogger('rasa')
        self.logger.addHandler(self.graylog_handler)
        self.logger.setLevel(logging.INFO)

    def send_event(self, event):
        try:
            self.logger.info(event)
        except Exception as e:
            print(f"Error logging event to Graylog: {e}")

class MyCustomEventBroker(EventBroker):

    def __init__(self, url, port, **kwargs: Any,
    ) -> None:
        self.client = GreylogClient(url, port)
    def publish(self, event: Dict):
        # Send the event to the Greylog server
        self.client.send_event(json.dumps(event))

    @classmethod
    async def from_endpoint_config(
            cls, broker_config: EndpointConfig, event_loop=None
            ) -> EventBroker:
        if broker_config is None:
            return None
        return cls(broker_config.url, **broker_config.kwargs)
