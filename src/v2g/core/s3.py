from typing import Annotated, Any

from fastapi import Depends, Request


async def get_s3_client(request: Request) -> Any:
    return request.state.s3_client


S3ClientDep = Annotated[Any, Depends(get_s3_client)]
