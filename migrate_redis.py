# migrate_to_redis.py - FINAL WORKING VERSION
import os
import pickle
import redis
import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger(__name__)

def extract_pickles_from_stream(filepath):
    """Extract all pickle objects from a binary stream by scanning for protocol markers."""
    items = []
    try:
        with open(filepath, 'rb') as f:
            data = f.read()
            
        # Pickle protocol markers: \x80\x03 (proto3), \x80\x04 (proto4), \x80\x05 (proto5)
        markers = [b'\x80\x03', b'\x80\x04', b'\x80\x05']
        pos = 0
        
        while pos < len(data) - 2:
            # Look for next pickle marker
            found = False
            for marker in markers:
                idx = data.find(marker, pos)
                if idx != -1:
                    # Try to unpickle from this position
                    try:
                        unpickler = pickle.Unpickler(data[idx:].io.BytesIO() if hasattr(data[idx:], 'io') else None)
                        # Actually, simpler: use loads on a slice and let it fail naturally
                        obj = pickle.loads(data[idx:], encoding='bytes')
                        if isinstance(obj, dict) and 'url' in obj:
                            items.append(obj)
                        # Move position past this object (approximate)
                        pos = idx + 100  # Conservative jump; the next loop will find the real next marker
                        found = True
                        break
                    except Exception:
                        # Not a valid pickle at this position, keep scanning
                        pos = idx + 1
                        found = True
                        break
            if not found:
                pos += 1
                
    except Exception as e:
        log.debug(f"Stream parse error {os.path.basename(filepath)}: {e}")
    return items

# Better version using proper incremental parsing:
def extract_pickles_streaming(filepath):
    """Extract pickles by scanning for markers and using incremental unpickling."""
    import io
    
    items = []
    try:
        with open(filepath, 'rb') as f:
            data = f.read()
        
        # Find all positions of pickle protocol markers
        markers = [b'\x80\x03', b'\x80\x04', b'\x80\x05']
        positions = []
        for marker in markers:
            start = 0
            while True:
                idx = data.find(marker, start)
                if idx == -1:
                    break
                positions.append(idx)
                start = idx + 1
        
        positions.sort()
        
        # Try to unpickle from each marker position
        for pos in positions:
            try:
                # Create a BytesIO from the slice starting at this marker
                stream = io.BytesIO(data[pos:])
                unpickler = pickle.Unpickler(stream)
                obj = unpickler.load()
                
                if isinstance(obj, dict) and 'url' in obj:
                    items.append(obj)
            except Exception:
                continue  # Try next marker
                
    except Exception as e:
        log.debug(f"Streaming parse error: {e}")
    return items

def migrate_jodir_to_redis(jodir_path: str, redis_url: str, spider_name: str, clear_existing: bool = True):
    r = redis.from_url(redis_url, decode_responses=False)
    queue_key = f"{spider_name}:requests"
    dupe_key = f"{spider_name}:dupefilter"
    state_key = f"{spider_name}:state"

    if clear_existing:
        log.info("🗑️  Clearing existing Redis keys...")
        r.delete(queue_key, dupe_key, state_key)

    # 1️⃣ DupeFilter
    seen_file = os.path.join(jodir_path, "requests.seen")
    if os.path.exists(seen_file):
        log.info("📦 Migrating dupefilter...")
        with open(seen_file, "r", encoding="utf-8", errors="ignore") as f:
            fps = [line.strip() for line in f if line.strip()]
        if fps:
            for i in range(0, len(fps), 1000):
                r.sadd(dupe_key, *fps[i:i+1000])
            log.info(f"✅ {len(fps)} fingerprints migrated")

    # 2️⃣ Queue - Scan for pickles directly
    queue_path = os.path.join(jodir_path, "requests.queue")
    if os.path.isdir(queue_path):
        log.info("📦 Migrating queue (scanning for pickle streams)...")
        count = 0
        
        for root, dirs, files in os.walk(queue_path):
            for fname in files:
                if fname in {"info.json", "active.json"} or fname.endswith(".lock"):
                    continue
                fpath = os.path.join(root, fname)
                if os.path.getsize(fpath) < 100:  # Too small to contain requests
                    continue
                    
                # Infer priority
                priority = 0
                if fname.isdigit():
                    priority = int(fname)
                else:
                    for part in root.split(os.sep):
                        if part.isdigit():
                            priority = int(part)
                            break
                
                reqs = extract_pickles_streaming(fpath)
                for req_dict in reqs:
                    req_dict['priority'] = priority
                    r.zadd(queue_key, {pickle.dumps(req_dict): priority})
                    count += 1
                    
                if reqs:
                    log.info(f"   • {fname}: {len(reqs)} requests (priority={priority})")
                    
        log.info(f"✅ {count} total pending requests migrated")

    # 3️⃣ Spider State
    state_file = os.path.join(jodir_path, "spider.state")
    if os.path.exists(state_file):
        with open(state_file, "rb") as f:
            r.set(state_key, f.read())
        log.info("✅ spider.state migrated")

    log.info("🎉 Migration complete!")
    log.info(f"   • Queue: {r.zcard(queue_key)}")
    log.info(f"   • Dupefilter: {r.scard(dupe_key)}")

if __name__ == "__main__":
    migrate_jodir_to_redis(
        jodir_path="jobdir/goodreads",
        redis_url="redis://localhost:6379/0",
        spider_name="goodreads",
        clear_existing=True
    )