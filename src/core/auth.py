"""Декораторы для ограничения доступа к ручкам. В списке аргументов ручки
обязательно должен быть параметр request (fastapi.Request).

@auth_required - пускает любых аутентифицированных пользователей;
@user_role_required('manager') - пускает пользователей с конкретной ролью.

"""
from functools import wraps

import aiohttp
from fastapi import HTTPException, status

from core.backoff import async_backoff
from core.config import settings


class AuthError(Exception):
    """Ошибка авторизации пользователя. """


@async_backoff(max_retries=3)
async def check_auth_url(request):
    session = aiohttp.ClientSession()
    async with session.get(
            settings.auth_url, headers=request.headers
    ) as auth_response:
        if auth_response.status == status.HTTP_200_OK:
            return await auth_response.json() or ['Guest']
        return ['Anonymous']

def user_role_required(role='premium'):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request = kwargs['request']
            if role in request.state.auth:
                return await func(*args, **kwargs)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="You do not have permission to access this resource",
            )
        return wrapper
    return decorator


def auth_required(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        request = kwargs['request']
        if 'Anonymous' not in request.state.auth:
            return await func(*args, **kwargs)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Only authenticated users allowed",
        )
    return wrapper
