# Production Deployment Guide - Gunicorn + Nginx

## Overview
This guide covers deploying the AI Timetable Generator with Gunicorn WSGI server behind Nginx reverse proxy.

## 📋 Prerequisites

- Ubuntu 20.04+ / Debian 11+ (or similar Linux distribution)
- Python 3.11+
- MongoDB Atlas account OR local MongoDB
- Domain name (for SSL)
- Root/sudo access

## 🚀 Deployment Options

### Option 1: Systemd Service (Traditional VPS)
### Option 2: Docker Compose (Containerized)
### Option 3: Vercel (Serverless) - Already configured

---

## Option 1: Systemd Service Deployment

### Step 1: System Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3.11 python3.11-venv python3-pip nginx git

# Create application user
sudo useradd -m -s /bin/bash www-data

# Create application directory
sudo mkdir -p /var/www/ai-timetable-generator
sudo chown www-data:www-data /var/www/ai-timetable-generator

# Create log directory
sudo mkdir -p /var/log/gunicorn
sudo chown www-data:www-data /var/log/gunicorn
```

### Step 2: Deploy Application

```bash
# Clone repository
cd /var/www/ai-timetable-generator
sudo -u www-data git clone https://github.com/RoshanJT5/AI-Timetable-Generator.git .

# Create virtual environment
sudo -u www-data python3.11 -m venv venv

# Activate and install dependencies
sudo -u www-data venv/bin/pip install --upgrade pip
sudo -u www-data venv/bin/pip install -r requirements.txt
```

### Step 3: Configure Environment

```bash
# Create .env file
sudo -u www-data nano .env
```

Add the following:
```env
MONGO_URI=your_mongodb_atlas_connection_string
MONGO_DBNAME=timetable
SECRET_KEY=your_very_secure_random_secret_key_here
GUNICORN_WORKERS=5
GUNICORN_THREADS=4
GUNICORN_BIND=127.0.0.1:5000
```

### Step 4: Install Systemd Service

```bash
# Copy service file
sudo cp ai-timetable.service /etc/systemd/system/

# Edit service file with correct paths
sudo nano /etc/systemd/system/ai-timetable.service

# Reload systemd
sudo systemctl daemon-reload

# Enable service
sudo systemctl enable ai-timetable

# Start service
sudo systemctl start ai-timetable

# Check status
sudo systemctl status ai-timetable
```

### Step 5: Configure Nginx

```bash
# Copy Nginx configuration
sudo cp nginx.conf /etc/nginx/sites-available/ai-timetable

# Edit configuration (update domain name)
sudo nano /etc/nginx/sites-available/ai-timetable

# Enable site
sudo ln -s /etc/nginx/sites-available/ai-timetable /etc/nginx/sites-enabled/

# Test Nginx configuration
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx
```

### Step 6: Setup SSL with Let's Encrypt

```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Obtain SSL certificate
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# Test auto-renewal
sudo certbot renew --dry-run
```

### Step 7: Verify Deployment

```bash
# Check Gunicorn is running
sudo systemctl status ai-timetable

# Check Nginx is running
sudo systemctl status nginx

# View Gunicorn logs
sudo journalctl -u ai-timetable -f

# View Nginx logs
sudo tail -f /var/log/nginx/ai-timetable-access.log
sudo tail -f /var/log/nginx/ai-timetable-error.log

# Test application
curl http://localhost:5000
curl https://your-domain.com
```

---

## Option 2: Docker Compose Deployment

### Step 1: Install Docker

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo apt install -y docker-compose

# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker
```

### Step 2: Clone and Configure

```bash
# Clone repository
git clone https://github.com/RoshanJT5/AI-Timetable-Generator.git
cd AI-Timetable-Generator

# Create .env file
cp .env.example .env
nano .env
```

### Step 3: Build and Run

```bash
# Build images
docker-compose build

# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Check status
docker-compose ps
```

### Step 4: Manage Services

```bash
# Stop services
docker-compose stop

# Restart services
docker-compose restart

# Update application
git pull
docker-compose build
docker-compose up -d

# View logs
docker-compose logs -f app
docker-compose logs -f nginx
docker-compose logs -f mongodb
```

---

## 🔧 Gunicorn Configuration

### Worker Calculation

```python
# Formula: (2 * CPU cores) + 1
workers = (multiprocessing.cpu_count() * 2) + 1

# Example:
# 2 CPU cores = 5 workers
# 4 CPU cores = 9 workers
# 8 CPU cores = 17 workers
```

### Worker Classes

| Worker Class | Use Case | Pros | Cons |
|-------------|----------|------|------|
| `sync` | CPU-bound | Simple, stable | Low concurrency |
| `gthread` | I/O-bound (RECOMMENDED) | Good balance | Moderate complexity |
| `gevent` | High concurrency | Very high concurrency | Requires gevent |
| `eventlet` | High concurrency | Very high concurrency | Requires eventlet |

### Performance Tuning

```python
# gunicorn_config.py
workers = 5  # Adjust based on CPU
threads = 4  # Threads per worker
worker_class = 'gthread'  # Recommended for Flask
timeout = 120  # Request timeout
keepalive = 5  # Keep-alive timeout
max_requests = 1000  # Restart worker after N requests
max_requests_jitter = 50  # Add randomness
```

---

## 📊 Monitoring

### System Monitoring

```bash
# Check Gunicorn workers
ps aux | grep gunicorn

# Monitor memory usage
watch -n 1 'ps aux | grep gunicorn | awk "{sum+=\$6} END {print sum/1024 \" MB\"}"'

# Monitor CPU usage
top -p $(pgrep -d',' -f gunicorn)

# Check open connections
ss -tunap | grep :5000
```

### Application Logs

```bash
# Systemd logs
sudo journalctl -u ai-timetable -f

# Gunicorn logs
sudo tail -f /var/log/gunicorn/ai-timetable.log
sudo tail -f /var/log/gunicorn/ai-timetable-access.log

# Nginx logs
sudo tail -f /var/log/nginx/ai-timetable-access.log
sudo tail -f /var/log/nginx/ai-timetable-error.log
```

### Performance Metrics

```bash
# Request rate
tail -f /var/log/nginx/ai-timetable-access.log | pv -l -i 1 > /dev/null

# Response times
tail -f /var/log/nginx/ai-timetable-access.log | awk '{print $NF}' | stats

# Error rate
tail -f /var/log/nginx/ai-timetable-access.log | grep -E ' (4|5)[0-9]{2} '
```

---

## 🔒 Security Checklist

- [ ] SSL/TLS enabled (HTTPS)
- [ ] Firewall configured (ufw/iptables)
- [ ] SSH key authentication only
- [ ] Non-root user for application
- [ ] Environment variables secured
- [ ] Database authentication enabled
- [ ] Rate limiting configured
- [ ] Security headers enabled
- [ ] Regular updates scheduled
- [ ] Backups configured

---

## 🚨 Troubleshooting

### Gunicorn won't start

```bash
# Check logs
sudo journalctl -u ai-timetable -n 50

# Test manually
cd /var/www/ai-timetable-generator
sudo -u www-data venv/bin/gunicorn -c gunicorn_config.py app_with_navigation:app

# Check permissions
ls -la /var/www/ai-timetable-generator
```

### Nginx 502 Bad Gateway

```bash
# Check Gunicorn is running
sudo systemctl status ai-timetable

# Check Gunicorn is listening
sudo ss -tulpn | grep :5000

# Check Nginx error log
sudo tail -f /var/log/nginx/error.log
```

### High Memory Usage

```bash
# Reduce workers
# Edit gunicorn_config.py
workers = 3  # Reduce from 5

# Restart service
sudo systemctl restart ai-timetable

# Enable max_requests to prevent memory leaks
max_requests = 500
max_requests_jitter = 50
```

### Slow Response Times

```bash
# Increase workers
workers = 9  # Increase from 5

# Increase threads
threads = 8  # Increase from 4

# Check database performance
# Monitor MongoDB Atlas metrics

# Enable caching (Redis)
# Add Redis caching layer
```

---

## 📦 Maintenance

### Update Application

```bash
# Systemd deployment
cd /var/www/ai-timetable-generator
sudo -u www-data git pull
sudo -u www-data venv/bin/pip install -r requirements.txt
sudo systemctl restart ai-timetable

# Docker deployment
cd AI-Timetable-Generator
git pull
docker-compose build
docker-compose up -d
```

### Backup Database

```bash
# MongoDB Atlas: Use Atlas backup features

# Local MongoDB
docker exec ai-timetable-mongodb mongodump --out /backup
docker cp ai-timetable-mongodb:/backup ./backup-$(date +%Y%m%d)
```

### Log Rotation

```bash
# Create logrotate config
sudo nano /etc/logrotate.d/ai-timetable
```

```
/var/log/gunicorn/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 www-data www-data
    sharedscripts
    postrotate
        systemctl reload ai-timetable > /dev/null 2>&1 || true
    endscript
}
```

---

## 🎯 Performance Optimization

### 1. Enable HTTP/2
Already enabled in nginx.conf

### 2. Enable Gzip Compression
Already enabled in nginx.conf

### 3. Add Caching Headers
```nginx
location /static/ {
    expires 30d;
    add_header Cache-Control "public, immutable";
}
```

### 4. Use CDN
- CloudFlare
- AWS CloudFront
- Fastly

### 5. Database Optimization
- Index frequently queried fields
- Use MongoDB Atlas auto-scaling
- Enable connection pooling

---

## 📞 Support

For issues:
1. Check logs first
2. Review this guide
3. Check GitHub issues
4. Create new issue with logs

**Repository**: https://github.com/RoshanJT5/AI-Timetable-Generator
