import logging
import sys
import json
import httpx
import xmltodict
from typing import Any
from mcp.server import FastMCP

logging.basicConfig(
    level=logging.INFO,
    stream=sys.stderr,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("wikimed-mcp-server")

mcp = FastMCP("WikiMed MCP Server")

client_configs = {}


def get_client_config(client_id: str = "") -> dict:
    """Get client configuration by ID"""
    if not client_id or client_id not in client_configs:
        return {"base_url": "http://edrak1.selfip.com:64384", "hcode": "13745064"}
    return client_configs[client_id]


def convert_xml_to_json(xml_data: str) -> str:
    """Convert XML response to JSON string"""
    try:
        data_dict = xmltodict.parse(xml_data)
        return json.dumps(data_dict, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"XML to JSON conversion failed: {e}")
        return json.dumps({"error": "Failed to parse XML response", "raw": xml_data})


async def make_wikimed_request(params: dict, client_id: str = "") -> str:
    """Make HTTP request to WikiMed API"""
    config = get_client_config(client_id)
    url = config["base_url"]

    if "HCode" not in params and "hcode" in config:
        params["HCode"] = config["hcode"]

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()

            content_type = response.headers.get("content-type", "")
            if "xml" in content_type.lower() or response.text.strip().startswith("<"):
                return convert_xml_to_json(response.text)
            return response.text
    except httpx.HTTPError as e:
        logger.error(f"HTTP request failed: {e}")
        return json.dumps({"error": f"Request failed: {str(e)}"})
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return json.dumps({"error": f"Unexpected error: {str(e)}"})


@mcp.tool()
async def configure_client(client_id: str, base_url: str, hcode: str) -> str:
    """Configure a new client with their WikiMed credentials"""
    if not client_id:
        return json.dumps({"error": "client_id is required"})
    if not base_url:
        return json.dumps({"error": "base_url is required"})
    if not hcode:
        return json.dumps({"error": "hcode is required"})

    client_configs[client_id] = {"base_url": base_url, "hcode": hcode}
    logger.info(f"Configured client: {client_id}")
    return json.dumps(
        {
            "success": True,
            "message": f"Client {client_id} configured successfully",
            "base_url": base_url,
        }
    )


@mcp.tool()
async def get_wikimed_info(client_id: str = "") -> str:
    """Get Wikimed system information"""
    params = {"MType": "100"}
    return await make_wikimed_request(params, client_id)


@mcp.tool()
async def list_doctors(client_id: str = "") -> str:
    """Get list of all doctors"""
    params = {"MType": "500"}
    return await make_wikimed_request(params, client_id)


@mcp.tool()
async def find_doctor_by_name(doctor_name: str, client_id: str = "") -> str:
    """Search for a doctor by name using fuzzy matching"""
    if not doctor_name:
        return json.dumps({"error": "doctor_name is required"})
    params = {"MType": "600", "DoctorName": doctor_name}
    return await make_wikimed_request(params, client_id)


@mcp.tool()
async def find_doctor_by_code(doctor_code: str, client_id: str = "") -> str:
    """Search for a doctor by their code"""
    if not doctor_code:
        return json.dumps({"error": "doctor_code is required"})
    params = {"MType": "600", "DoctorCode": doctor_code}
    return await make_wikimed_request(params, client_id)


@mcp.tool()
async def create_appointment(
    doctor_code: str,
    patient_phone: str,
    appointment_date: str,
    appointment_time: str,
    patient_name: str = "",
    social_id: str = "",
    branch_id: str = "1",
    client_id: str = "",
) -> str:
    """Create a new appointment"""
    if not doctor_code:
        return json.dumps({"error": "doctor_code is required"})
    if not patient_phone:
        return json.dumps({"error": "patient_phone is required"})
    if not appointment_date:
        return json.dumps({"error": "appointment_date is required"})
    if not appointment_time:
        return json.dumps({"error": "appointment_time is required"})

    params = {
        "MType": "700",
        "DoctorCode": doctor_code,
        "PatientPhone": patient_phone,
        "AppointmentDate": appointment_date,
        "AppointmentTime": appointment_time,
        "IDBranch": branch_id,
    }

    if patient_name:
        params["PatientName"] = patient_name
    if social_id:
        params["SocialID"] = social_id

    return await make_wikimed_request(params, client_id)


@mcp.tool()
async def find_nearest_slot(
    doctor_code: str, preferred_date: str = "", client_id: str = ""
) -> str:
    """Find the nearest available appointment slot for a doctor"""
    if not doctor_code:
        return json.dumps({"error": "doctor_code is required"})

    params = {"MType": "800", "DoctorCode": doctor_code}
    if preferred_date:
        params["PreferredDate"] = preferred_date

    return await make_wikimed_request(params, client_id)


@mcp.tool()
async def confirm_appointment(
    appointment_number: str, action: str = "confirm", client_id: str = ""
) -> str:
    """Confirm, cancel, or update an appointment"""
    if not appointment_number:
        return json.dumps({"error": "appointment_number is required"})
    if action not in ["confirm", "cancel", "update"]:
        return json.dumps({"error": "action must be confirm, cancel, or update"})

    params = {"MType": "900", "AppointmentNumber": appointment_number, "Action": action}
    return await make_wikimed_request(params, client_id)


@mcp.tool()
async def get_appointment(appointment_number: str, client_id: str = "") -> str:
    """Retrieve details of a saved appointment"""
    if not appointment_number:
        return json.dumps({"error": "appointment_number is required"})

    params = {"MType": "910", "AppointmentNumber": appointment_number}
    return await make_wikimed_request(params, client_id)


@mcp.tool()
async def list_appointments(
    date: str, doctor_code: str = "", branch_id: str = "", client_id: str = ""
) -> str:
    """Get all appointments for a specific date"""
    if not date:
        return json.dumps({"error": "date is required in format DD/MM/YYYY"})

    params = {"MType": "1000", "Date": date}
    if doctor_code:
        params["DoctorCode"] = doctor_code
    if branch_id:
        params["IDBranch"] = branch_id

    return await make_wikimed_request(params, client_id)


@mcp.tool()
async def get_patient_invoice(
    patient_file_no: str = "",
    patient_phone: str = "",
    social_id: str = "",
    client_id: str = "",
) -> str:
    """Get patient invoice summary"""
    if not patient_file_no and not patient_phone and not social_id:
        return json.dumps(
            {
                "error": "At least one identifier required: patient_file_no, patient_phone, or social_id"
            }
        )

    params = {"MType": "1200"}
    if patient_file_no:
        params["FileNo"] = patient_file_no
    if patient_phone:
        params["Phone"] = patient_phone
    if social_id:
        params["SocialID"] = social_id

    return await make_wikimed_request(params, client_id)


@mcp.tool()
async def get_daily_income(date: str, client_id: str = "") -> str:
    """Get daily income summary"""
    if not date:
        return json.dumps({"error": "date is required in format DD/MM/YYYY"})

    params = {"MType": "1200", "Date": date, "ReportType": "DailyIncome"}
    return await make_wikimed_request(params, client_id)


@mcp.tool()
async def restart_service(client_id: str = "") -> str:
    """Restart the WikiMed service"""
    params = {"MType": "1300"}
    return await make_wikimed_request(params, client_id)


@mcp.tool()
async def search_patient(
    file_no: str = "", phone: str = "", social_id: str = "", client_id: str = ""
) -> str:
    """Search for a patient by file number, phone, or social ID"""
    if not file_no and not phone and not social_id:
        return json.dumps(
            {"error": "At least one identifier required: file_no, phone, or social_id"}
        )

    params = {"MType": "1100"}
    if file_no:
        params["FileNo"] = file_no
    if phone:
        params["Phone"] = phone
    if social_id:
        params["SocialID"] = social_id

    return await make_wikimed_request(params, client_id)
