import pytest
from unittest.mock import Mock
from modules.order.application.use_cases.start_draft_order_use_case import StartDraftOrderUseCase
from modules.order.application.ports.driver.start_draft_order_ports import StartDraftOrderCommand

def test_start_draft_order_success():
    mock_repo = Mock()
    mock_client_query = Mock()
    mock_client_query.check_client_exists.return_value = True
    
    use_case = StartDraftOrderUseCase(order_repo=mock_repo, client_query=mock_client_query)
    
    command = StartDraftOrderCommand(client_id="client-1")
    response = use_case.execute(command)
    
    assert response.order_id is not None
    assert response.status == "DRAFT"
    
    mock_client_query.check_client_exists.assert_called_once_with("client-1")
    mock_repo.save.assert_called_once()
    saved_order = mock_repo.save.call_args[0][0]
    assert saved_order.client_id == "client-1"
    assert saved_order.id == response.order_id

def test_start_draft_order_fails_if_client_not_found():
    mock_repo = Mock()
    mock_client_query = Mock()
    mock_client_query.check_client_exists.return_value = False
    
    use_case = StartDraftOrderUseCase(order_repo=mock_repo, client_query=mock_client_query)
    
    command = StartDraftOrderCommand(client_id="non-existent")
    with pytest.raises(ValueError):
        use_case.execute(command)
