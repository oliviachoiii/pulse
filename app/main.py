import os
from typing import Any

import httpx
from fastapi import FastAPI


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
async def status() -> dict[str, list[dict[str, Any]]]:
    results = []

    async with httpx.AsyncClient(timeout=5.0) as client:
        for url in get_targets():
            try:
                response = await client.get(url)

                results.append(
                    {
                        "url": url,
                        "status": "up" if response.is_success else "degraded",
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

    return {"services": results}