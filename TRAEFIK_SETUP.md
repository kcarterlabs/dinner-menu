# Traefik Setup for HTTPS with Let's Encrypt

## Overview
This setup adds Traefik as a reverse proxy with automatic TLS certificate management using Let's Encrypt and Cloudflare DNS challenge.

## What You Get
- ✅ Access app without port number: `https://dinner-menu.kcarterlabs.tech`
- ✅ Automatic HTTPS with Let's Encrypt certificates
- ✅ Auto-renewal of certificates
- ✅ HTTP to HTTPS redirect
- ✅ Cloudflare DNS-01 challenge (works behind NAT/firewalls)

## Setup Steps

### 1. Get Cloudflare API Credentials

#### Option A: API Token (Recommended)
1. Go to https://dash.cloudflare.com/profile/api-tokens
2. Click "Create Token"
3. Use "Edit zone DNS" template
4. Set permissions:
   - Zone > DNS > Edit
   - Zone > Zone > Read
5. Set Zone Resources: Include > Specific zone > kcarterlabs.tech
6. Copy the token

#### Option B: Global API Key
1. Go to https://dash.cloudflare.com/profile/api-tokens
2. Scroll to "API Keys"
3. View Global API Key
4. Copy your email and key

### 2. Configure Environment Variables

Copy the example file:
```bash
cp .env.prod.example .env.prod
```

Edit `.env.prod` with your values:
```bash
# Cloudflare credentials
CF_API_EMAIL=your-email@example.com
CF_API_KEY=your-cloudflare-global-api-key-or-token

# Let's Encrypt email
ACME_EMAIL=your-email@example.com

# Weather API
RAPID_API_FORECAST_KEY=your-key

# ECR registry
ECR_REGISTRY=856817629634.dkr.ecr.us-west-2.amazonaws.com
```

### 3. DNS Configuration

In Cloudflare, ensure you have an A record:
```
Type: A
Name: dinner-menu
Content: 10.10.69.21 (your Docker host IP)
Proxy status: DNS only (grey cloud) - important for Let's Encrypt
TTL: Auto
```

### 4. Deploy

On your Docker host:
```bash
./deploy-traefik.sh
```

### 5. Verify

Check the logs:
```bash
docker logs dinner-menu-traefik
```

Look for:
```
[...] acme: Obtaining certificate...
[...] Domains ["dinner-menu.kcarterlabs.tech"] need ACME certificates generation for domains...
[...] acme: Authorization validated
[...] Server responded with a certificate.
```

Access your app:
- Frontend: https://dinner-menu.kcarterlabs.tech
- API: https://dinner-menu.kcarterlabs.tech/api/health

## Testing First

To test without hitting Let's Encrypt rate limits, uncomment this line in `docker-compose.prod.yml`:
```yaml
# - "--certificatesresolvers.cloudflare.acme.caserver=https://acme-staging-v02.api.letsencrypt.org/directory"
```

This uses Let's Encrypt staging server. The certificate won't be trusted by browsers, but you can verify the process works.

## Troubleshooting

### Certificate not obtained
1. Check Traefik logs: `docker logs dinner-menu-traefik`
2. Verify Cloudflare credentials are correct
3. Ensure DNS record exists and is not proxied (grey cloud)
4. Check firewall allows DNS queries (port 53)

### 502 Bad Gateway
- Check backend containers are running: `docker ps`
- Check backend logs: `docker logs dinner-menu-frontend`

### Certificate renewal
- Traefik automatically renews certificates 30 days before expiry
- Certificates are stored in `./letsencrypt/acme.json`
- Backup this file to preserve certificates

## Architecture

```
Internet
    ↓
Traefik (:80, :443)
    ↓
    ├── dinner-menu.kcarterlabs.tech → Frontend (:8501)
    └── dinner-menu.kcarterlabs.tech/api → API (:5000)
```

## Security Notes

1. **Traefik Dashboard**: Currently exposed on port 8080. In production, either:
   - Remove port mapping
   - Add basic auth (see commented labels in docker-compose.prod.yml)
   - Access via subdomain with auth

2. **API Key Storage**: Never commit `.env.prod` to git

3. **Certificate Storage**: `letsencrypt/acme.json` should be backed up but not committed

## Files Created

- `docker-compose.prod.yml` - Production docker-compose with Traefik
- `.env.prod.example` - Example environment variables
- `deploy-traefik.sh` - Deployment script
- `.env.prod` - Your actual credentials (create this, don't commit)
