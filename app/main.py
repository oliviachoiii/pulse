import os
from typing import Any

import httpx
from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI(
    title="Project Pulse",
    description="A lightweight endpoint health checker.",
    version="1.0.0",
)


def get_targets() -> list[str]:
    raw_targets = os.getenv("TARGET_URLS", "",)

    return [
        url.strip()
        for url in raw_targets.split(",")
        if url.strip()
    ]

@app.get("/")
async def root():
    return {
        "name": "Project Pulse",
        "message": "Use /health, /status, or /docs"
    }
    
@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/status")
async def status():
    results: list[dict[str, Any]] = []

    targets = get_targets()

    if not targets:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "message": "No target URLs configured.",
                "services": [],
            },
        )

    async with httpx.AsyncClient(timeout=5.0) as client:
        for url in targets:
            try:
                response = await client.get(url)

                service_status = (
                    "up"
                    if response.is_success
                    else "degraded"
                )

                results.append(
                    {
                        "url": url,
                        "status": service_status,
                        "status_code": response.status_code,
                    }
                )

            except httpx.HTTPError as exc:
                results.append(
                    {
                        "url": url,
                        "status": "down",
                        "error": type(exc).__name__,
                    }
                )

    all_healthy = all(
        service["status"] == "up"
        for service in results
    )

    overall_status = "healthy" if all_healthy else "unhealthy"
    response_status_code = 200 if all_healthy else 503

    return JSONResponse(
        status_code=response_status_code,
        content={
            "status": overall_status,
            "services": results,
        },
    )