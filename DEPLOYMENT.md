# Deployment Guide - Streamlit Cloud

## Deploy Your Fantasy League for Remote Access (FREE)

This guide will help you deploy your Unrivaled Fantasy League to Streamlit Cloud so your 8 managers can access it from anywhere, not just your local WiFi.

---

## Prerequisites

- GitHub account (free): [github.com/signup](https://github.com/signup)
- Git installed on your computer
- Your league data ready in `data/handmade/managers.csv`

---

## Step 1: Prepare Your Repository

### 1.1 Create Required Files

**Create `.gitignore`** to exclude temporary files:

```bash
cd unrivaled
cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
.venv

# Streamlit
.streamlit/secrets.toml

# OS
.DS_Store
Thumbs.db

# IDE
.vscode/
.idea/
*.swp
*.swo

# Don't ignore data files - we want them in git for Streamlit Cloud
# !data/
EOF
```

**Create `requirements.txt`** (Streamlit Cloud needs this instead of pyproject.toml):

```bash
cat > requirements.txt << 'EOF'
streamlit>=1.30.0
pandas>=2.1.0
plotly>=5.18.0
EOF
```

### 1.2 Update README for Deployment

Add deployment badge and live URL placeholder to your README:

```bash
cat >> README.md << 'EOF'

---

## Live Deployment

Access the league: **[Add your Streamlit Cloud URL here after deployment]**

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](your-url-here)
EOF
```

---

## Step 2: Push to GitHub

### 2.1 Initialize Git Repository

```bash
cd unrivaled

# Initialize git
git init

# Add all files
git add .

# Create first commit
git commit -m "Initial commit - Unrivaled Fantasy League Season 2"

# Set main branch
git branch -M main
```

### 2.2 Create GitHub Repository

1. Go to [github.com/new](https://github.com/new)
2. Repository name: `unrivaled-fantasy-league` (or your choice)
3. Description: `Fantasy basketball league for Unrivaled Season 2`
4. **Keep it PUBLIC** (required for free Streamlit Cloud tier)
5. **Do NOT** initialize with README, .gitignore, or license (we already have these)
6. Click "Create repository"

### 2.3 Push Code to GitHub

GitHub will show you commands. Use these (replace `YOUR_USERNAME`):

```bash
git remote add origin https://github.com/YOUR_USERNAME/unrivaled-fantasy-league.git
git push -u origin main
```

**Troubleshooting**: If you get authentication errors, you may need to:
- Use a [Personal Access Token](https://github.com/settings/tokens) instead of password
- Or set up [SSH keys](https://docs.github.com/en/authentication/connecting-to-github-with-ssh)

---

## Step 3: Deploy to Streamlit Cloud

### 3.1 Sign Up for Streamlit Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Click "Sign up" or "Continue with GitHub"
3. Authorize Streamlit Cloud to access your GitHub repositories

### 3.2 Deploy Your App

1. Click "New app" button
2. Fill in the form:
   - **Repository**: `YOUR_USERNAME/unrivaled-fantasy-league`
   - **Branch**: `main`
   - **Main file path**: `app/streamlit_app.py`
   - **App URL**: Choose a custom subdomain (e.g., `unrivaled-fantasy-2026`)
3. Click "Deploy!"

**Deployment takes 2-5 minutes**. You'll see logs as it builds.

### 3.3 Your App is Live!

Once deployed, you'll get a URL like:
```
https://unrivaled-fantasy-2026.streamlit.app
```

**Share this URL with your 8 managers!**

---

## Step 4: Managing Data Updates

### How to Update Data (Scores, Lineups, etc.)

Since your data is stored in CSV files tracked by git, you have two options:

#### **Option A: Edit on GitHub (Easiest)**

1. Go to your repository on GitHub
2. Navigate to the file (e.g., `data/source/game_stats/2026-01-05_game1.csv`)
3. Click the pencil icon (Edit)
4. Make your changes
5. Click "Commit changes"
6. **Streamlit Cloud auto-updates within 1 minute!**

**Use this for**:
- Uploading new game stats
- Updating player injury status
- Quick fixes

#### **Option B: Push from Your Computer**

After making changes locally:

```bash
cd unrivaled

# Add changed files
git add data/

# Commit with a message
git commit -m "Add game stats for Jan 5, 2026"

# Push to GitHub
git push origin main
```

Streamlit Cloud will automatically redeploy within 1 minute.

---

## Step 5: Running Your League

### Before Season Starts (Before Jan 5)

1. **Update managers.csv** with real manager names and team names
2. **Push to GitHub**: `git add data/ && git commit -m "Add real managers" && git push`
3. **Share the app URL** with all 8 managers
4. **Run the draft together**:
   - One person (admin) uses Admin Portal → Run Draft
   - Everyone watches on their devices
   - Or run draft locally first, then push results to GitHub

### During the Season (Jan 5 - Feb 27)

**After Each Game Day:**

1. **Collect game stats** (from Unrivaled website, box scores, etc.)
2. **Format as CSV** (see `data/source/game_stats/example_game_stats.csv`)
3. **Upload via Admin Portal**:
   - Go to your app URL
   - Admin Portal → Upload Stats
   - Select CSV file
   - Pick game date
   - Click "Save Stats and Calculate Scores"
4. **Scores update automatically** for all managers

**Managers Set Lineups:**
- Visit the app URL on any device
- Manager Portal → Set Lineup
- Select 3 active players
- Save before lineup lock (first game time of the day)

---

## Step 6: Important Settings & Tips

### Data Persistence

**Good News**: CSV files in your GitHub repo are persistent. When Streamlit Cloud restarts:
- All uploaded stats remain
- All lineups remain
- All scores remain

**Important**: Since data is in git, you can always:
- Roll back to previous versions
- See history of all changes
- Clone to your computer for backup

### Resource Limits (Free Tier)

Streamlit Cloud free tier includes:
- Unlimited public apps
- 1 GB RAM
- 1 CPU core
- Sleeps after 7 days of inactivity (wakes up instantly when visited)

**Your league should be fine** - you have 8 users, simple CSV operations, not computationally intensive.

### Privacy Considerations

**Your repository is PUBLIC** (required for free tier). This means:
- Anyone can see your code
- Anyone can see your data files (manager names, scores, etc.)

If you need privacy:
- Upgrade to Streamlit Cloud for Teams ($250/year) for private repos
- Or use alternative deployment (Heroku, Railway, etc.)

For most fantasy leagues, public is fine - it's just your friends' fantasy scores!

### Auto-Sleep & Wake-Up

Free apps sleep after 7 days of no visitors. When someone visits:
- App wakes up in ~10 seconds
- All data intact
- No action needed

**Tip**: During the season (Jan-Feb), there will be daily activity, so no sleeping.

---

## Step 7: Updating Your App Code

If you need to fix bugs or add features:

```bash
# Make your code changes locally
# Test locally: uv run streamlit run app/streamlit_app.py

# Commit and push
git add .
git commit -m "Fix bug in lineup validation"
git push origin main
```

Streamlit Cloud redeploys automatically within 1 minute.

---

## Alternative: Quick Testing with ngrok

If you just want to test with your league before full deployment:

```bash
# Terminal 1: Run app
cd unrivaled
uv run streamlit run app/streamlit_app.py

# Terminal 2: Expose to internet
brew install ngrok
ngrok http 8501
```

Share the ngrok URL (e.g., `https://abc123.ngrok.io`).

**Limitations:**
- URL changes each restart
- Your computer must stay on
- Only for testing, not production

---

## Troubleshooting

### "Module not found" errors
- Make sure `requirements.txt` exists with all dependencies
- Check Streamlit Cloud logs for exact error
- Redeploy if needed

### Data not updating
- Check you pushed to GitHub: `git push origin main`
- Check Streamlit Cloud logs for errors
- Hard refresh browser: Cmd+Shift+R (Mac) or Ctrl+Shift+R (Windows)

### App won't deploy
- Verify main file path is `app/streamlit_app.py` (not just `streamlit_app.py`)
- Check repository is public
- Look at error logs in Streamlit Cloud dashboard

### Changes not reflecting
- Wait 60 seconds after pushing to GitHub
- Click "Reboot app" in Streamlit Cloud settings if needed
- Clear browser cache

---

## Support Resources

- **Streamlit Cloud Docs**: [docs.streamlit.io/streamlit-community-cloud](https://docs.streamlit.io/streamlit-community-cloud)
- **GitHub Help**: [docs.github.com](https://docs.github.com)
- **This League's Issues**: See `ISSUES_AND_AUTOMATION.md`

---

## Quick Reference: Common Tasks

| Task | Command |
|------|---------|
| Update game stats | Edit file on GitHub OR push from computer |
| Fix a bug | Edit code locally → `git push origin main` |
| View logs | Streamlit Cloud dashboard → Your app → Logs |
| Reboot app | Streamlit Cloud dashboard → Manage app → Reboot |
| Change URL | Streamlit Cloud dashboard → Settings → General |
| Add collaborators | GitHub repo → Settings → Collaborators |

---

## Next Steps

1. ✅ Create `requirements.txt` and `.gitignore` (commands above)
2. ✅ Push to GitHub
3. ✅ Deploy to Streamlit Cloud
4. ✅ Test with a few managers
5. ✅ Update `managers.csv` with real names
6. ✅ Run draft before Jan 5
7. ✅ Share URL with all 8 managers

Your league is ready to go live! 🏀
