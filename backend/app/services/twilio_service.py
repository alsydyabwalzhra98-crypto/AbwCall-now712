from typing import List, Optional
import phonenumbers

from app.core.config import settings
from app.schemas.call import CallRate


class TwilioService:
    def __init__(self):
        self.twilio_phone_number = settings.TWILIO_PHONE_NUMBER
        self._client = None

    @property
    def client(self):
        if self._client is None:
            if not settings.TWILIO_ACCOUNT_SID or not settings.TWILIO_AUTH_TOKEN:
                raise Exception("Twilio credentials are not configured. Please set TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN.")
            from twilio.rest import Client
            self._client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        return self._client

    def make_call(self, to: str, from_number: str, callback_url: str):
        """
        Make a phone call using Twilio
        """
        from twilio.base.exceptions import TwilioRestException
        try:
            call = self.client.calls.create(
                to=to,
                from_=from_number,
                url=callback_url,
                method="POST"
            )
            return call
        except TwilioRestException as e:
            raise Exception(f"Twilio error: {str(e)}")

    def end_call(self, call_sid: str):
        """
        End an active call
        """
        from twilio.base.exceptions import TwilioRestException
        try:
            call = self.client.calls(call_sid).update(status="completed")
            return call
        except TwilioRestException as e:
            raise Exception(f"Twilio error: {str(e)}")

    def get_call_rate(self, phone_number: str) -> Optional[CallRate]:
        """
        Get call rate for a phone number
        """
        try:
            parsed_number = phonenumbers.parse(phone_number)
            country_code = parsed_number.country_code
            country_name = phonenumbers.region_code_for_number(parsed_number)

            rates = {
                "US": 0.01,
                "GB": 0.02,
                "CA": 0.015,
                "AU": 0.025,
                "DE": 0.03,
                "FR": 0.03,
                "SA": 0.05,
                "AE": 0.04,
                "EG": 0.06,
                "JO": 0.05,
            }

            rate = rates.get(country_name, 0.10)

            return CallRate(
                country=country_name,
                country_code=f"+{country_code}",
                rate=rate,
                currency="USD"
            )
        except Exception:
            return None

    def get_all_call_rates(self) -> List[CallRate]:
        """
        Get all available call rates
        """
        return [
            CallRate(country="US", country_code="+1", rate=0.01, currency="USD"),
            CallRate(country="GB", country_code="+44", rate=0.02, currency="USD"),
            CallRate(country="CA", country_code="+1", rate=0.015, currency="USD"),
            CallRate(country="AU", country_code="+61", rate=0.025, currency="USD"),
            CallRate(country="DE", country_code="+49", rate=0.03, currency="USD"),
            CallRate(country="FR", country_code="+33", rate=0.03, currency="USD"),
            CallRate(country="SA", country_code="+966", rate=0.05, currency="USD"),
            CallRate(country="AE", country_code="+971", rate=0.04, currency="USD"),
            CallRate(country="EG", country_code="+20", rate=0.06, currency="USD"),
            CallRate(country="JO", country_code="+962", rate=0.05, currency="USD"),
        ]
