from modules.order.application.ports.driver.remove_line_port import (
    RemoveLinePort, RemoveLineCommand, RemoveLineResponse
)
from modules.order.application.ports.driven.order_repository import OrderRepository
from modules.order.domain.errors.order_errors import OrderNotFound


class RemoveLineUseCase(RemoveLinePort):
    def __init__(self, order_repo: OrderRepository):
        self.order_repo = order_repo

    def remove_line(self, command: RemoveLineCommand) -> RemoveLineResponse:
        order = self.order_repo.get_by_id(command.order_id)
        if not order:
            raise OrderNotFound("Order not found")

        order.remove_line(command.product_id)
        self.order_repo.save(order)
        
        return RemoveLineResponse(
            order_id=order.id,
            total_amount=str(order.total_amount),
            line_count=len(order.lines)
        )
