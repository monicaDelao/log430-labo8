"""
Handler: Stock Increased
SPDX-License-Identifier: LGPL-3.0-or-later
Auteurs : Gabriel C. Ullmann, Fabio Petrillo, 2025
"""
from typing import Dict, Any
import config
from db import get_sqlalchemy_session
from event_management.base_handler import EventHandler
from orders.commands.order_event_producer import OrderEventProducer
from stocks.commands.write_stock import check_in_items_to_stock


class StockIncreasedHandler(EventHandler):
    """Handles StockIncrease events"""
    
    def __init__(self):
        self.order_producer = OrderEventProducer()
        super().__init__()
    
    def get_event_type(self) -> str:
        """Get event type name"""
        return "StockIncreased"
    
    def handle(self, event_data: Dict[str, Any]) -> None:
        """Execute every time the event is published"""
        try:
            # Compensation: remettre les items en stock (augmenter les quantités)
            session = get_sqlalchemy_session()
            check_in_items_to_stock(session, event_data['order_items'])
            session.commit()
            self.logger.debug(f"Stock restauré pour la commande {event_data['order_id']}")
            
            # Si l'opération a réussi, déclenchez OrderCancelled
            event_data['event'] = "OrderCancelled"
        except Exception as e:
            session.rollback()
            # Si l'opération de compensation a échoué, gardez l'erreur mais continuez
            self.logger.error(f"Échec de la compensation du stock: {str(e)}")
            event_data['event'] = "OrderCancelled"  # Continuer quand même la compensation
            event_data['stock_compensation_error'] = str(e)
        finally:
            session.close()
            OrderEventProducer().get_instance().send(config.KAFKA_TOPIC, value=event_data)



