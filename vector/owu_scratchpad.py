import os
import requests
from datetime import datetime
from typing import Any, Dict, Awaitable
import asyncio


class Tools:
    """
    Collection of helper methods for remote requests and patient diagnosis.
    """

    PATIENT_NOT_FOUND = "The patient was not found in register"
    PATIENT_FOUND = "Located {pid}, continuing"

    async def condition_search(
        self,
        condition_description: str,
        __event_emitter__: None,
    ) -> str:
        """
        Provide a list of patients based on a description of their symptoms or medical condition
        """

        condition_service_url = os.environ.get(
            "CONDITION_SERVCIE_URL", "http://vector:8080/condition_search"
        )

        payload = {"query": condition_description, "result_set_size": 3}

        relevant_patients = await self._issue_post_request(
            condition_service_url, payload, __event_emitter__
        )

        header = "|First Name|Family Name|Subject Id|"
        divider = "|---|---|---|"
        rows = [
            f"|{p['first_name']}|{p['family_name']}|{p['subject_id']}|"
            for p in relevant_patients
        ]

        table_md = "\n".join([header, divider, *rows, divider])

        # Emit a single message containing the whole table

        if __event_emitter__:
            await __event_emitter__(
                {"type": "message", "data": {"description": table_md}}
            )

        return table_md

    async def todays_patient_list(self, __event_emitter__: None) -> str:
        """
        Provide a list of all patients current on the patient register
        """
        patient_service_url = "http://host.docker.internal:8080/patients"
        all_patients = await self._issue_get_request(
            patient_service_url, __event_emitter__
        )

        header = "|First Name|Family Name|Subject Id|"
        divider = "|---|---|---|"
        rows = [
            f"|{p['first_name']}|{p['family_name']}|{p['subject_id']}|"
            for p in all_patients
        ]

        table_md = "\n".join([header, divider, *rows, divider])

        # Emit a single message containing the whole table

        if __event_emitter__:
            await __event_emitter__(
                {"type": "message", "data": {"description": table_md}}
            )

        return table_md

    async def diagnose_patient(
        self, first_name: str, last_name: str, multimodal: bool, __event_emitter__: None
    ) -> str:
        """
        Provide a patient diagnosis from the external SUBJECT_SERVICE.
        """
        diagnosis_service_url = os.environ.get(
            "DIAGNOSIS_SERVICE_URL", "http://host.docker.internal:8080/diagnose"
        )

        payload = {
            "first_name": first_name,
            "last_name": last_name,
            "multi_modal": multimodal,
        }
        diagnosis_search = []
        try:
            diagnosis_search = await self._issue_post_request(
                diagnosis_service_url, payload=payload
            )
            if not diagnosis_search["subject_id"]:
                raise Exception("retrying...")

        except:
            diagnosis_search = await self._issue_post_request(
                diagnosis_service_url, payload=payload
            )
            if not diagnosis_search["subject_id"]:
                return "Diagnosis service appears offline"

        if __event_emitter__:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {
                        "description": (
                            f"Searching for {first_name} {last_name}. Multimodal = {multimodal}. Diagnosis in progress…"
                        ),
                        "done": True,
                    },
                }
            )

        subject_id = diagnosis_search["subject_id"]
        img_url = f"http://localhost:8080/xray_image/{subject_id}"
        html = f"""<!DOCTYPE html>
        <html><body style="margin:0">
            <img src="{img_url}" style="max-width:100%;height:auto">
        </body></html>
        """

        diagnosis_search["jpg"] = img_url
        diagnosis_search["xray_img_html"] = html

        return diagnosis_search

    async def _issue_post_request(
        self,
        url: str,
        payload: Dict[str, Any],
        __event_emitter__: Awaitable[str] = None,
    ) -> Dict[str, Any]:
        if __event_emitter__:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {"description": f"post request to {url}", "done": True},
                }
            )

        response = requests.post(url, json=payload, timeout=60)
        response.raise_for_status()
        return response.json()

    async def _issue_get_request(self, url: str, __event_emitter__) -> Dict[str, Any]:

        response = requests.get(url, timeout=60)
        if __event_emitter__:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {"description": f"get request to {url}", "done": True},
                }
            )
        response.raise_for_status()
        return response.json()


if __name__ == "__main__":

    tools = Tools()

    result = asyncio.run(tools.list_all_patients(__event_emitter__=evt_em))

    result = asyncio.run(
        tools.diagnose_patient(
            first_name="Aarav",
            last_name="Sharma",
            multimodal=True,
            __event_emitter__=evt_em,
        )
    )

    result_not_found = asyncio.run(
        tools.diagnose_patient(
            first_name="Jack",
            last_name="Munrow",
            multimodal=True,
            __event_emitter__=evt_em,
        )
    )

    asyncio.run(evt_em(result))
