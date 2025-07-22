import re
import json
import random
from locust import HttpLocust, HttpUser, TaskSet, task, events, between

class NPApiTest(HttpUser):
    wait_time = between(0.500, 5)

    token_list = []

    @events.init_command_line_parser.add_listener
    def _(parser):
        # First add all the keys + ids (note these are the dev.neononepay.com defaults)
        parser.add_argument("--private-key", type=str, default="key_21c4faaa4cf389049358c12a5f434ac1ca73200f1d1f4c3ae8d04fb8")
        parser.add_argument("--public-key", type=str, default="public_d43ac11206bee0632dcce3578d33c69e3f1e10ffe46bc29c34c61627")
        parser.add_argument("--merchant-id", type=str, default="231")

        # Then add the various token request params
        parser.add_argument("--token-type", type=str, default="cc")
        parser.add_argument("--token-first-name", type=str, default="Load")
        parser.add_argument("--token-last-name", type=str, default="Test User")
        parser.add_argument("--token-card-cvc", type=str, default="666")
        parser.add_argument("--token-card-number", type=str, default="4242424242424242")
        parser.add_argument("--token-expiration-date", type=str, default="12/28")
        parser.add_argument("--token-email", type=str, default="load-test@example.com")
        parser.add_argument("--token-phone", type=str, default="5555555555")
        parser.add_argument("--token-address-line-1", type=str, default="4545 Load Test Ave.")
        parser.add_argument("--token-address-line-2", type=str, default="Ste. 201")
        parser.add_argument("--token-address-city", type=str, default="Chicago")
        parser.add_argument("--token-address-state", type=str, default="IL")
        parser.add_argument("--token-address-zip", type=str, default="60640")
        parser.add_argument("--token-address-country", type=str, default="US")

    @task
    def charge(self):
        # First make a tokenize request for token

        # Set the appropriate headers on the client
        self.client.headers['Content-Type'] = "application/json"
        self.client.headers['Accept'] = "application/json"
        self.client.headers['X-Api-Key'] = self.environment.parsed_options.private_key
        self.client.headers['X-App-Id'] = "14"
        self.client.headers['X-Merchant-Id'] = self.environment.parsed_options.merchant_id

        token_type = self.environment.parsed_options.token_type
        # Set the post data for a token request
        token_post_json = {
            "merchant_id": self.environment.parsed_options.merchant_id,
            "public_app_key": self.environment.parsed_options.public_key,
            "type": token_type,
            "first_name": self.environment.parsed_options.token_first_name,
            "last_name": self.environment.parsed_options.token_last_name,
            "email": self.environment.parsed_options.token_email,
            "phone": self.environment.parsed_options.token_phone,
            "address_line_1": self.environment.parsed_options.token_address_line_1,
            "address_line_2": self.environment.parsed_options.token_address_line_2,
            "address_city": self.environment.parsed_options.token_address_city,
            "address_state": self.environment.parsed_options.token_address_state,
            "address_zip": self.environment.parsed_options.token_address_zip,
            "address_country": self.environment.parsed_options.token_address_country
        }

        if token_type == 'cc':
            # Add relevent credit card fields if it's a credit card type test
            token_post_json.update({"card_cvc" : self.environment.parsed_options.token_card_cvc})
            token_post_json.update({"card_number" : self.environment.parsed_options.token_card_number})
            token_post_json.update({"expiration_date" : self.environment.parsed_options.token_expiration_date})
        else:
            # Replace with account_holder_first_name and account_holder_last_name
            # Remove the first_name / last_name if it's an ACH
            token_post_json.update({"account_holder_first_name" : token_post_json['first_name']})
            token_post_json.update({"account_holder_last_name" : token_post_json['last_name']})
            del token_post_json['first_name']
            del token_post_json['last_name']

        token_response = self.client.post("/api/tokenize", data=None, json=token_post_json)

        if token_response.status_code != 200:
            print("Token Response status Error Code:", token_response.status_code)
            print("Token Response status Error Code:", token_response.content)
        json_response_dict = token_response.json()

        # Get the token off the response
        token_for_request = json_response_dict.get('token')

        charge_post_json = {
            "merchant_id": self.environment.parsed_options.merchant_id,
            "amount": random.randint(1,500)*100,
            "type": token_type,
            "currency": "usd",
            "funding_currency": "usd",
            "recurring": False,
            "origin": "ecommerce",
            "description": "Load Test Donation",
            "token": token_for_request,
            "platform_fee": random.randint(1,100),
            "capture":  True,
            "metadata": {
                "key_name": "100",
                "another_key_name": "2",
                "third_key_name": "string"
            },
            "statement_descriptor": "Donation to The Example Foundation",
            "ip": "216.80.4.174"
        }

        charge_response = self.client.post("/api/charges", data=None, json=charge_post_json)
        #Print errors / response if status code is not 200
        if charge_response.status_code != 200:
            print("Charge Response status Error Code:", charge_response.status_code)
            print("Charge Response content:", charge_response.content)