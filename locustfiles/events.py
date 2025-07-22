from faker import Faker
from locust import HttpLocust, HttpUser, TaskSet, task, events, between
import json
import re
import requests
import random
import subprocess
from uuid import uuid4
fake = Faker()

def generate_event_payload():
    return {
        "id": str(uuid4()),
        "name": fake.catch_phrase(),
        "summary": fake.sentence(),
        "code": fake.bothify(text="EVT-####"),
        "maximumAttendees": random.randint(10, 500),
        "category": {
            "id": str(uuid4()),
            "name": fake.word(),
            "status": "ACTIVE"
        },
        "topic": {
            "id": str(uuid4()),
            "name": fake.word(),
            "status": "ACTIVE"
        },
        "campaign": {
            "id": str(uuid4()),
            "name": fake.word(),
            "status": "ACTIVE"
        },
        "publishEvent": True,
        "enableEventRegistrationForm": True,
        "archived": False,
        "enableWaitListing": True,
        "createAccountsforAttendees": True,
        "eventDescription": fake.paragraph(),
        "eventDates": {
            "startDate": fake.iso8601(),
            "endDate": fake.iso8601(),
            "startTime": fake.time(),
            "endTime": fake.time(),
            "registrationOpenDate": fake.iso8601(),
            "registrationCloseDate": fake.iso8601(),
            "timeZone": {
                "id": str(uuid4()),
                "name": fake.timezone(),
                "status": "ACTIVE"
            }
        },
        "financialSettings": {
            "feeType": "Free",
            "admissionFee": {
                "fee": round(random.uniform(0, 100), 2),
                "craInfo": {
                    "advantageAmount": random.randint(0, 100),
                    "advantageDescription": fake.sentence()
                },
                "taxDeductibleInfo": {
                    "nonDeductibleAmount": random.randint(0, 100),
                    "nonDeductibleDescription": fake.sentence()
                }
            },
            "ticketsPerRegistration": {
                "number": random.randint(1, 10),
                "operator": "Up_to"
            },
            "fund": {
                "id": str(uuid4()),
                "name": fake.word(),
                "status": "ACTIVE"
            },
            "taxDeductiblePortion": {
                "fund": {
                    "id": str(uuid4()),
                    "name": fake.word(),
                    "status": "ACTIVE"
                },
                "purpose": {
                    "id": str(uuid4()),
                    "name": fake.word(),
                    "status": "ACTIVE"
                }
            },
            "donations": {
                "type": "None",
                "label": fake.word()
            }
        },
        "location": {
            "name": fake.company(),
            "roomNumber": fake.bothify(text="Room-###"),
            "buildingNumber": fake.bothify(text="Bldg-##"),
            "address": fake.street_address(),
            "city": fake.city(),
            "stateProvince": {
                "code": fake.state_abbr(),
                "name": fake.state(),
                "status": "ACTIVE"
            },
            "country": {
                "id": str(uuid4()),
                "name": fake.country(),
                "status": "ACTIVE"
            },
            "zipCode": fake.zipcode(),
            "zipCodeSuffix": fake.postcode()
        },
        "thumbnailUrl": fake.image_url()
    }

def generate_ticket_payload():
    return {
        "id": random.randint(1, 10000),
        "name": fake.word().capitalize() + " Ticket",
        "description": fake.sentence(),
        "fee": round(random.uniform(0, 200), 2),
        "maxNumberAvailable": random.randint(1, 500),
        "numberRemaining": random.randint(0, 500),
        "attendeesPerTicketType": "Up_to",
        "attendeesPerTicketNumber": random.randint(1, 10),
        "craInfo": {
            "advantageAmount": random.randint(0, 100),
            "advantageDescription": fake.sentence()
        },
        "taxDeductibleInfo": {
            "nonDeductibleAmount": random.randint(0, 100),
            "nonDeductibleDescription": fake.sentence()
        }
    }

class NGE_API_Test(HttpUser):
    wait_time = between(0.5, 5)


    @task
    def create_then_delete_event(self):
        # Create event
        payload = generate_event_payload()
        create_resp = self.client.post("/api/events", json=payload)
        if create_resp.status_code != 201:
            print(f"POST /api/events status: {create_resp.status_code}")
            print(f"Response content: {create_resp.content}")
            return
        event_id = None
        try:
            event_id = create_resp.json().get("id")
        except Exception as e:
            print(f"Failed to parse event id from response: {e}")
            print(f"Response content: {create_resp.content}")
            return
        if not event_id:
            print("No event id returned from create event response.")
            print(f"Response content: {create_resp.content}")
            return

        get_resp = self.client.get(f"/api/events/{event_id}")
        if get_resp.status_code != 200:
            print(f"GET /api/events/{event_id} status: {get_resp.status_code}")
            print(f"Response content: {get_resp.content}")

        put_payload = generate_event_payload()
        put_resp = self.client.put(f"/api/events/{event_id}", json=put_payload)
        if put_resp.status_code != 200:
            print(f"PUT /api/events/{event_id} status: {put_resp.status_code}")
            print(f"Response content: {put_resp.content}")

        patch_payload = generate_event_payload()
        patch_resp = self.client.patch(f"/api/events/{event_id}", json=patch_payload)
        if patch_resp.status_code != 200:
            print(f"PATCH /api/events/{event_id} status: {patch_resp.status_code}")
            print(f"Response content: {patch_resp.content}")

        del_resp = self.client.delete(f"/api/events/{event_id}")
        if del_resp.status_code != 200:
            print(f"DELETE /api/events/{event_id} status: {del_resp.status_code}")
            print(f"Response content: {del_resp.content}")

    @task
    def get_ticket_option(self):
        event_id = 1
        ticket_id = 1
        response = self.client.get(f"/api/events/{event_id}/tickets/{ticket_id}")
        if response.status_code != 200:
            print(f"GET /api/events/{event_id}/tickets/{ticket_id} status: {response.status_code}")
            print(f"Response content: {response.content}")

    @task
    def put_ticket_option(self):
        event_id = 1
        ticket_id = 1
        payload = generate_ticket_payload()
        response = self.client.put(f"/api/events/{event_id}/tickets/{ticket_id}", json=payload)
        if response.status_code != 200:
            print(f"PUT /api/events/{event_id}/tickets/{ticket_id} status: {response.status_code}")
            print(f"Response content: {response.content}")

    @task
    def delete_ticket_option(self):
        event_id = 1
        ticket_id = 1
        response = self.client.delete(f"/api/events/{event_id}/tickets/{ticket_id}")
        if response.status_code != 200:
            print(f"DELETE /api/events/{event_id}/tickets/{ticket_id} status: {response.status_code}")
            print(f"Response content: {response.content}")

    @task
    def patch_ticket_option(self):
        event_id = 1
        ticket_id = 1
        payload = {"option": "Patched Option"}
        response = self.client.patch(f"/api/events/{event_id}/tickets/{ticket_id}", json=payload)
        if response.status_code != 200:
            print(f"PATCH /api/events/{event_id}/tickets/{ticket_id} status: {response.status_code}")
            print(f"Response content: {response.content}")

    @task
    def put_event_category(self):
        category_id = 1
        payload = {"name": "Updated Category"}
        response = self.client.put(f"/api/events/categories/{category_id}", json=payload)
        if response.status_code != 200:
            print(f"PUT /api/events/categories/{category_id} status: {response.status_code}")
            print(f"Response content: {response.content}")

    @task
    def delete_event_category(self):
        category_id = 1
        response = self.client.delete(f"/api/events/categories/{category_id}")
        if response.status_code != 200:
            print(f"DELETE /api/events/categories/{category_id} status: {response.status_code}")
            print(f"Response content: {response.content}")

    @task
    def patch_event_category(self):
        category_id = 1
        payload = {"description": "Patched Category"}
        response = self.client.patch(f"/api/events/categories/{category_id}", json=payload)
        if response.status_code != 200:
            print(f"PATCH /api/events/categories/{category_id} status: {response.status_code}")
            print(f"Response content: {response.content}")

    @task
    def get_events(self):
        response = self.client.get("/api/events")
        if response.status_code != 200:
            print(f"GET /api/events status: {response.status_code}")
            print(f"Response content: {response.content}")



    @task
    def get_event_tickets(self):
        event_id = 1
        response = self.client.get(f"/api/events/{event_id}/tickets")
        if response.status_code != 200:
            print(f"GET /api/events/{event_id}/tickets status: {response.status_code}")
            print(f"Response content: {response.content}")

    @task
    def post_event_ticket(self):
        event_id = 1
        payload = {"option": "New Ticket Option"}
        response = self.client.post(f"/api/events/{event_id}/tickets", json=payload)
        if response.status_code != 200:
            print(f"POST /api/events/{event_id}/tickets status: {response.status_code}")
            print(f"Response content: {response.content}")

    @task
    def post_events_search(self):
        payload = {"query": "search term"}
        response = self.client.post("/api/events/search", json=payload)
        if response.status_code != 200:
            print(f"POST /api/events/search status: {response.status_code}")
            print(f"Response content: {response.content}")

    @task
    def get_event_categories(self):
        response = self.client.get("/api/events/categories")
        if response.status_code != 200:
            print(f"GET /api/events/categories status: {response.status_code}")
            print(f"Response content: {response.content}")

    @task
    def post_event_category(self):
        payload = {"name": "New Category"}
        response = self.client.post("/api/events/categories", json=payload)
        if response.status_code != 200:
            print(f"POST /api/events/categories status: {response.status_code}")
            print(f"Response content: {response.content}")

    @task
    def get_event_registrations(self):
        event_id = 1
        response = self.client.get(f"/api/events/{event_id}/eventRegistrations")
        if response.status_code != 200:
            print(f"GET /api/events/{event_id}/eventRegistrations status: {response.status_code}")
            print(f"Response content: {response.content}")

    @task
    def get_event_attendees(self):
        event_id = 1
        response = self.client.get(f"/api/events/{event_id}/attendees")
        if response.status_code != 200:
            print(f"GET /api/events/{event_id}/attendees status: {response.status_code}")
            print(f"Response content: {response.content}")

    @task
    def get_search_fields(self):
        response = self.client.get("/api/events/search/searchFields")
        if response.status_code != 200:
            print(f"GET /api/events/search/searchFields status: {response.status_code}")
            print(f"Response content: {response.content}")

    @task
    def get_output_fields(self):
        response = self.client.get("/api/events/search/outputFields")
        if response.status_code != 200:
            print(f"GET /api/events/search/outputFields status: {response.status_code}")
            print(f"Response content: {response.content}")

