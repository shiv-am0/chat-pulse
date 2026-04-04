from config.redis_client import get_redis_client


def room_members_key(room_id: int) -> str:
    return f"room:{room_id}:members"


def room_info_key(room_id: int) -> str:
    return f"room:{room_id}:info"


def room_channel(room_id: int) -> str:
    return f"room:{room_id}"


def add_member_to_room(room_id: int, user_id: int) -> None:
    r = get_redis_client()
    r.sadd(room_members_key(room_id), user_id)


def remove_member_from_room(room_id: int, user_id: int) -> None:
    r = get_redis_client()
    r.srem(room_members_key(room_id), user_id)


def is_member_of_room(room_id: int, user_id: int) -> bool:
    r = get_redis_client()
    return r.sismember(room_members_key(room_id), user_id)


def get_room_members(room_id: int) -> set:
    r = get_redis_client()
    return r.smembers(room_members_key(room_id))


def get_room_member_count(room_id: int) -> int:
    r = get_redis_client()
    return r.scard(room_members_key(room_id))


def delete_room_cache(room_id: int) -> None:
    r = get_redis_client()
    r.delete(
        room_members_key(room_id),
        room_info_key(room_id),
    )


def sync_room_members_to_redis(room_id: int, user_ids: list) -> None:
    r = get_redis_client()
    key = room_members_key(room_id)
    pipe = r.pipeline()
    pipe.delete(key)
    if user_ids:
        pipe.sadd(key, *user_ids)
    pipe.execute()


def cache_room_info(room_id: int, name: str, creator_id: int) -> None:
    r = get_redis_client()
    r.hset(
        room_info_key(room_id),
        mapping={
            "name": name,
            "creator_id": str(creator_id),
        }
    )
    r.expire(room_info_key(room_id), 3600)


def get_cached_room_info(room_id: int) -> dict | None:
    r = get_redis_client()
    data = r.hgetall(room_info_key(room_id))
    return data if data else None


def publish_message(room_id: int, message: str) -> None:
    r = get_redis_client()
    r.publish(room_channel(room_id), message)


def get_pubsub_client():
    r = get_redis_client()
    return r.pubsub()