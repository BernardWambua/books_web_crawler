from fastapi import FastAPI, Depends
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter
import redis.asyncio as redis
from contextlib import asynccontextmanager

from api.routers import books, changes


@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Startup logic ---
    # Initialize Redis client for rate limiting
    redis_client = await redis.from_url("redis://localhost", encoding="utf8", decode_responses=True)
    await FastAPILimiter.init(redis_client)

    yield

    # --- Shutdown logic ---
    await redis_client.close()
    await FastAPILimiter.close()


app = FastAPI(
    title="Books Crawler API",
    description="""
        This API provides access to book data collected from **Books to Scrape**.

        ### Features
        * Filter books by category, price, and rating
        * View individual book details
        * Track and view recent changes detected by the crawler

        🔒 All endpoints require an `X-API-Key` header.
        """,
    version="1.0.0",
    contact={
        "name": "Books Crawler Maintainer",
        "url": "https://github.com/BernardWambua/books_web_crawler",
        "email": "benerio72@gmail.com",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
    docs_url="/docs",
    lifespan=lifespan,
)

# --- Routers with rate limiting ---
app.include_router(
    books.router,
    dependencies=[Depends(RateLimiter(times=100, seconds=3600))]
)

app.include_router(
    changes.router,
    dependencies=[Depends(RateLimiter(times=100, seconds=3600))]
)
