from v2g.models import ErrorResponse

_error_responses = {
    400: {
        'model': ErrorResponse,
        'description': 'Could not complete the request successfully with this input data.',
    },
    401: {'model': ErrorResponse, 'description': 'Could not authorize. No token was provided.'},
    403: {'model': ErrorResponse, 'description': 'Could not authorize. Provided token is invalid.'},
    404: {'model': ErrorResponse, 'description': 'Not found.'},
}


def create_error_responses(status_codes: set, add_token_related_errors=False):
    if add_token_related_errors:
        status_codes.add(401)
        status_codes.add(403)

    return {k: v for k, v in _error_responses.items() if k in status_codes}
