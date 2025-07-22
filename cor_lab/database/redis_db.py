from redis.asyncio import Redis
from cor_lab.config.config import settings


redis_client = Redis(
    host=settings.redis_host,
    port=settings.redis_port,
    db=settings.redis_db,
    decode_responses=True,
)
