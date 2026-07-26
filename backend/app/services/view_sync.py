import asyncio
import logging
import uuid
from typing import List, Dict

from redis.asyncio import Redis
from sqlalchemy import update, bindparam
from app.database import AsyncSessionLocal
from app.models.listing import Listing

logger = logging.getLogger(__name__)

DIRTY_SET_KEY = "aparty:views:dirty"
VIEW_KEY_PREFIX = "aparty:views:"

async def increment_apartment_view(apartment_id: uuid.UUID, redis_client: Redis) -> None:
    """
    Increments the view count for an apartment and adds it to the dirty set.
    """
    view_key = f"{VIEW_KEY_PREFIX}{str(apartment_id)}"
    
    # Use a pipeline to ensure atomic operations and reduce network roundtrips
    async with redis_client.pipeline(transaction=True) as pipe:
        pipe.incr(view_key)
        pipe.sadd(DIRTY_SET_KEY, str(apartment_id))
        await pipe.execute()

async def sync_views_to_db(redis_client: Redis) -> None:
    """
    Reads from the dirty set, fetches counts, updates DB in bulk, and clears keys.
    """
    try:
        # SPOP with count removes and returns the elements up to 10,000 at a time
        dirty_ids_bytes = await redis_client.spop(DIRTY_SET_KEY, 10000)
        
        if not dirty_ids_bytes:
            return
            
        # Decode bytes if decode_responses=False
        dirty_ids = [apt_id.decode('utf-8') if isinstance(apt_id, bytes) else apt_id for apt_id in dirty_ids_bytes]
        
        view_keys = [f"{VIEW_KEY_PREFIX}{apt_id}" for apt_id in dirty_ids]
        view_counts = await redis_client.mget(view_keys)
        
        update_params = []
        keys_to_delete = []
        
        for apt_id, count_bytes in zip(dirty_ids, view_counts):
            if count_bytes:
                count_str = count_bytes.decode('utf-8') if isinstance(count_bytes, bytes) else count_bytes
                update_params.append({
                    "b_id": uuid.UUID(apt_id),
                    "b_views": int(count_str)
                })
                keys_to_delete.append(f"{VIEW_KEY_PREFIX}{apt_id}")

        if not update_params:
            return

        async with AsyncSessionLocal() as db_session:
            async with db_session.begin():
                stmt = (
                    update(Listing)
                    .where(Listing.id == bindparam('b_id'))
                    .values(views_count=Listing.views_count + bindparam('b_views'))
                )
                await db_session.execute(stmt, update_params)
            
        if keys_to_delete:
            await redis_client.delete(*keys_to_delete)
            
        logger.info(f"Successfully synchronized view counts for {len(update_params)} apartments.")

    except Exception as e:
        logger.error(f"Error during view synchronization: {e}")
        # Re-add to dirty set on failure
        if 'dirty_ids_bytes' in locals() and dirty_ids_bytes:
             await redis_client.sadd(DIRTY_SET_KEY, *dirty_ids_bytes)

async def view_sync_daemon(redis_client: Redis):
    """Background daemon that wakes up every 5 minutes."""
    logger.info("View sync daemon started.")
    while True:
        await asyncio.sleep(300) # Sleep for 5 minutes (300 seconds)
        await sync_views_to_db(redis_client)
