import binascii

from fastapi import Depends, HTTPException, Query
from orjson import JSONDecodeError

from services.film import FilmService, get_film_service


class PaginatedParams:
    def __init__(self,
                 page_number: int = Query(
                     default=1,
                     alias="page[number]",
                     ge=1,
                     description="Номер страницы, данным перебором можно получить не более 10000 документов"
                 ),
                 page_next: str | None = Query(
                     default=None,
                     alias="page[next]",
                     description="Токен (next) для получения следующей страницы, при использовании игнорируется page[number]"
                 ),
                 film_service: FilmService = Depends(get_film_service),
            ):
        self.page_number = page_number
        self.page_next = page_next
        self.search_after = None
        if self.page_next:
            try:
                self.search_after = film_service.b64decode_sync(self.page_next)
            except (binascii.Error, JSONDecodeError):
                raise HTTPException(status_code=422, detail="page[next] not valid")
