"""
Global exception handler for DRF.
Returns all errors in a consistent shape:

    {
        "error": "short_code",
        "detail": "Human-readable message",
        "errors": { "field": ["message"] }   # only on validation errors
    }
"""

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    # Let DRF build the default response first
    response = exception_handler(exc, context)

    if response is None:
        # Unhandled exception — let Django's 500 handler deal with it
        return None

    data = {
        'error': _get_error_code(response.status_code),
        'detail': _extract_detail(response.data),
    }

    # Attach field-level validation errors when present
    if response.status_code == status.HTTP_400_BAD_REQUEST and isinstance(response.data, dict):
        field_errors = {
            k: v for k, v in response.data.items()
            if k not in ('detail', 'non_field_errors')
        }
        if field_errors:
            data['errors'] = field_errors

        non_field = response.data.get('non_field_errors')
        if non_field:
            data['detail'] = non_field[0] if isinstance(non_field, list) else non_field

    response.data = data
    return response


def _get_error_code(status_code: int) -> str:
    mapping = {
        400: 'bad_request',
        401: 'unauthorized',
        403: 'forbidden',
        404: 'not_found',
        405: 'method_not_allowed',
        409: 'conflict',
        429: 'too_many_requests',
        500: 'server_error',
    }
    return mapping.get(status_code, 'error')


def _extract_detail(data) -> str:
    if isinstance(data, dict):
        detail = data.get('detail', '')
        if detail:
            return str(detail)
        # Pick the first message from the first field
        for value in data.values():
            if isinstance(value, list) and value:
                return str(value[0])
            if isinstance(value, str):
                return value
    if isinstance(data, list) and data:
        return str(data[0])
    return str(data)
