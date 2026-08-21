# Telegram API from Russia

## The Problem

`api.telegram.org` is blocked in Russia. Hermes Gateway cannot connect
directly — all attempts time out.

## Solutions (in order of reliability)

### 1. VPN on Host Machine (Recommended)

Enable VPN before starting gateway. Hermes uses system network stack — if
`curl https://api.telegram.org` works, the gateway will work.

Test:
```bash
curl -s --connect-timeout 5 https://api.telegram.org/botTOKEN/getMe
# Should return: {"ok":true,"result":{"id":...,"username":"..."}}
```

### 2. SOCKS5 Proxy

```bash
hermes config set gateway.platforms.telegram.proxy "socks5://127.0.0.1:1080"
```

### 3. DNS-over-HTTPS Fallback (Built-in)

Hermes auto-discovers Telegram API IPs via DNS-over-HTTPS. This works if
DNS is blocked but IPs are not. The gateway tries 8 times with increasing
delays.

## Diagnostics

Hermes gateway logs will show:
```
[Telegram] Discovering Telegram API fallback IPs via DNS-over-HTTPS...
[Telegram] Connecting to Telegram (attempt 1/8)...
```

If all 8 attempts fail → VPN/proxy problem.

## Token debugging

404 from API = token invalid/revoked (NOT a connectivity issue):
```json
{"ok":false,"error_code":404,"description":"Not Found"}
```

Timeout from API = connectivity issue (VPN off or blocked):
```
curl: (28) Connection timed out
```
