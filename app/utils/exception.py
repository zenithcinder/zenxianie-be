from django.forms import ValidationError
from django.http import Http404
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import APIException, PermissionDenied, NotAuthenticated
from django.core.exceptions import PermissionDenied
from django.db import IntegrityError
from django.db.utils import DataError
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.conf import settings
import traceback


def custom_exception_handler(exc, context):
    """Custom exception handler for DRF that returns consistent JSON responses."""
    response = exception_handler(exc, context)

    if response is not None:
        # If the exception is already handled by DRF
        error_data = {
            'status': 'error',
            'code': response.status_code,
            'message': response.data
        }
        
        # Add debug information if DEBUG is True
        if settings.DEBUG:
            error_data['debug'] = {
                'exception_type': exc.__class__.__name__,
                'exception_message': str(exc),
                'traceback': traceback.format_exc()
            }
        
        return Response(error_data, status=response.status_code)

    # Handle Django's ValidationError
    if isinstance(exc, ValidationError):
        error_data = {
            'status': 'error',
            'code': status.HTTP_400_BAD_REQUEST,
            'message': exc.message_dict if hasattr(exc, 'message_dict') else str(exc)
        }
        
        if settings.DEBUG:
            error_data['debug'] = {
                'exception_type': exc.__class__.__name__,
                'exception_message': str(exc),
                'traceback': traceback.format_exc()
            }
        
        return Response(error_data, status=status.HTTP_400_BAD_REQUEST)

    # Handle database integrity errors
    if isinstance(exc, IntegrityError):
        error_data = {
            'status': 'error',
            'code': status.HTTP_400_BAD_REQUEST,
            'message': 'Database integrity error. This might be due to duplicate entries or invalid data.'
        }
        
        if settings.DEBUG:
            error_data['debug'] = {
                'exception_type': exc.__class__.__name__,
                'exception_message': str(exc),
                'traceback': traceback.format_exc()
            }
        
        return Response(error_data, status=status.HTTP_400_BAD_REQUEST)

    # Handle database data errors
    if isinstance(exc, DataError):
        error_data = {
            'status': 'error',
            'code': status.HTTP_400_BAD_REQUEST,
            'message': 'Invalid data format or length.'
        }
        
        if settings.DEBUG:
            error_data['debug'] = {
                'exception_type': exc.__class__.__name__,
                'exception_message': str(exc),
                'traceback': traceback.format_exc()
            }
        
        return Response(error_data, status=status.HTTP_400_BAD_REQUEST)

    # Handle JWT token errors
    if isinstance(exc, (InvalidToken, TokenError)):
        error_data = {
            'status': 'error',
            'code': status.HTTP_401_UNAUTHORIZED,
            'message': 'Invalid or expired token.'
        }
        
        if settings.DEBUG:
            error_data['debug'] = {
                'exception_type': exc.__class__.__name__,
                'exception_message': str(exc),
                'traceback': traceback.format_exc()
            }
        
        return Response(error_data, status=status.HTTP_401_UNAUTHORIZED)

    # Handle permission denied errors
    if isinstance(exc, PermissionDenied):
        error_data = {
            'status': 'error',
            'code': status.HTTP_403_FORBIDDEN,
            'message': 'You do not have permission to perform this action.'
        }
        
        if settings.DEBUG:
            error_data['debug'] = {
                'exception_type': exc.__class__.__name__,
                'exception_message': str(exc),
                'traceback': traceback.format_exc()
            }
        
        return Response(error_data, status=status.HTTP_403_FORBIDDEN)

    # Handle authentication errors
    if isinstance(exc, NotAuthenticated):
        error_data = {
            'status': 'error',
            'code': status.HTTP_401_UNAUTHORIZED,
            'message': 'Authentication credentials were not provided.'
        }
        
        if settings.DEBUG:
            error_data['debug'] = {
                'exception_type': exc.__class__.__name__,
                'exception_message': str(exc),
                'traceback': traceback.format_exc()
            }
        
        return Response(error_data, status=status.HTTP_401_UNAUTHORIZED)

    # Handle 404 errors
    if isinstance(exc, Http404):
        error_data = {
            'status': 'error',
            'code': status.HTTP_404_NOT_FOUND,
            'message': 'Resource not found.'
        }
        
        if settings.DEBUG:
            error_data['debug'] = {
                'exception_type': exc.__class__.__name__,
                'exception_message': str(exc),
                'traceback': traceback.format_exc()
            }
        
        return Response(error_data, status=status.HTTP_404_NOT_FOUND)

    # Handle any other unhandled exceptions
    error_data = {
        'status': 'error',
        'code': status.HTTP_500_INTERNAL_SERVER_ERROR,
        'message': 'An unexpected error occurred. Please try again later.'
    }
    
    if settings.DEBUG:
        error_data['debug'] = {
            'exception_type': exc.__class__.__name__,
            'exception_message': str(exc),
            'traceback': traceback.format_exc()
        }
    
    return Response(error_data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)