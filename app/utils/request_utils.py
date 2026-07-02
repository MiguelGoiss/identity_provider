from fastapi import Request

def get_client_ip(request: Request) -> str:
    """
    Extracts the real client IP address from the request headers if behind a proxy,
    otherwise falls back to the direct client host.
    """
    if not request:
        return "0.0.0.0"
        
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # X-Forwarded-For can be a comma-separated list of IPs. The first one is the original client.
        return forwarded_for.split(",")[0].strip()
        
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()
        
    if request.client and request.client.host:
        return request.client.host
        
    return "0.0.0.0"

def get_user_agent(request: Request) -> str:
    """
    Extracts the User-Agent header from the request.
    """
    if not request:
        return "Unknown"
    return request.headers.get("User-Agent", "Unknown")
