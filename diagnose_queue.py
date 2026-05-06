import os
import struct
import pickle
import marshal

filepath = r"jobdir\goodreads\requests.queue\www.goodreads.com-977183fec4dc383a841d102853b1806d\0"

print(f"📁 File: {filepath}")
print(f"📏 Size: {os.path.getsize(filepath):,} bytes\n")

with open(filepath, 'rb') as f:
    # Read first 100 bytes as hex + ASCII
    raw = f.read(100)
    print("🔍 First 100 bytes (hex):")
    print(' '.join(f"{b:02X}" for b in raw[:50]))
    print(' '.join(f"{b:02X}" for b in raw[50:100]))
    print("\n🔍 ASCII preview (printable chars only):")
    print(''.join(chr(b) if 32 <= b < 127 else '.' for b in raw))
    
    # Try to parse as queuelib format with both endiannesses
    f.seek(0)
    for endian_name, endian_fmt in [("little-endian <I", '<I'), ("big-endian >I", '>I')]:
        print(f"\n🧪 Trying {endian_name}...")
        f.seek(0)
        count = 0
        try:
            while count < 5:  # Just try first 5 items
                header = f.read(4)
                if len(header) < 4:
                    print(f"   → EOF after {count} items")
                    break
                length = struct.unpack(endian_fmt, header)[0]
                print(f"   → Item {count+1}: length={length:,}")
                if length == 0 or length > 5_000_000:
                    print(f"   → Invalid length, stopping")
                    break
                data = f.read(length)
                if len(data) < length:
                    print(f"   → Truncated data, stopping")
                    break
                    
                # Try pickle first
                try:
                    obj = pickle.loads(data, encoding='bytes')
                    url = obj.get('url', 'N/A') if isinstance(obj, dict) else 'N/A'
                    print(f"   ✓ Pickle success: {url[:80]}...")
                    count += 1
                    continue
                except:
                    pass
                    
                # Try marshal (queuelib sometimes uses this)
                try:
                    obj = marshal.loads(data)
                    url = obj.get('url', 'N/A') if isinstance(obj, dict) else 'N/A'
                    print(f"   ✓ Marshal success: {url[:80]}...")
                    count += 1
                    continue
                except:
                    pass
                    
                print(f"   ✗ Failed to deserialize (not pickle or marshal)")
                break
        except Exception as e:
            print(f"   ✗ Parse error: {e}")