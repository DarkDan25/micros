import pytest
from uuid import uuid4
from datetime import datetime
from app.models.bonus import BonusReason, EarnBonusRequest, ApplyBonusRequest, AdjustBonusRequest
from app.services.bonus_service import BonusService
from unittest.mock import Mock


@pytest.fixture
def mock_bonus_repo():
    return Mock()


@pytest.fixture
def bonus_service(mock_bonus_repo):
    service = BonusService()
    service.bonus_repo = mock_bonus_repo
    return service


class TestBonusService:
    
    @pytest.mark.unit
    def test_earn_bonus_success(self, bonus_service, mock_bonus_repo):
        # Arrange
        user_id = uuid4()
        current_balance = 50
        earn_amount = 100
        
        mock_bonus_repo.get_user_balance.return_value = current_balance
        mock_bonus_repo.create_operation.return_value = Mock(
            operation_id=uuid4(),
            user_id=user_id,
            delta=earn_amount,
            balance_after=current_balance + earn_amount,
            reason=BonusReason.PURCHASE,
            description="Test bonus",
            external_operation_id="ext_123",
            created_at=datetime.now()
        )
        
        request = EarnBonusRequest(
            user_id=user_id,
            amount=earn_amount,
            reason=BonusReason.PURCHASE,
            description="Test bonus",
            external_operation_id="ext_123"
        )
        
        # Act
        result = bonus_service.earn_bonus(request)
        
        # Assert
        assert result.delta == earn_amount
        assert result.balance_after == current_balance + earn_amount
        mock_bonus_repo.get_user_balance.assert_called_once_with(user_id)
        mock_bonus_repo.create_operation.assert_called_once()
    
    @pytest.mark.unit
    def test_apply_bonus_success(self, bonus_service, mock_bonus_repo):
        # Arrange
        user_id = uuid4()
        current_balance = 150
        apply_amount = 50
        
        mock_bonus_repo.get_user_balance.return_value = current_balance
        mock_bonus_repo.create_operation.return_value = Mock(
            operation_id=uuid4(),
            user_id=user_id,
            delta=-apply_amount,
            balance_after=current_balance - apply_amount,
            reason=BonusReason.ORDER_PAYMENT,
            description="Apply bonus",
            external_operation_id="ext_456",
            created_at=datetime.now()
        )
        
        request = ApplyBonusRequest(
            user_id=user_id,
            amount=apply_amount,
            reason=BonusReason.ORDER_PAYMENT,
            description="Apply bonus",
            external_operation_id="ext_456"
        )
        
        # Act
        result = bonus_service.apply_bonus(request)
        
        # Assert
        assert result.delta == -apply_amount
        assert result.balance_after == current_balance - apply_amount
        mock_bonus_repo.get_user_balance.assert_called_once_with(user_id)
        mock_bonus_repo.create_operation.assert_called_once()
    
    @pytest.mark.unit
    def test_apply_bonus_insufficient_balance(self, bonus_service, mock_bonus_repo):
        # Arrange
        user_id = uuid4()
        current_balance = 30
        apply_amount = 50
        
        mock_bonus_repo.get_user_balance.return_value = current_balance
        
        request = ApplyBonusRequest(
            user_id=user_id,
            amount=apply_amount,
            reason=BonusReason.ORDER_PAYMENT,
            description="Apply bonus",
            external_operation_id="ext_456"
        )
        
        # Act & Assert
        with pytest.raises(ValueError, match="Insufficient bonus balance"):
            bonus_service.apply_bonus(request)
    
    @pytest.mark.unit
    def test_adjust_balance_positive(self, bonus_service, mock_bonus_repo):
        # Arrange
        user_id = uuid4()
        current_balance = 100
        adjust_amount = 25
        
        mock_bonus_repo.get_user_balance.return_value = current_balance
        mock_bonus_repo.create_operation.return_value = Mock(
            operation_id=uuid4(),
            user_id=user_id,
            delta=adjust_amount,
            balance_after=current_balance + adjust_amount,
            reason=BonusReason.SUPPORT_ADJUSTMENT,
            description="Support adjustment",
            external_operation_id="ext_789",
            created_at=datetime.now()
        )
        
        request = AdjustBonusRequest(
            user_id=user_id,
            delta=adjust_amount,
            reason=BonusReason.SUPPORT_ADJUSTMENT,
            description="Support adjustment",
            external_operation_id="ext_789"
        )
        
        # Act
        result = bonus_service.adjust_balance(request)
        
        # Assert
        assert result.delta == adjust_amount
        assert result.balance_after == current_balance + adjust_amount
    
    @pytest.mark.unit
    def test_adjust_balance_negative_balance(self, bonus_service, mock_bonus_repo):
        # Arrange
        user_id = uuid4()
        current_balance = 50
        adjust_amount = -60
        
        mock_bonus_repo.get_user_balance.return_value = current_balance
        
        request = AdjustBonusRequest(
            user_id=user_id,
            delta=adjust_amount,
            reason=BonusReason.SUPPORT_ADJUSTMENT,
            description="Support adjustment",
            external_operation_id="ext_789"
        )
        
        # Act & Assert
        with pytest.raises(ValueError, match="Balance cannot be negative"):
            bonus_service.adjust_balance(request)
    
    @pytest.mark.unit
    def test_get_balance(self, bonus_service, mock_bonus_repo):
        # Arrange
        user_id = uuid4()
        balance = 200
        last_operation = Mock(created_at=datetime.now())
        
        mock_bonus_repo.get_user_balance.return_value = balance
        mock_bonus_repo.get_last_operation.return_value = last_operation
        
        # Act
        result = bonus_service.get_balance(user_id)
        
        # Assert
        assert result.user_id == user_id
        assert result.balance == balance
        assert result.updated_at == last_operation.created_at
    
    @pytest.mark.unit
    def test_get_balance_no_operations(self, bonus_service, mock_bonus_repo):
        # Arrange
        user_id = uuid4()
        balance = 0
        
        mock_bonus_repo.get_user_balance.return_value = balance
        mock_bonus_repo.get_last_operation.return_value = None
        
        # Act
        result = bonus_service.get_balance(user_id)
        
        # Assert
        assert result.user_id == user_id
        assert result.balance == balance
        assert isinstance(result.updated_at, datetime)