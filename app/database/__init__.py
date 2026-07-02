from fastapi import FastAPI
from tortoise.exceptions import IntegrityError, DoesNotExist


def register_db_exceptions(app: FastAPI) -> None:
  """
  Manually maps Tortoise ORM exceptions to HTTP responses.
  Complements register_tortoise(add_exception_handlers=True) with
  custom JSON formatting for IntegrityError and DoesNotExist.
  """
  @app.exception_handler(IntegrityError)
  async def integrity_error_handler(request, exc):
    import logging
    logging.error(f"IntegrityError: {exc}")
    return await _exception_response(409, "A data conflict occurred. Please check your input.")

  @app.exception_handler(DoesNotExist)
  async def does_not_exist_handler(request, exc):
    return await _exception_response(404, str(exc))

async def _exception_response(status_code: int, message: str):
  from fastapi.responses import JSONResponse
  return JSONResponse(
    status_code=status_code,
    content={"detail": message}
  )