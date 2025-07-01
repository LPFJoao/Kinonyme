import asyncpg

class GuildConfigDB:
    def __init__(self, pool):
        self.pool = pool

    async def get_config(self, guild_id):
        """Fetch configuration for a specific guild."""
        return await self.pool.fetchrow(
            "SELECT * FROM guild_configs WHERE guild_id = $1", guild_id
        )

    async def set_config(self, guild_id, **kwargs):
        """
        Set or update configuration for a guild.
        kwargs: Dict of config keys/values (e.g., welcome_channel=123).
        """
        keys = ', '.join(kwargs.keys())
        values = list(kwargs.values())
        placeholders = ', '.join(f'${i+2}' for i in range(len(values)))
        update_clause = ', '.join(f"{k} = EXCLUDED.{k}" for k in kwargs.keys())
        await self.pool.execute(
            f"""
            INSERT INTO guild_configs (guild_id, {keys})
            VALUES ($1, {placeholders})
            ON CONFLICT (guild_id)
            DO UPDATE SET {update_clause}
            """,
            guild_id, *values
        )

