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
    def event_create_update_delete(self):
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

        # Get event registrations
        reg_resp = self.client.get(f"/api/events/{event_id}/eventRegistrations")
        if reg_resp.status_code != 200:
            print(f"GET /api/events/{event_id}/eventRegistrations status: {reg_resp.status_code}")
            print(f"Response content: {reg_resp.content}")

        # Get event attendees
        att_resp = self.client.get(f"/api/events/{event_id}/attendees")
        if att_resp.status_code != 200:
            print(f"GET /api/events/{event_id}/attendees status: {att_resp.status_code}")
            print(f"Response content: {att_resp.content}")

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
    def tickets_create_update_delete(self):
        # Create event
        event_payload = generate_event_payload()
        create_event_resp = self.client.post("/api/events", json=event_payload)
        if create_event_resp.status_code != 201:
            print(f"POST /api/events status: {create_event_resp.status_code}")
            print(f"Response content: {create_event_resp.content}")
            return
        event_id = None
        try:
            event_id = create_event_resp.json().get("id")
        except Exception as e:
            print(f"Failed to parse event id from response: {e}")
            print(f"Response content: {create_event_resp.content}")
            return
        if not event_id:
            print("No event id returned from create event response.")
            print(f"Response content: {create_event_resp.content}")
            return

        # 1. GET event tickets (should be empty or default)
        get_tickets_resp = self.client.get(f"/api/events/{event_id}/tickets")
        if get_tickets_resp.status_code != 200:
            print(f"GET /api/events/{event_id}/tickets status: {get_tickets_resp.status_code}")
            print(f"Response content: {get_tickets_resp.content}")

        # 2. POST event ticket
        ticket_payload = generate_ticket_payload()
        post_ticket_resp = self.client.post(f"/api/events/{event_id}/tickets", json=ticket_payload)
        if post_ticket_resp.status_code not in (200, 201):
            print(f"POST /api/events/{event_id}/tickets status: {post_ticket_resp.status_code}")
            print(f"Response content: {post_ticket_resp.content}")
            # Clean up event before returning
            self.client.delete(f"/api/events/{event_id}")
            return
        ticket_id = None
        try:
            ticket_id = post_ticket_resp.json().get("id")
        except Exception as e:
            print(f"Failed to parse ticket id from response: {e}")
            print(f"Response content: {post_ticket_resp.content}")
        if not ticket_id:
            print("No ticket id returned from create ticket response.")
            print(f"Response content: {post_ticket_resp.content}")
            self.client.delete(f"/api/events/{event_id}")
            return

        # 3. GET ticket option
        get_ticket_resp = self.client.get(f"/api/events/{event_id}/tickets/{ticket_id}")
        if get_ticket_resp.status_code != 200:
            print(f"GET /api/events/{event_id}/tickets/{ticket_id} status: {get_ticket_resp.status_code}")
            print(f"Response content: {get_ticket_resp.content}")

        # 4. PUT ticket option
        put_ticket_payload = generate_ticket_payload()
        put_ticket_resp = self.client.put(f"/api/events/{event_id}/tickets/{ticket_id}", json=put_ticket_payload)
        if put_ticket_resp.status_code != 200:
            print(f"PUT /api/events/{event_id}/tickets/{ticket_id} status: {put_ticket_resp.status_code}")
            print(f"Response content: {put_ticket_resp.content}")

        # 5. PATCH ticket option
        patch_ticket_payload = {"name": "Patched Ticket"}
        patch_ticket_resp = self.client.patch(f"/api/events/{event_id}/tickets/{ticket_id}", json=patch_ticket_payload)
        if patch_ticket_resp.status_code != 200:
            print(f"PATCH /api/events/{event_id}/tickets/{ticket_id} status: {patch_ticket_resp.status_code}")
            print(f"Response content: {patch_ticket_resp.content}")

        # 6. DELETE ticket option
        del_ticket_resp = self.client.delete(f"/api/events/{event_id}/tickets/{ticket_id}")
        if del_ticket_resp.status_code != 200:
            print(f"DELETE /api/events/{event_id}/tickets/{ticket_id} status: {del_ticket_resp.status_code}")
            print(f"Response content: {del_ticket_resp.content}")

        # Finally, delete the event
        del_event_resp = self.client.delete(f"/api/events/{event_id}")
        if del_event_resp.status_code != 200:
            print(f"DELETE /api/events/{event_id} status: {del_event_resp.status_code}")
            print(f"Response content: {del_event_resp.content}")

    @task
    def category_create_update_delete(self):
        # 1. POST event category
        cat_payload = {"name": fake.word().capitalize() + " Category"}
        post_cat_resp = self.client.post("/api/events/categories", json=cat_payload)
        if post_cat_resp.status_code not in (200, 201):
            print(f"POST /api/events/categories status: {post_cat_resp.status_code}")
            print(f"Response content: {post_cat_resp.content}")
            return
        category_id = None
        try:
            category_id = post_cat_resp.json().get("id")
        except Exception as e:
            print(f"Failed to parse category id from response: {e}")
            print(f"Response content: {post_cat_resp.content}")
        if not category_id:
            print("No category id returned from create category response.")
            print(f"Response content: {post_cat_resp.content}")
            return

        # 2. GET event categories
        get_cat_resp = self.client.get("/api/events/categories")
        if get_cat_resp.status_code != 200:
            print(f"GET /api/events/categories status: {get_cat_resp.status_code}")
            print(f"Response content: {get_cat_resp.content}")

        # 3. PUT event category
        put_cat_payload = {"name": "Updated Category"}
        put_cat_resp = self.client.put(f"/api/events/categories/{category_id}", json=put_cat_payload)
        if put_cat_resp.status_code != 200:
            print(f"PUT /api/events/categories/{category_id} status: {put_cat_resp.status_code}")
            print(f"Response content: {put_cat_resp.content}")

        # 4. PATCH event category
        patch_cat_payload = {"description": "Patched Category"}
        patch_cat_resp = self.client.patch(f"/api/events/categories/{category_id}", json=patch_cat_payload)
        if patch_cat_resp.status_code != 200:
            print(f"PATCH /api/events/categories/{category_id} status: {patch_cat_resp.status_code}")
            print(f"Response content: {patch_cat_resp.content}")

        # 5. DELETE event category
        del_cat_resp = self.client.delete(f"/api/events/categories/{category_id}")
        if del_cat_resp.status_code != 200:
            print(f"DELETE /api/events/categories/{category_id} status: {del_cat_resp.status_code}")
            print(f"Response content: {del_cat_resp.content}")


    @task
    def get_events(self):
        response = self.client.get("/api/events")
        if response.status_code != 200:
            print(f"GET /api/events status: {response.status_code}")
            print(f"Response content: {response.content}")

    @task
    def post_events_search(self):
        payload = {"query": fake.random.alpha()}
        response = self.client.post("/api/events/search", json=payload)
        if response.status_code != 200:
            print(f"POST /api/events/search status: {response.status_code}")
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

