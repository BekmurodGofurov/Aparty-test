from app.schemas import PublicProfile
from tests.conftest import GUEST_ID, OWNER_ID, auth_headers

BASE = "/api/v1/bookings"


async def test_incoming_bookings_include_requester_and_listing_title(client, create_booking, iam_profiles):
    iam_profiles[GUEST_ID] = PublicProfile(id=GUEST_ID, full_name="Malika Karimova", phone="+998901112233", is_verified=True)
    await create_booking()
    incoming = (await client.get(f"{BASE}/incoming", headers=auth_headers(OWNER_ID))).json()[0]
    assert incoming["listing_title"] == "Test flat"
    assert incoming["requester"] == {
        "id": GUEST_ID, "full_name": "Malika Karimova", "phone": "+998901112233", "is_verified": True,
    }


async def test_a_single_booking_includes_the_requester(client, create_booking, iam_profiles):
    iam_profiles[GUEST_ID] = PublicProfile(id=GUEST_ID, full_name="Malika Karimova")
    booking = await create_booking()
    body = (await client.get(f"{BASE}/{booking['id']}", headers=auth_headers(OWNER_ID))).json()
    assert body["requester"]["full_name"] == "Malika Karimova"


async def test_bookings_work_when_iam_has_no_profile(client, create_booking):
    await create_booking()
    incoming = (await client.get(f"{BASE}/incoming", headers=auth_headers(OWNER_ID))).json()[0]
    assert incoming["requester"] is None
    assert incoming["status"] == "pending"


async def test_own_bookings_carry_the_listing_title(client, create_booking):
    await create_booking()
    mine = (await client.get(BASE, headers=auth_headers(GUEST_ID))).json()[0]
    assert mine["listing_title"] == "Test flat"
