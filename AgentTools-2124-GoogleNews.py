import requests
import time
import json
import os
import random
import sys
import getpass
try:
    import fcntl
except ImportError:
    fcntl = None


# This file is generated for one fixed AgentTools template. Template discovery
# happens before generation and is deliberately absent from this runtime file.
#
# Template: Google News Scraper (Cloud)
#   - id            : 2124
#   - slug / name   : google-news-scraper-cloud
#   - url           : https://www.octoparse.com/template/google-news-scraper-cloud
#   - runOn         : CLOUD   (templateType PYTHON, dataSupplyMode REAL_TIME)
#   - min account   : FREE
#   - pricing       : PAY_PER_LINE, $0.0001/line  ($0.1 / 1,000 lines)
#
# Integration flow (identical to every AgentTools template):
#   1. POST {BASE_URL}/api/agentTools/executeTask   -> returns a taskId (one paid cloud task)
#   2. GET  {BASE_URL}/api/agentTools/exportData     -> poll until status == "exported", then download
#
# Auth headers:
#   x-api-key         : your Octoparse OpenAPI key
#   x-external-user-id: a stable caller-owned ID (executeTask only)
BASE_URL = 'https://openapi.octoparse.com'
TEMPLATE_NAME = 'google-news-scraper-cloud'
TASK_NAME = 'Google News - "Vote" last 24h (US)'

# Complete exact-lookup snapshots taken from the template's v3 structured data.
# SOURCE_TREE is [] because this template has no external source options.
#
# NOTE on parameter keys: the request MUST use the live inputSchema.field keys, not the
# x-octoparse.paramName from the offline v3 data pack. Verified against a real executeTask
# call on 2026-08-06 (the pack's "MainKeys"/"Language" were rejected as unmapped):
#   - google_News_Search_URLs -> required, MultiInput string[] (the pack's stale paramName was "MainKeys")
#   - language                -> optional, Input string        (the pack's stale paramName was "Language")
INPUT_SCHEMA = [{'field': 'google_News_Search_URLs',
  'label': 'Google News Search URLs (up to 10,000)',
  'type': 'string',
  'required': True,
  'uiType': 'MultiInput',
  'minLen': 1,
  'maxLen': 1000,
  'valueFormat': 'string[]',
  'example': ['https://news.google.com/search?q=%22Vote%22&hl=en-US&gl=US&ceid=US%3Aen'],
  'fieldId': '5c1ed9e2-d4d4-eef7-20d0-7d3108a18bf6',
  'sourceBacked': None,
  'dependsOn': None},
 {'field': 'language',
  'label': 'Language',
  'type': 'string',
  'required': False,
  'uiType': 'Input',
  'minLen': 1,
  'maxLen': 50,
  'valueFormat': None,
  'example': 'en',
  'fieldId': 'e6ae9e2c-ffe1-4fbe-5735-0fba54a7ffb3',
  'sourceBacked': None,
  'dependsOn': None}]
SOURCE_TREE = []
SOURCE_SUMMARY = {'hasSourceOptions': False,
 'hasDependentSourceOptions': False,
 'sourceFieldCount': 0,
 'rootSourceFieldCount': 0,
 'dependentSourceFieldCount': 0,
 'rootOptionCount': 0,
 'sourceFields': []}

# Verified request values. parameters is serialized exactly once in execute_task.
# Each entry is a Google News search URL. Build one from any news.google.com/search
# query and URL-encode it, e.g. add "when:1d" to limit to the last day.
TASK_PARAMETERS = {'google_News_Search_URLs': [
    'https://news.google.com/search?q=%22Vote%22%20when%3A1d&hl=en-US&gl=US&ceid=US%3Aen'
], 'language': 'en'}
PARAMETER_DESCRIPTIONS = {
 'templateName': 'Fixed verified template slug: google-news-scraper-cloud (template id 2124).',
 'taskName': 'Optional human-readable task name.',
 'parameters': 'Serialized JSON string containing the fixed template parameters.',
 'x-external-user-id': 'Required stable caller-owned ID sent as a request header.',
 'google_News_Search_URLs': 'Required MultiInput string array of Google News search URLs; '
             '1-10000 entries, each 1-1000 chars. Live inputSchema.field key (the v3 pack '
             'paramName "MainKeys" is stale and gets rejected as unmapped).',
 'language': 'Optional Input string (1-50 chars). Hint language to improve accuracy; verified '
             'as "en". Omit the key entirely to leave it unset.'}

EXPORT_FILE_TYPE = 'JSON'
PREVIEW_ROWS = 5
MAX_POLL_SECONDS = 900
MAX_POLL_ATTEMPTS = 30
MAX_EXPORT_BYTES = 100 * 1024 * 1024

# ILLUSTRATIVE response shapes (NOT a captured run of this template). They show the
# envelope every AgentTools task returns, so you know what to poll for.
#   executeTask (accepted):
#     {"data": {"success": true, "status": "accepted",
#               "templateId": 2124, "templateName": "google-news-scraper-cloud",
#               "taskId": "<uuid>", "lotNo": "<digits>",
#               "retryGuidance": {"tool": "export_data", "waitSecondsMin": 60, "waitSecondsMax": 60}}}
#   exportData status progression:  collecting -> exporting -> exported
#   exported payload carries: exportFileUrl (https) OR sampleData, dataTotal, sampleRowCount.
#
# Output (VERIFIED via a real run on 2026-08-06): a JSON array of rows, each shaped as
#   {"keyword": "<the search URL you sent>", "FollowField": "<JSON string>"}
# Parse FollowField (it is a JSON string) to get the article fields:
#   Keyword, Source, Title, ProjectUrl (article link), PublishDate, Author, Language
# Note: this Cloud template returns metadata only — NO article body (despite the template
# page copy). To collect the full body (a NewsText field), use the free companion templates:
#   - google-news-scraper        (by keyword, template id 1370)
#   - google-news-scraper-by-URL (by URL,     template id 1747)
# In a cloud pipeline this Cloud template hands its result links to that article-extraction step.


def prompt_secret(prompt_text):
    """Prompt for an API Key without echoing it when the console supports TTY."""
    if not sys.stdin.isatty():
        raise RuntimeError(
            "Cannot safely prompt for API Key without a TTY; set OCTOPARSE_API_KEY."
        )
    return getpass.getpass(prompt_text)


def print_parameter_reference():
    """Print the fixed template parameters and their source."""
    print("\nexecuteTask parameters:")
    for name, description in PARAMETER_DESCRIPTIONS.items():
        print(f"  - {name}: {description}")
    print(f"Debug - task parameters: {json.dumps(TASK_PARAMETERS, ensure_ascii=False)}")
    print(
        "Debug - exportData parameters: "
        + json.dumps(
            {"exportFileType": EXPORT_FILE_TYPE, "previewRows": PREVIEW_ROWS},
            ensure_ascii=False,
        )
    )


def _is_empty(value):
    return value is None or value == "" or value == []


def _is_array_field(field_definition):
    ui_type = str(field_definition.get("uiType") or "").lower()
    value_format = str(field_definition.get("valueFormat") or "").lower()
    field_type = str(field_definition.get("type") or "").lower()
    return (
        field_type == "array"
        or "[]" in value_format
        or ui_type in {"checkboxlist", "multiinput", "multiselect", "checklist"}
    )


def _collect_available_source_options(nodes, parameters, result=None):
    """Collect valid keys, following only the selected parent source branches."""
    if result is None:
        result = {}
    for node in nodes if isinstance(nodes, list) else []:
        if not isinstance(node, dict):
            continue
        field = node.get("field")
        options = node.get("options") if isinstance(node.get("options"), list) else []
        if field:
            result.setdefault(field, set()).update(
                str(option.get("key"))
                for option in options
                if isinstance(option, dict) and option.get("key") not in (None, "")
            )

        selected_value = parameters.get(field) if field else None
        selected_values = selected_value if isinstance(selected_value, list) else [selected_value]
        selected_keys = {str(value) for value in selected_values if value not in (None, "")}
        for option in options:
            if not isinstance(option, dict):
                continue
            option_key = str(option.get("key"))
            if not field or option_key in selected_keys:
                _collect_available_source_options(option.get("children"), parameters, result)
    return result


def _zero_option_source_fields():
    source_fields = SOURCE_SUMMARY.get("sourceFields")
    if not isinstance(source_fields, list):
        return set()
    return {
        item.get("field")
        for item in source_fields
        if isinstance(item, dict)
        and item.get("field")
        and item.get("rootOptionCount") == 0
    }


def validate_task_parameters():
    """Validate the fixed request against the embedded schema and full sourceTree."""
    schema_by_field = {
        item.get("field"): item
        for item in INPUT_SCHEMA
        if isinstance(item, dict) and item.get("field")
    }
    unknown_fields = sorted(set(TASK_PARAMETERS) - set(schema_by_field))
    if unknown_fields:
        raise Exception(f"Unknown task parameter fields: {unknown_fields}")

    for field, definition in schema_by_field.items():
        value = TASK_PARAMETERS.get(field)
        if definition.get("required") and _is_empty(value):
            raise Exception(f"Required task parameter '{field}' is empty.")
        if field in TASK_PARAMETERS and _is_array_field(definition) and not isinstance(value, list):
            raise Exception(f"Task parameter '{field}' must be an array.")

    if SOURCE_TREE:
        available_options = _collect_available_source_options(SOURCE_TREE, TASK_PARAMETERS)
        zero_option_fields = _zero_option_source_fields()
        for field, definition in schema_by_field.items():
            if not definition.get("sourceBacked") or field not in TASK_PARAMETERS:
                continue
            allowed_options = available_options.get(field, set())
            if not allowed_options:
                if field in zero_option_fields:
                    continue
                raise Exception(
                    f"No source options are available for configured field '{field}'."
                )
            values = TASK_PARAMETERS[field]
            selected_values = values if isinstance(values, list) else [values]
            invalid = [
                value
                for value in selected_values
                if str(value) not in allowed_options
            ]
            if invalid:
                raise Exception(
                    f"Task parameter '{field}' contains invalid source option keys: {invalid}"
                )


def execute_task(api_key, external_user_id):
    """Step 1: create and start one real cloud task. This call is never retried."""
    validate_task_parameters()
    print(f"Starting task from template '{TEMPLATE_NAME}'...")
    url = f"{BASE_URL}/api/agentTools/executeTask"
    headers = {
        "x-api-key": api_key,
        "x-external-user-id": external_user_id,
        "Content-Type": "application/json",
    }
    payload = {
        "templateName": TEMPLATE_NAME,
        "parameters": json.dumps(TASK_PARAMETERS, ensure_ascii=False),
    }
    if TASK_NAME:
        payload["taskName"] = TASK_NAME

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        print(f"Response received, status code: {response.status_code}")
        if response.status_code != 200:
            print(f"Warning: executeTask returned an error: {response.text}")
        response.raise_for_status()
        result = response.json()
        print(f"Debug - executeTask raw response: {json.dumps(result, ensure_ascii=False)}")

        data = result.get("data") if isinstance(result.get("data"), dict) else {}
        task_id = data.get("taskId")
        lot_no = data.get("lotNo")
        if data.get("status") == "accepted" and task_id:
            print(f"Task accepted, task ID: {task_id}, lot number: {lot_no}")
            return task_id, lot_no
        raise Exception(f"Task launch was not accepted: {result}")
    except requests.exceptions.Timeout as error:
        raise AmbiguousExecuteError(
            "executeTask timed out after submission. Do not create another task until "
            "the original request has been reconciled."
        ) from error
    except requests.exceptions.RequestException as error:
        if getattr(error, "response", None) is None:
            raise AmbiguousExecuteError(
                "executeTask failed without an HTTP response. It may have been submitted; "
                "do not create another task until this request has been reconciled."
            ) from error
        print(f"Error: executeTask request failed: {error}")
        raise


def export_data(
    api_key,
    task_id,
    lot_no,
    output_folder=".",
    max_wait_seconds=900,
    max_attempts=30,
):
    """Step 2: poll exportData serially and save the completed export."""
    print(f"Monitoring task {task_id} and preparing a {EXPORT_FILE_TYPE} export...")
    url = f"{BASE_URL}/api/agentTools/exportData"
    headers = {"x-api-key": api_key, "Content-Type": "application/json"}
    params = {
        "taskId": task_id,
        "exportFileType": EXPORT_FILE_TYPE,
        "previewRows": PREVIEW_ROWS,
    }
    if lot_no not in (None, ""):
        params["lotNo"] = lot_no

    max_wait_seconds = max(1, min(max_wait_seconds, MAX_POLL_SECONDS))
    max_attempts = max(1, min(max_attempts, MAX_POLL_ATTEMPTS))
    deadline = time.monotonic() + max_wait_seconds
    last_result = None
    for attempt in range(1, max_attempts + 1):
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise Exception(
                f"Polling exceeded {max_wait_seconds} seconds. Last response: {last_result}"
            )
        elapsed = max_wait_seconds - remaining

        try:
            response = requests.get(
                url,
                headers=headers,
                params=params,
                timeout=max(1, min(30, remaining)),
            )
            if response.status_code != 200:
                print(f"Warning: exportData returned an error: {response.text}")
            response.raise_for_status()
            result = response.json()
            last_result = result
            print(
                f"Debug - exportData response {attempt}/{max_attempts} "
                f"(elapsed {int(elapsed)}s): {json.dumps(result, ensure_ascii=False)}"
            )

            data = result.get("data") if isinstance(result.get("data"), dict) else {}
            status = str(data.get("status") or result.get("status") or "").lower()
            if status == "exported":
                print("Task export completed successfully.")
                return _download_exported_file(data, output_folder, task_id)
            if status in {"no_data", "invalid"}:
                raise Exception(f"Task export stopped with status '{status}': {result}")
            if status == "failed" and data.get("recoverable") is not True:
                raise Exception(f"Task export failed: {result}")

            if attempt == max_attempts:
                break
            wait_time = _extract_wait_time(result, data)
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                break
            wait_time = min(wait_time + random.uniform(0, min(5, wait_time * 0.1)), remaining)
            print(f"Task status: {status or 'unknown'}, retrying in {wait_time} seconds...")
            time.sleep(wait_time)
        except requests.exceptions.RequestException as error:
            if attempt == max_attempts or not _is_retryable_request_error(error):
                raise
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                break
            retry_delay = min(10 + random.uniform(0, 2), remaining)
            print(f"Warning: export request failed: {error}; retrying in {retry_delay} seconds...")
            time.sleep(retry_delay)

    raise Exception(
        f"Polling reached {max_attempts} attempts without completing. Last response: {last_result}"
    )


def _extract_wait_time(result, data):
    """Read retry guidance and return a delay bounded to 1-600 seconds."""
    retry_guidance = data.get("retryGuidance") or result.get("retryGuidance") or {}
    if isinstance(retry_guidance, dict):
        for key in ("waitSecondsMin", "delay"):
            delay = retry_guidance.get(key)
            if isinstance(delay, (int, float)):
                return max(1, min(600, delay))

    suggested = data.get("suggestedNextCall") or result.get("suggestedNextCall")
    if isinstance(suggested, dict) and isinstance(suggested.get("delayMs"), (int, float)):
        return max(1, min(600, suggested["delayMs"] / 1000))
    if isinstance(suggested, (int, float)):
        return max(1, min(600, suggested))
    return 60


def _is_retryable_request_error(error):
    response = getattr(error, "response", None)
    status_code = getattr(response, "status_code", None)
    if status_code is None:
        return True
    return status_code in {408, 429} or 500 <= status_code <= 599


class AmbiguousExecuteError(Exception):
    pass


def _state_paths(output_folder):
    prefix = os.path.join(output_folder, f".agenttools-{TEMPLATE_NAME}")
    return prefix + ".lock", prefix + ".state.json", prefix + ".ambiguous"


def _acquire_run_lock(lock_path):
    if fcntl is None:
        raise RuntimeError("This generated executor requires fcntl for single-flight locking.")
    lock_file = open(lock_path, "a+", encoding="utf-8")
    try:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        lock_file.close()
        raise RuntimeError("Another process is already running this template executor.")
    return lock_file


def _load_task_state(state_path):
    if not os.path.exists(state_path):
        return None
    with open(state_path, "r", encoding="utf-8") as state_file:
        state = json.load(state_file)
    if not state.get("taskId"):
        raise RuntimeError(f"Invalid task state file: {state_path}")
    return state


def _save_task_state(state_path, task_id, lot_no):
    temporary_path = state_path + ".tmp"
    with open(temporary_path, "w", encoding="utf-8") as state_file:
        json.dump({"taskId": task_id, "lotNo": lot_no}, state_file)
    os.replace(temporary_path, state_path)


EXPORT_FILE_EXTENSIONS = {
    "JSON": "json",
    "CSV": "csv",
    "EXCEL": "xlsx",
    "HTML": "html",
    "XML": "xml",
}


def _download_exported_file(data, output_folder, task_id):
    """Download an HTTPS export URL, or save sampleData as JSON."""
    os.makedirs(output_folder, exist_ok=True)
    extension = EXPORT_FILE_EXTENSIONS.get(EXPORT_FILE_TYPE.upper(), "json")
    filepath = os.path.join(output_folder, f"octoparse_export_{task_id}.{extension}")

    export_file_url = data.get("exportFileUrl")
    if export_file_url:
        if not export_file_url.lower().startswith("https://"):
            raise Exception("Refusing to download a non-HTTPS exportFileUrl.")
        print(f"Downloading exported data from: {export_file_url}")
        file_response = requests.get(
            export_file_url,
            timeout=60,
            stream=True,
            allow_redirects=True,
        )
        temporary_path = filepath + ".part"
        try:
            file_response.raise_for_status()
            final_url = str(getattr(file_response, "url", export_file_url))
            if not final_url.lower().startswith("https://"):
                raise Exception("Refusing an export download redirected away from HTTPS.")
            content_length = file_response.headers.get("Content-Length")
            if content_length and int(content_length) > MAX_EXPORT_BYTES:
                raise Exception("Export file exceeds the 100 MiB download limit.")

            downloaded = 0
            with open(temporary_path, "wb") as output_file:
                for chunk in file_response.iter_content(chunk_size=64 * 1024):
                    if not chunk:
                        continue
                    downloaded += len(chunk)
                    if downloaded > MAX_EXPORT_BYTES:
                        raise Exception("Downloaded export exceeds the 100 MiB limit.")
                    output_file.write(chunk)
            os.replace(temporary_path, filepath)
        finally:
            file_response.close()
            if os.path.exists(temporary_path):
                os.remove(temporary_path)
        return filepath

    sample_data = data.get("sampleData") or []
    filepath = os.path.join(output_folder, f"octoparse_export_{task_id}.json")
    with open(filepath, "w", encoding="utf-8") as output_file:
        json.dump(sample_data, output_file, ensure_ascii=False, indent=4)
    return filepath


if __name__ == "__main__":
    # ================= Configuration =================
    API_KEY = (os.environ.get("OCTOPARSE_API_KEY") or prompt_secret(
        "Enter your Octoparse API Key: "
    )).strip()
    EXTERNAL_USER_ID = input("Enter a stable external user ID: ").strip()
    OUTPUT_FOLDER = (
        input("Enter the export folder (press Enter for current directory): ").strip() or "."
    )
    # ===================================================

    if not API_KEY:
        raise SystemExit("API Key cannot be empty.")
    if not EXTERNAL_USER_ID:
        raise SystemExit("External user ID cannot be empty.")

    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    lock_path, state_path, ambiguous_path = _state_paths(OUTPUT_FOLDER)
    run_lock = _acquire_run_lock(lock_path)
    try:
        print_parameter_reference()
        if os.path.exists(ambiguous_path):
            raise RuntimeError(
                f"A previous executeTask result is ambiguous. Reconcile it before removing {ambiguous_path}."
            )
        task_state = _load_task_state(state_path)
        if task_state:
            created_task_id = task_state["taskId"]
            created_lot_no = task_state.get("lotNo")
            print(f"Resuming export for existing task {created_task_id}.")
        else:
            confirmation = input("Type EXECUTE to create one paid cloud task: ").strip()
            if confirmation != "EXECUTE":
                raise RuntimeError("Task creation was not confirmed.")
            try:
                created_task_id, created_lot_no = execute_task(API_KEY, EXTERNAL_USER_ID)
            except AmbiguousExecuteError:
                with open(ambiguous_path, "x", encoding="utf-8") as marker_file:
                    marker_file.write("executeTask timed out; reconcile before retrying.\n")
                raise
            _save_task_state(state_path, created_task_id, created_lot_no)
        saved_filepath = export_data(
            API_KEY,
            created_task_id,
            created_lot_no,
            output_folder=OUTPUT_FOLDER,
        )
        os.remove(state_path)
        print(f"\nExport complete! Saved to: {os.path.abspath(saved_filepath)}")
    except Exception as error:
        print(f"\nProgram terminated, error details: {error}")
        raise SystemExit(1)
    finally:
        run_lock.close()
