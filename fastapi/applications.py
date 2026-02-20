from __future__ import annotations

from typing import (
    Any,
    Awaitable,
    Callable,
    Coroutine,
    Dict,
    List,
    Optional,
    Sequence,
    Type,
    Union,
)

from fastapi.datastructures import Default, DefaultPlaceholder
from fastapi.exceptions import RequestValidationError
from fastapi.logger import logger
from fastapi.openapi.docs import (
    get_redoc_html,
    get_swagger_ui_html,
    get_swagger_ui_oauth2_redirect_html,
)
from fastapi.params import Depends
from fastapi.types import DecoratedCallable
from starlette.applications import Starlette
from starlette.datastructures import State
from starlette.middleware import Middleware
from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse, Response
from starlette.routing import BaseRoute, Mount
from starlette.types import Lifespan, Receive, Scope, Send


class FastAPI(Starlette):
    def __init__(
        self,
        *,
        debug: bool = False,
        title: str = "FastAPI",
        summary: Optional[str] = None,
        description: str = "",
        version: str = "0.1.0",
        openapi_url: Optional[str] = "/openapi.json",
        openapi_tags: Optional[List[Dict[str, Any]]] = None,
        servers: Optional[List[Dict[str, Union[str, Any]]]] = None,
        dependencies: Optional[Sequence[Depends]] = None,
        default_response_class: Type[Response] = Default(JSONResponse),
        redirect_slashes: bool = True,
        docs_url: Optional[str] = "/docs",
        redoc_url: Optional[str] = "/redoc",
        swagger_ui_oauth2_redirect_url: Optional[str] = "/docs/oauth2-redirect",
        swagger_ui_init_oauth: Optional[Dict[str, Any]] = None,
        middleware: Optional[Sequence[Middleware]] = None,
        exception_handlers: Optional[
            Dict[
                Union[int, Type[Exception]],
                Callable[[Request, Any], Union[Response, Awaitable[Response]]],
            ]
        ] = None,
        on_startup: Optional[Sequence[Callable[[], Any]]] = None,
        on_shutdown: Optional[Sequence[Callable[[], Any]]] = None,
        lifespan: Optional[Lifespan[Starlette]] = None,
        terms_of_service: Optional[str] = None,
        contact: Optional[Dict[str, Union[str, Any]]] = None,
        license_info: Optional[Dict[str, Union[str, Any]]] = None,
        openapi_prefix: str = "",
        root_path: str = "",
        root_path_in_servers: bool = True,
        responses: Optional[Dict[Union[int, str], Dict[str, Any]]] = None,
        callbacks: Optional[List[BaseRoute]] = None,
        webhooks: Optional[APIRouter] = None,
        deprecated: Optional[bool] = None,
        include_in_schema: bool = True,
        swagger_ui_parameters: Optional[Dict[str, Any]] = None,
        generate_unique_id_function: Callable[[APIRoute], str] = Default(
            generate_unique_id
        ),
        separate_input_output_schemas: bool = True,
        **extra: Any,
    ) -> None:
        self._debug = debug
        self.title = title
        self.summary = summary
        self.description = description
        self.version = version
        self.terms_of_service = terms_of_service
        self.contact = contact
        self.license_info = license_info
        self.openapi_url = openapi_url
        self.openapi_tags = openapi_tags
        self.servers = servers or []
        self.separate_input_output_schemas = separate_input_output_schemas
        self.extra = extra
        self.openapi_version = "3.1.0"
        self.openapi_schema: Optional[Dict[str, Any]] = None
        self.root_path_in_servers = root_path_in_servers
        self.docs_url = docs_url
        self.redoc_url = redoc_url
        self.swagger_ui_oauth2_redirect_url = swagger_ui_oauth2_redirect_url
        self.swagger_ui_init_oauth = swagger_ui_init_oauth
        self.swagger_ui_parameters = swagger_ui_parameters
        self.state: State = State()
        self.dependency_overrides: Dict[Callable[..., Any], Callable[..., Any]] = {}
        self.router: APIRouter = APIRouter(
            routes=routes,
            dependency_overrides_provider=self,
            on_startup=on_startup,
            on_shutdown=on_shutdown,
            default_response_class=default_response_class,
            dependencies=dependencies,
            callbacks=callbacks,
            responses=responses,
            deprecated=deprecated,
            include_in_schema=include_in_schema,
            generate_unique_id_function=generate_unique_id_function,
        )
        self.exception_handlers = (
            {} if exception_handlers is None else dict(exception_handlers)
        )
        self.exception_handlers.setdefault(
            RequestValidationError, request_validation_exception_handler
        )
        self.exception_handlers.setdefault(ValidationError, validation_exception_handler)
        self.user_middleware: List[Middleware] = (
            [] if middleware is None else list(middleware)
        )
        self.middleware_stack: ASGIApp = self.build_middleware_stack()
        self.setup()