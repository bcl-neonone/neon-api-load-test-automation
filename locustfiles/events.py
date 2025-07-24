from faker import Faker
from locust import HttpLocust, HttpUser, TaskSet, task, events, between
import random
from uuid import uuid4
from datetime import datetime, timedelta

fake = Faker()

def report_failure(request_type, name, response, exception=None):
    events.request_failure.fire(
        request_type=request_type,
        name=name,
        response_time=getattr(response, "elapsed", None) and response.elapsed.total_seconds() * 1000 or 0,
        response_length=len(getattr(response, "content", b"")),
        exception=exception or Exception(f"Status: {getattr(response, 'status_code', 'N/A')}, Content: {getattr(response, 'content', '')}")
    )

def generate_event_payload():
    now = datetime.now()
    start_dt = now + timedelta(days=random.randint(1, 30))
    end_dt = start_dt + timedelta(days=random.randint(1, 5))
    return {
        "id": str(uuid4()),
        "name": fake.catch_phrase(),
        "summary": fake.sentence(),
        "code": fake.bothify(text="EVT-####"),
        "maximumAttendees": random.randint(10, 500),
        # assigning a category that doesn't exist may cause an error
        "category": {
            "id": str(uuid4()),
            "name": fake.word(),
            "status": "ACTIVE"
        },
        # assigning a campaign that doesn't exist may cause an error
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
            "startDate": start_dt.isoformat(),
            "endDate": end_dt.isoformat(),
            "startTime": fake.time(),
            "endTime": fake.time(),
            "registrationOpenDate": start_dt.isoformat(),
            "registrationCloseDate": end_dt.isoformat(),
            "timeZone": {
                "id": 2,
                # "name": fake.timezone(),
                "name": "GMT Central",
                "status": "ACTIVE"
            }
        },
        "financialSettings": {
            "feeType": "Free",
            "admissionFee": {
                "fee": round(random.uniform(0, 100), 2),
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
                "id": 1,
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
        "id": random.randint(1, 10000000),
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
            report_failure("POST", "/api/events", create_resp)
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
            report_failure("GET", f"/api/events/{event_id}", get_resp)

        reg_resp = self.client.get(f"/api/events/{event_id}/eventRegistrations")
        if reg_resp.status_code != 200:
            report_failure("GET", f"/api/events/{event_id}/eventRegistrations", reg_resp)

        att_resp = self.client.get(f"/api/events/{event_id}/attendees")
        if att_resp.status_code != 200:
            report_failure("GET", f"/api/events/{event_id}/attendees", att_resp)

        put_payload = generate_event_payload()
        put_resp = self.client.put(f"/api/events/{event_id}", json=put_payload)
        if put_resp.status_code != 200:
            report_failure("PUT", f"/api/events/{event_id}", put_resp)

        patch_payload = generate_event_payload()
        patch_resp = self.client.patch(f"/api/events/{event_id}", json=patch_payload)
        if patch_resp.status_code != 200:
            report_failure("PATCH", f"/api/events/{event_id}", patch_resp)

        del_resp = self.client.delete(f"/api/events/{event_id}")
        if del_resp.status_code != 200:
            report_failure("DELETE", f"/api/events/{event_id}", del_resp)

    @task
    def tickets_create_update_delete(self):
        event_payload = generate_event_payload()
        create_event_resp = self.client.post("/api/events", json=event_payload)
        if create_event_resp.status_code != 201:
            report_failure("POST", "/api/events", create_event_resp)
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

        get_tickets_resp = self.client.get(f"/api/events/{event_id}/tickets")
        if get_tickets_resp.status_code != 200:
            report_failure("GET", f"/api/events/{event_id}/tickets", get_tickets_resp)

        ticket_payload = generate_ticket_payload()
        post_ticket_resp = self.client.post(f"/api/events/{event_id}/tickets", json=ticket_payload)
        if post_ticket_resp.status_code not in (200, 201):
            report_failure("POST", f"/api/events/{event_id}/tickets", post_ticket_resp)
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

        get_ticket_resp = self.client.get(f"/api/events/{event_id}/tickets/{ticket_id}")
        if get_ticket_resp.status_code != 200:
            report_failure("GET", f"/api/events/{event_id}/tickets/{ticket_id}", get_ticket_resp)

        put_ticket_payload = generate_ticket_payload()
        put_ticket_resp = self.client.put(f"/api/events/{event_id}/tickets/{ticket_id}", json=put_ticket_payload)
        if put_ticket_resp.status_code != 200:
            report_failure("PUT", f"/api/events/{event_id}/tickets/{ticket_id}", put_ticket_resp)

        patch_ticket_payload = {"name": "Patched Ticket"}
        patch_ticket_resp = self.client.patch(f"/api/events/{event_id}/tickets/{ticket_id}", json=patch_ticket_payload)
        if patch_ticket_resp.status_code != 200:
            report_failure("PATCH", f"/api/events/{event_id}/tickets/{ticket_id}", patch_ticket_resp)

        del_ticket_resp = self.client.delete(f"/api/events/{event_id}/tickets/{ticket_id}")
        if del_ticket_resp.status_code != 200:
            report_failure("DELETE", f"/api/events/{event_id}/tickets/{ticket_id}", del_ticket_resp)

        del_event_resp = self.client.delete(f"/api/events/{event_id}")
        if del_event_resp.status_code != 200:
            report_failure("DELETE", f"/api/events/{event_id}", del_event_resp)

    @task
    def category_create_update_delete(self):
        cat_payload = {"name": fake.word().capitalize() + " Category"}
        post_cat_resp = self.client.post("/api/events/categories", json=cat_payload)
        if post_cat_resp.status_code not in (200, 201):
            report_failure("POST", "/api/events/categories", post_cat_resp)
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

        get_cat_resp = self.client.get("/api/events/categories")
        if get_cat_resp.status_code != 200:
            report_failure("GET", "/api/events/categories", get_cat_resp)

        put_cat_payload = {"name": "Updated Category"}
        put_cat_resp = self.client.put(f"/api/events/categories/{category_id}", json=put_cat_payload)
        if put_cat_resp.status_code != 200:
            report_failure("PUT", f"/api/events/categories/{category_id}", put_cat_resp)

        patch_cat_payload = {"description": "Patched Category"}
        patch_cat_resp = self.client.patch(f"/api/events/categories/{category_id}", json=patch_cat_payload)
        if patch_cat_resp.status_code != 200:
            report_failure("PATCH", f"/api/events/categories/{category_id}", patch_cat_resp)

        del_cat_resp = self.client.delete(f"/api/events/categories/{category_id}")
        if del_cat_resp.status_code != 200:
            report_failure("DELETE", f"/api/events/categories/{category_id}", del_cat_resp)


    @task
    def get_events(self):
        response = self.client.get("/api/events")
        if response.status_code != 200:
            report_failure("GET", "/api/events", response)

    @task
    def post_events_search(self):
        payload = {"query": fake.random.alpha()}
        response = self.client.post("/api/events/search", json=payload)
        if response.status_code != 200:
            report_failure("POST", "/api/events/search", response)

    @task
    def get_search_fields(self):
        response = self.client.get("/api/events/search/searchFields")
        if response.status_code != 200:
            report_failure("GET", "/api/events/search/searchFields", response)

    @task
    def get_output_fields(self):
        response = self.client.get("/api/events/search/outputFields")
        if response.status_code != 200:
            report_failure("GET", "/api/events/search/outputFields", response)

