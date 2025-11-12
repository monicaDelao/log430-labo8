"""
Handler: Stock Decrease Failed
SPDX-License-Identifier: LGPL-3.0-or-later
Auteurs : Gabriel C. Ullmann, Fabio Petrillo, 2025
"""
from typing import Dict, Any
import config
from event_management.base_handler import EventHandler
from orders.commands.order_event_producer import OrderEventProducer


class StockDecreaseFailedHandler(EventHandler):
    """Handles StockDecreaseFailed events"""
    
    def __init__(self):
        self.order_producer = OrderEventProducer()
        super().__init__()
    
    def get_event_type(self) -> str:
        """Get event type name"""
        return "StockDecreaseFailed"
    
    def handle(self, event_data: Dict[str, Any]) -> None:
        """Execute every time the event is published"""
        try:
            # La diminution de stock a échoué (par ex: stock insuffisant)
            # On ne peut pas continuer la saga, il faut annuler la commande
            self.logger.error(f"Échec de la diminution du stock pour la commande {event_data['order_id']}: {event_data.get('error', 'Unknown error')}")
            
            # Passer directement à l'annulation de la commande
            # Pas besoin de remettre le stock car la diminution a échoué
            event_data['event'] = "OrderCancelled"
            event_data['cancellation_reason'] = f"Stock insuffisant: {event_data.get('error', 'Unknown error')}"
            
        except Exception as e:
            # Si même la gestion d'erreur échoue, logguer et continuer l'annulation
            self.logger.error(f"Erreur lors de la gestion de l'échec de stock: {str(e)}")
            event_data['event'] = "OrderCancelled"
            event_data['cancellation_reason'] = f"Erreur de gestion: {str(e)}"
        finally:
            OrderEventProducer().get_instance().send(config.KAFKA_TOPIC, value=event_data)
  
