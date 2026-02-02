import os
import socket
import sys
from urllib.parse import urlparse
from dotenv import load_dotenv

# Load env without interpolation to see raw values if possible, 
# but python-dotenv defaults to interpolation.
load_dotenv(override=True)

url = os.getenv("DATABASE_URL")

print(f"--- DIAGNOSTIC START ---")

if not url:
    print("ERROR: DATABASE_URL is empty!")
    sys.exit(1)

try:
    parsed = urlparse(url)
    print(f"Hostname: {parsed.hostname}")
    print(f"Port: {parsed.port}")
    
    # Check Password Fidelity
    # mask all but last char
    if parsed.password:
        masked = "*" * (len(parsed.password)-1) + parsed.password[-1] if len(parsed.password) > 0 else "[EMPTY]"
        print(f"Password ends with: '{parsed.password[-1] if parsed.password else 'N/A'}' (Checking for '$' loss)")
        if "$" in url and "$" not in parsed.password:
             print("WARNING: It looks like the '$' sign might have been stripped by the parser/dotenv!")
    
    # Network Test
    print(f"\nResolving {parsed.hostname}...")
    try:
        infos = socket.getaddrinfo(parsed.hostname, parsed.port)
        print("DNS Resolution Succeeded:")
        for family, type, proto, canonname, sockaddr in infos:
            fam_name = "IPv6" if family == socket.AF_INET6 else "IPv4"
            print(f" - {fam_name}: {sockaddr}")
            
        print("\nAttempting socket connection...")
        # Try connecting to the first one
        family, type, proto, canonname, sockaddr = infos[0]
        s = socket.socket(family, type, proto)
        s.settimeout(5)
        s.connect(sockaddr)
        print("SUCCESS! Socket connected.")
        s.close()
        
    except socket.gaierror:
        print("ERROR: DNS Resolution failed. Host not found.")
    except Exception as e:
        print(f"ERROR: Connection failed: {e}")

except Exception as e:
    print(f"Parsing error: {e}")

print(f"--- DIAGNOSTIC END ---")
