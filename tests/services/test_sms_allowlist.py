"""
Tests for the SMS recipient allowlist (WOF-42 Part A).

The hosted dev stack sends real SMS through a live Twilio account. These
rails make sure it can only ever text numbers on ``SMS_ALLOWED_NUMBERS``,
and that a dev deploy with no allowlist sends nothing at all — even if prod
data (real coworker numbers) ends up in its database.

Rules:
- ``SMS_ALLOWED_NUMBERS`` set → only those numbers are sent to, in any mode.
- ``APP_ENV=dev`` + real Twilio + empty allowlist → every send is blocked.
- Neither set (prod) → behavior unchanged.
- A blocked send raises ``SMSRecipientBlockedError`` (a permanent
  ``SMSDeliveryError``), never calls Twilio, and never logs the full number.
"""

import os
from unittest.mock import MagicMock, patch

import pytest

from src.models import TeamMember
from src.services.sms_service import (
    SMSDeliveryError,
    SMSRecipientBlockedError,
    SMSService,
)


ALLOWED = "+15550001111"
OTHER = "+15550002222"

TWILIO_ENV = {
    "TWILIO_ACCOUNT_SID": "ACallowlist0000000000000000000000",
    "TWILIO_AUTH_TOKEN": "allowlist-test-token-000000000000",  # gitleaks:allow (test-only fake token)
    "TWILIO_PHONE_NUMBER": "+15559990000",
}


@pytest.fixture
def live_service(test_db_session):
    """Build an env-configured (non-mock) SMSService with a mocked Twilio client."""
    def _build(extra_env):
        env = {**TWILIO_ENV, **extra_env}
        with patch.dict(os.environ, env, clear=True), \
                patch("src.services.sms_service.Client") as mock_client_cls:
            client = MagicMock()
            client.messages.create.return_value = MagicMock(sid="SMlive", status="queued")
            mock_client_cls.return_value = client
            service = SMSService(test_db_session, mock_mode=False)
        return service, client
    return _build


class TestAllowlistEnforcement:

    def test_allowlisted_number_is_sent(self, live_service):
        service, client = live_service({"SMS_ALLOWED_NUMBERS": ALLOWED})

        result = service._send_sms(ALLOWED, "hello")

        assert result["sid"] == "SMlive"
        client.messages.create.assert_called_once()

    def test_other_number_is_blocked_without_calling_twilio(self, live_service):
        service, client = live_service({"SMS_ALLOWED_NUMBERS": ALLOWED})

        with pytest.raises(SMSRecipientBlockedError):
            service._send_sms(OTHER, "hello")

        client.messages.create.assert_not_called()

    def test_blocked_error_is_permanent_delivery_error(self):
        assert issubclass(SMSRecipientBlockedError, SMSDeliveryError)

    def test_blocked_error_message_masks_the_number(self, live_service):
        service, _ = live_service({"SMS_ALLOWED_NUMBERS": ALLOWED})

        with pytest.raises(SMSRecipientBlockedError) as exc_info:
            service._send_sms(OTHER, "hello")

        assert OTHER not in str(exc_info.value)
        assert "2222" in str(exc_info.value)

    def test_allowlist_parses_commas_and_whitespace(self, live_service):
        service, client = live_service(
            {"SMS_ALLOWED_NUMBERS": f" {OTHER} , {ALLOWED},, "}
        )

        service._send_sms(ALLOWED, "a")
        service._send_sms(OTHER, "b")

        assert client.messages.create.call_count == 2

    def test_allowlist_also_applies_in_mock_mode(self, test_db_session):
        with patch.dict(os.environ, {"SMS_ALLOWED_NUMBERS": ALLOWED}, clear=True):
            service = SMSService(test_db_session, mock_mode=True)

        with pytest.raises(SMSRecipientBlockedError):
            service._send_sms(OTHER, "hello")


class TestDevFailClosed:

    def test_dev_with_live_twilio_and_no_allowlist_blocks_everything(self, live_service):
        service, client = live_service({"APP_ENV": "dev"})

        with pytest.raises(SMSRecipientBlockedError):
            service._send_sms(ALLOWED, "hello")

        client.messages.create.assert_not_called()

    def test_dev_with_blank_allowlist_blocks_everything(self, live_service):
        service, client = live_service({"APP_ENV": "dev", "SMS_ALLOWED_NUMBERS": " , "})

        with pytest.raises(SMSRecipientBlockedError):
            service._send_sms(ALLOWED, "hello")

        client.messages.create.assert_not_called()

    def test_dev_with_allowlist_sends_to_allowed_number(self, live_service):
        service, client = live_service({"APP_ENV": "DEV", "SMS_ALLOWED_NUMBERS": ALLOWED})

        service._send_sms(ALLOWED, "hello")

        client.messages.create.assert_called_once()

    def test_dev_in_mock_mode_without_allowlist_still_sends_mock(self, test_db_session):
        """Local Mac dev (SMS_MOCK_MODE=true) keeps working with no allowlist."""
        with patch.dict(os.environ, {"APP_ENV": "dev"}, clear=True):
            service = SMSService(test_db_session, mock_mode=True)

        result = service._send_sms(OTHER, "hello")

        assert result["sid"].startswith("SM")

    def test_prod_without_allowlist_is_unchanged(self, live_service):
        service, client = live_service({})

        service._send_sms(OTHER, "hello")

        client.messages.create.assert_called_once()


class TestBlockedSendsThroughCallers:

    def test_manual_notification_blocked_is_logged_failed(self, live_service, test_db_session):
        member = TeamMember(name="Not Allowed", phone=OTHER, is_active=True)
        test_db_session.add(member)
        test_db_session.commit()
        service, client = live_service({"SMS_ALLOWED_NUMBERS": ALLOWED})

        result = service.send_manual_notification(team_member=member, message="hi")

        assert result["success"] is False
        assert result["status"] == "failed"
        client.messages.create.assert_not_called()

    def test_scheduled_send_blocked_is_not_retried(self, live_service, populated_schedules):
        schedule = populated_schedules[0]
        service, client = live_service({"SMS_ALLOWED_NUMBERS": ALLOWED})
        service.base_delay = 0

        result = service._send_to_single_phone(
            phone=OTHER,
            message_body="test",
            schedule=schedule,
            phone_type="primary",
            recipient_name="Test User",
        )

        assert result["success"] is False
        client.messages.create.assert_not_called()
        failed_rows = service.notification_repo.get_retry_count_for_schedule(schedule.id)
        assert failed_rows == 1
