# Deployment Guide - Hosting Options

## 🏆 Recommended Options (Easiest & Cheapest)

### Option 1: Railway (Recommended - Easiest) ⭐
**Cost:** Free tier (500 hours/month), then ~$5-10/month
**Pros:** 
- ✅ Automatic deployments from GitHub
- ✅ Free SSL/HTTPS included
- ✅ Easy environment variable setup
- ✅ Persistent storage for ChromaDB
- ✅ One-click deploy
- ✅ No credit card needed for free tier

**Setup:**
1. Go to: https://railway.app
2. Sign up with GitHub
3. Click "New Project" → "Deploy from GitHub repo"
4. Select `evonow/twilio-chatbot`
5. Add environment variables:
   - `OPENAI_API_KEY`
   - `TWILIO_ACCOUNT_SID`
   - `TWILIO_AUTH_TOKEN`
   - `TWILIO_PHONE_NUMBER`
   - `FLASK_DEBUG=false` (for production)
6. Railway will auto-deploy and give you a URL
7. Update Twilio webhook to: `https://your-app.railway.app/sms`

### Option 2: Render (Free Tier Available)
**Cost:** Free tier (spins down after inactivity), $7/month for always-on
**Pros:**
- ✅ Free tier available
- ✅ Automatic HTTPS
- ✅ GitHub integration
- ✅ Easy setup

**Setup:**
1. Go to: https://render.com
2. Sign up with GitHub
3. Click "New" → "Web Service"
4. Connect your GitHub repo: `evonow/twilio-chatbot`
5. Settings:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python3 web_app.py`
   - Environment: Python 3
6. Add environment variables (same as Railway)
7. Deploy → Get URL → Update Twilio webhook

### Option 3: Fly.io (Very Cheap)
**Cost:** Free tier (3 shared VMs), then pay-as-you-go (~$2-5/month)
**Pros:**
- ✅ Generous free tier
- ✅ Global edge deployment
- ✅ Persistent volumes for ChromaDB
- ✅ Great for production

**Setup:**
1. Install Fly CLI: `brew install flyctl`
2. Sign up: `flyctl auth signup`
3. In project directory: `flyctl launch`
4. Follow prompts, add environment variables
5. Deploy: `flyctl deploy`
6. Get URL and update Twilio webhook

### Option 4: DigitalOcean App Platform
**Cost:** $5/month (Basic plan)
**Pros:**
- ✅ Predictable pricing
- ✅ Reliable infrastructure
- ✅ Easy scaling
- ✅ Persistent storage

**Setup:**
1. Go to: https://cloud.digitalocean.com/apps
2. Create App → GitHub → Select repo
3. Configure:
   - Build: `pip install -r requirements.txt`
   - Run: `python3 web_app.py`
4. Add environment variables
5. Deploy → Get URL

## 📋 Pre-Deployment Checklist

### Environment Variables Needed
- `OPENAI_API_KEY` - Your OpenAI API key
- `TWILIO_ACCOUNT_SID` - Twilio Account SID
- `TWILIO_AUTH_TOKEN` - Twilio Auth Token
- `TWILIO_PHONE_NUMBER` - Your Twilio number (+1234567890)
- `PORT` - Usually auto-set by platform
- `FLASK_DEBUG` - Set to `false` for production

### Persistent Storage
- ChromaDB needs persistent storage
- Most platforms support volumes/mounts
- Check platform docs for persistent storage setup

## 🚀 Quick Deploy Commands

### Railway
```bash
# Install Railway CLI (optional)
npm i -g @railway/cli

# Or just use web interface - it's easier!
```

### Render
- Use web interface (easiest)
- Or use Render CLI

### Fly.io
```bash
flyctl launch
flyctl deploy
```

## 💰 Cost Comparison

| Platform | Free Tier | Paid Tier | Best For |
|----------|-----------|-----------|----------|
| Railway | 500 hrs/month | $5-10/mo | ⭐ Easiest setup |
| Render | Limited | $7/mo | Simple deployments |
| Fly.io | 3 VMs | $2-5/mo | Production apps |
| DigitalOcean | None | $5/mo | Predictable costs |

## 🔒 Security Notes

- Never commit `.env` file (already in .gitignore)
- Use platform's secret management for environment variables
- Enable HTTPS (most platforms do this automatically)
- Keep dependencies updated
- Set `FLASK_DEBUG=false` in production

## 📝 After Deployment

1. Get your deployment URL (e.g., `https://your-app.railway.app`)
2. Update Twilio webhook:
   - Go to Twilio Console → Phone Numbers → Your Number
   - Set webhook to: `https://your-app.railway.app/sms`
   - Method: POST
3. Test by sending an SMS!

