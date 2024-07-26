import datetime as dt
from functools import wraps
import json
import http.client
import base64
import os
from urllib.parse import quote
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()


def create_auth():
    """
    Create an authorization string for basic authentication using the Windchill username and password.

    Returns:
    - The base64 encoded authorization string.
    """
    auth_string = f"{os.getenv('USERNAME_WINDCHILL')}:{os.getenv('PASSWORD_WINDCHILL')}"
    auth_string_bytes = auth_string.encode("ascii")
    base64_bytes = base64.b64encode(auth_string_bytes)
    base64_string = base64_bytes.decode("ascii")
    return f"Basic {base64_string}"


# Initialize global variables
NONCE = None
CONN = http.client.HTTPSConnection(os.getenv("Adress_Windchill"))
AUTH = create_auth()


def log_request(func):
    """
    Decorator to log the time taken by a function to execute.

    Parameters:
    - func: The function to be decorated.

    Returns:
    - The wrapped function.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        tic = dt.datetime.now()
        try:
            result = func(*args, **kwargs)
        except Exception as e:
            result = f"Error: {str(e)}"
        time_taken = str(dt.datetime.now() - tic)
        print(f"just ran step {func.__name__} took {time_taken}s")
        return result

    return wrapper


@log_request
def read_from_windchill_per_node(nodename: str, skiptoken=0) -> str:
    """
    Read data from Windchill for a specific classification node.

    Parameters:
    - nodename: The name of the node to read from.
    - skiptoken: Token for pagination (default is 0).

    Returns:
    - The response data as a string.
    """
    payload = ""
    headers = {"Authorization": f"{AUTH}"}
    CONN.request(
        "GET",
        f"/Windchill/servlet/odata/ClfStructure/ClfNodes('{nodename}')/ClassifiedObjects?$skiptoken={skiptoken}",
        payload,
        headers,
    )
    res = CONN.getresponse()
    data = res.read().decode("utf8")
    res.close()
    return data


@log_request
def read_from_windchill_last_modified(last_modified: str, skiptoken=0) -> str:
    """
    Read data from Windchill for parts modified after a specific date.

    Parameters:
    - last_modified: The date to filter parts modified after.
    - skiptoken: Token for pagination (default is 0).

    Returns:
    - The response data as a string.
    """
    payload = ""
    headers = {"Authorization": f"{AUTH}"}
    CONN.request(
        "GET",
        f"/Windchill/servlet/odata/ProdMgmt/Parts?$filter=LastModified%20gt%20{last_modified}&$skiptoken={skiptoken}",
        payload,
        headers,
    )
    res = CONN.getresponse()
    data = res.read().decode("utf8")
    res.close()
    return data


@log_request
def read_from_windchill_per_name(name: str) -> str:
    """
    Read data from Windchill for parts with a specific name.

    Parameters:
    - name: The name of the parts to read.

    Returns:
    - The response data as a string.
    """
    payload = ""
    headers = {"Authorization": f"{AUTH}"}
    CONN.request(
        "GET",
        f"/Windchill/servlet/odata/ProdMgmt/Parts?$filter=Name%20eq%20'{name}'",
        payload,
        headers,
    )
    res = CONN.getresponse()
    data = res.read().decode("utf8")
    res.close()
    return data


@log_request
def read_from_windchill_per_sapnr(sap_matnr: str) -> str:
    """
    Read data from Windchill for parts with a specific SAP material number.

    Parameters:
    - sap_matnr: The SAP material number of the parts to read.

    Returns:
    - The response data as a string.
    """
    payload = ""
    headers = {"Authorization": f"{AUTH}"}
    CONN.request(
        "GET",
        f"/Windchill/servlet/odata/ProdMgmt/Parts?$filter=SAPMATNR%20eq%20'{quote(sap_matnr)}'",
        payload,
        headers,
    )
    res = CONN.getresponse()
    data = res.read().decode("utf8")
    res.close()
    return data


@log_request
def read_nonce_from_windchill() -> str:
    """
    Read a CSRF token (nonce) from Windchill.

    Returns:
    - The nonce value as a string.
    """
    payload = ""
    headers = {"Authorization": f"{AUTH}"}
    CONN.request("GET", "/Windchill/servlet/odata/PTC/GetCSRFToken()", payload, headers)
    res = CONN.getresponse()
    data = json.loads(res.read().decode("utf8"))["NonceValue"]
    res.close()
    return data


@log_request
def read_use_from_windchill_per_oid(oid: str) -> str:
    """
    Read data from Windchill for a part with a specific OID.

    Parameters:
    - oid: The OID of the part to read.

    Returns:
    - The response data as a string.
    """
    global NONCE
    if not NONCE:
        NONCE = read_nonce_from_windchill()
    payload = "{}"
    headers = {
        "Content-Type": "application/json",
        "CSRF_NONCE": f"{NONCE}",
        "Accept": "application/json;odata.metadata=full",
        "Authorization": f"{AUTH}",
    }
    CONN.request(
        "POST",
        f"/Windchill/servlet/odata/ProdMgmt/Parts('{oid}')/PTC.ProdMgmt.GetPartsList?$expand=Part",
        payload,
        headers,
    )
    res = CONN.getresponse()
    data = res.read().decode("utf8")
    res.close()
    return data
