from asyncpg import IntegrityConstraintViolationError, ForeignKeyViolationError
from fastapi import FastAPI
from lottery_api.lib.base_exception import UniqueViolationException, ParameterViolationException, \
    hy_exception_to_json_response, add_exception_handler, use_route_names_as_operation_ids
from lottery_api.lib.logger import get_prefix_logger_adapter
from starlette.middleware.cors import CORSMiddleware

from lottery_api.endpoints import register_routers

logger = get_prefix_logger_adapter(__name__)
app = FastAPI(title="Lottery Backend API", version="1.0.0", openapi_url="/api/spec/swagger.json",
              docs_url="/api/spec/doc")
app.add_middleware(CORSMiddleware,
                   allow_origins='*',
                   allow_credentials=True,
                   allow_methods=["GET", "POST", "OPTIONS", "DELETE"],
                   allow_headers=["*"]
                   )

add_exception_handler(app)


@app.exception_handler(IntegrityConstraintViolationError)
async def db_integrity_exception_handler(request, exc: IntegrityConstraintViolationError):
    return hy_exception_to_json_response(UniqueViolationException(message=str(exc)))


@app.exception_handler(ForeignKeyViolationError)
async def db_foreignkey_exception_handler(request, exc: ForeignKeyViolationError):
    return hy_exception_to_json_response(ParameterViolationException(message=str(exc)))


# Register all API routers
register_routers(app)

use_route_names_as_operation_ids(app)

if __name__ == '__main__':
    import uvicorn

    uvicorn.run('lottery_api.main:app', host="0.0.0.0", port=8000, reload=True)
