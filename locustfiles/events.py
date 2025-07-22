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

class NGE_API_Test(HttpUser):
    wait_time = between(0.5, 5)

    @task
    def get_event(self):
        event_id = 1  # Replace with dynamic or random ID as needed
        self.client.get(f"/api/events/{event_id}")

    @task
    def put_event(self):
        event_id = 1
        payload = generate_event_payload()
        self.client.put(f"/api/events/{event_id}", json=payload)

    @task
    def delete_event(self):
        event_id = 1
        self.client.delete(f"/api/events/{event_id}")

    @task
    def patch_event(self):
        event_id = 1
        payload = {"description": "Patched Event"}
        self.client.patch(f"/api/events/{event_id}", json=payload)

    @task
    def get_ticket_option(self):
        event_id = 1
        ticket_id = 1
        self.client.get(f"/api/events/{event_id}/tickets/{ticket_id}")

    @task
    def put_ticket_option(self):
        event_id = 1
        ticket_id = 1
        payload = {"option": "Updated Option"}
        self.client.put(f"/api/events/{event_id}/tickets/{ticket_id}", json=payload)

    @task
    def delete_ticket_option(self):
        event_id = 1
        ticket_id = 1
        self.client.delete(f"/api/events/{event_id}/tickets/{ticket_id}")

    @task
    def patch_ticket_option(self):
        event_id = 1
        ticket_id = 1
        payload = {"option": "Patched Option"}
        self.client.patch(f"/api/events/{event_id}/tickets/{ticket_id}", json=payload)

    @task
    def put_event_category(self):
        category_id = 1
        payload = {"name": "Updated Category"}
        self.client.put(f"/api/events/categories/{category_id}", json=payload)

    @task
    def delete_event_category(self):
        category_id = 1
        self.client.delete(f"/api/events/categories/{category_id}")

    @task
    def patch_event_category(self):
        category_id = 1
        payload = {"description": "Patched Category"}
        self.client.patch(f"/api/events/categories/{category_id}", json=payload)

    @task
    def get_events(self):
        self.client.get("/api/events")

    @task
    def post_event(self):
        payload = {"name": "New Event"}
        self.client.post("/api/events", json=payload)

    @task
    def get_event_tickets(self):
        event_id = 1
        self.client.get(f"/api/events/{event_id}/tickets")

    @task
    def post_event_ticket(self):
        event_id = 1
        payload = {"option": "New Ticket Option"}
        self.client.post(f"/api/events/{event_id}/tickets", json=payload)

    @task
    def post_events_search(self):
        payload = {"query": "search term"}
        self.client.post("/api/events/search", json=payload)

    @task
    def get_event_categories(self):
        self.client.get("/api/events/categories")

    @task
    def post_event_category(self):
        payload = {"name": "New Category"}
        self.client.post("/api/events/categories", json=payload)

    @task
    def get_event_registrations(self):
        event_id = 1
        self.client.get(f"/api/events/{event_id}/eventRegistrations")

    @task
    def get_event_attendees(self):
        event_id = 1
        self.client.get(f"/api/events/{event_id}/attendees")

    @task
    def get_search_fields(self):
        self.client.get("/api/events/search/searchFields")

    @task
    def get_output_fields(self):
        self.client.get("/api/events/search/outputFields")

