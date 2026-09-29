from clinical_trials_pipeline.api import fetch_studies


def make_study(nct_id):
    return {"protocolSection": {"identificationModule": {"nctId": nct_id}}}


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


class FakeSession:
    def __init__(self, responses):
        self.headers = {}
        self.responses = list(responses)
        self.calls = []

    def get(self, url, *, params, timeout):
        self.calls.append((url, dict(params), timeout))
        return FakeResponse(self.responses.pop(0))


def test_fetch_studies_follows_cursor_and_deduplicates_ids():
    session = FakeSession(
        [
            {"totalCount": 3, "studies": [make_study("NCT00000001"), make_study("NCT00000002")], "nextPageToken": "next"},
            {"totalCount": 3, "studies": [make_study("NCT00000002"), make_study("NCT00000003")]},
        ]
    )

    batch = fetch_studies(page_size=2, max_studies=0, session=session)

    assert [s["protocolSection"]["identificationModule"]["nctId"] for s in batch.studies] == [
        "NCT00000001",
        "NCT00000002",
        "NCT00000003",
    ]
    assert batch.api_total_count == 3
    assert batch.page_count == 2
    assert session.calls[1][1]["pageToken"] == "next"


def test_fetch_studies_stops_at_requested_limit():
    session = FakeSession(
        [{"totalCount": 5, "studies": [make_study("NCT00000001"), make_study("NCT00000002")], "nextPageToken": "next"}]
    )

    batch = fetch_studies(page_size=2, max_studies=1, session=session)

    assert len(batch.studies) == 1
    assert batch.page_count == 1


def test_fetch_rejects_invalid_page_size():
    try:
        fetch_studies(page_size=1001, session=FakeSession([]))
    except ValueError as error:
        assert "page_size" in str(error)
    else:
        raise AssertionError("Invalid page size should be rejected")
