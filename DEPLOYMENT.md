# 🚀 ARBTRONX Railway Deployment Guide

## 📋 Environment Variables Required

Add these environment variables in Railway dashboard:

```
BINANCE_API_KEY=ZETdLJmOxVNd6JqoCP5eGOUagRlv68yKcyW8ouaxVmBg9yIeflakSXoCXNm2LLDt
BINANCE_SECRET_KEY=ax9aDcjPZEzpIVMLapUnZRqjt8CJlcPBDO2X9LGJp3uPC2lmXBO5McUj0mHIUhQb
BINANCE_SANDBOX=false
USER_NAME=Ibrahim Razzan
USER_EMAIL=raxxex@gmail.com
USER_ID=76bfd673
PORT=8006
```

## 🌐 Deployment Steps

### 1. Push to GitHub
```bash
git init
git add .
git commit -m "Initial ARBTRONX deployment"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/arbtronx.git
git push -u origin main
```

### 2. Deploy to Railway
1. Go to https://railway.app
2. Sign up with GitHub
3. Click "New Project" → "Deploy from GitHub repo"
4. Select your ARBTRONX repository
5. Add environment variables from above
6. Deploy automatically!

### 3. Access Your Live Dashboard
- Railway will provide a URL like: `https://arbtronx-production.up.railway.app`
- Health check: `https://your-url.railway.app/health`

## 🔧 Custom Domain (Optional)
1. In Railway dashboard → Settings → Domains
2. Add your custom domain (e.g., arbtronx.com)
3. Update DNS records as shown
4. Get automatic HTTPS

## 📊 Monitoring
- Railway provides built-in metrics
- Health check endpoint: `/health`
- Logs available in Railway dashboard

## 💰 Pricing
- Free tier: Limited hours
- Hobby plan: $5/month (recommended)
- Pro plan: $20/month (for scaling)
