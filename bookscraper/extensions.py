# extensions.py
import json
import logging
import pickle
from scrapy import signals
from datetime import datetime, date
from decimal import Decimal

logger = logging.getLogger(__name__)

class RedisSpiderState:
    """
    Persist spider.state to Redis using JSON (with custom encoder for datetime/Decimal).
    
    Usage:
        1. Add to EXTENSIONS in settings.py
        2. Use spider.state normally in your spider
        3. State auto-loads on open, auto-saves on close
    """
    
    def __init__(self, crawler):
        self.crawler = crawler
        self.redis = None
        self.state_key = None
        self.auto_save_interval = crawler.settings.getint('REDIS_STATE_AUTO_SAVE_SECONDS', 0)
        self._last_save = None
        
    @classmethod
    def from_crawler(cls, crawler):
        ext = cls(crawler)
        crawler.signals.connect(ext.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(ext.spider_closed, signal=signals.spider_closed)
        
        # Optional: periodic saves for long-running spiders
        if ext.auto_save_interval > 0:
            crawler.signals.connect(ext.spider_idle, signal=signals.spider_idle)
            
        return ext
    
    def spider_opened(self, spider):
        """Load state from Redis when spider starts."""
        self.state_key = f"spider:{spider.name}:state"
        
        # Get Redis client from scrapy-redis (attached to crawler)
        self.redis = getattr(self.crawler.engine, 'scheduler', None)
        if self.redis and hasattr(self.redis, 'server'):
            self.redis = self.redis.server
        else:
            # Fallback: create new connection from settings
            import redis
            redis_url = self.crawler.settings.get('REDIS_URL', 'redis://localhost:6379/0')
            self.redis = redis.from_url(redis_url, decode_responses=False)
        
        # Load state
        try:
            raw = self.redis.get(self.state_key)
            if raw:
                spider.state = self._decode_state(raw)
                logger.info(f"📥 Loaded spider.state from Redis ({len(spider.state)} keys)")
            else:
                spider.state = {}
                logger.info("🆕 Initialized empty spider.state")
        except Exception as e:
            logger.warning(f"⚠️  Failed to load spider.state: {e}")
            spider.state = {}
    
    def spider_closed(self, spider, reason):
        """Save state to Redis when spider stops."""
        self._save_state(spider, reason=reason)
        logger.info(f"💾 Saved spider.state to Redis (reason: {reason})")
    
    def spider_idle(self, spider):
        """Optional: auto-save state periodically during long runs."""
        if self.auto_save_interval > 0:
            now = datetime.now()
            if not self._last_save or (now - self._last_save).total_seconds() >= self.auto_save_interval:
                self._save_state(spider, reason='auto-save')
                self._last_save = now
    
    def _save_state(self, spider, reason=''):
        """Internal: serialize and save state to Redis."""
        try:
            encoded = self._encode_state(spider.state)
            self.redis.set(self.state_key, encoded)
            logger.debug(f"💾 spider.state saved ({len(encoded)} bytes) - {reason}")
        except Exception as e:
            logger.error(f"❌ Failed to save spider.state: {e}")
    
    def _encode_state(self, state: dict) -> bytes:
        """Serialize state dict to bytes, handling non-JSON types."""
        return json.dumps(state, cls=_StateEncoder).encode('utf-8')
    
    def _decode_state(self, raw: bytes) -> dict:
        """Deserialize bytes to state dict, restoring special types."""
        return json.loads(raw.decode('utf-8'), object_hook=_state_decoder)


# --- Custom JSON Encoder/Decoder for common Scrapy types ---

class _StateEncoder(json.JSONEncoder):
    """Encode datetime, Decimal, bytes, set, etc. to JSON-compatible format."""
    def default(self, obj):
        if isinstance(obj, (datetime, date)):
            return {'__type__': 'datetime', 'value': obj.isoformat()}
        if isinstance(obj, Decimal):
            return {'__type__': 'decimal', 'value': str(obj)}
        if isinstance(obj, bytes):
            return {'__type__': 'bytes', 'value': obj.hex()}
        if isinstance(obj, set):
            return {'__type__': 'set', 'value': list(obj)}
        if isinstance(obj, Exception):
            return {'__type__': 'exception', 'class': obj.__class__.__name__, 'message': str(obj)}
        # Fallback: try string representation (lossy but safe)
        return {'__type__': 'str', 'value': str(obj)}


def _state_decoder(dct: dict):
    """Restore special types from JSON during decode."""
    if '__type__' not in dct:
        return dct
        
    t = dct['__type__']
    v = dct.get('value')
    
    if t == 'datetime':
        return datetime.fromisoformat(v)
    if t == 'decimal':
        return Decimal(v)
    if t == 'bytes':
        return bytes.fromhex(v)
    if t == 'set':
        return set(v)
    if t == 'exception':
        # Reconstruct a basic exception (not fully functional, but preserves message)
        return Exception(f"{dct.get('class')}: {v}")
    if t == 'str':
        return v  # Already a string
        
    return dct  # Fallback