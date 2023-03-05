"""Декораторы для ограничения доступа к ручкам. В списке аргументов ручки
обязательно должен быть параметр request (fastapi.Request).

@auth_required - пускает любых аутентифицированных пользователей;
@user_role_required('manager') - пускает пользователей с конкретной ролью.

"""

from fastapi import HTTPException, status
from functools import wraps


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
