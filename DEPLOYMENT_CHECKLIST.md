# 🚀 Render Deployment Checklist

## Pre-Deployment Preparation

### ✅ **Step 1: Data Backup**
- [ ] Run migration script to backup SQLite data
  ```bash
  python migrate_to_postgresql.py
  ```
- [ ] Verify backup file is created (`sqlite_export_*.json`)
- [ ] Keep backup file secure and accessible

### ✅ **Step 2: Environment Setup**
- [ ] Ensure all dependencies are in `requirements.txt`
- [ ] Test locally with PostgreSQL (optional but recommended)
- [ ] Verify OpenAI API key is ready

### ✅ **Step 3: Code Preparation**
- [ ] Commit all changes to GitHub
- [ ] Push to your repository: `https://github.com/scherkao31/dental-app`
- [ ] Verify all files are pushed correctly

## Render Deployment

### ✅ **Step 4: Create Render Account**
- [ ] Go to [render.com](https://render.com)
- [ ] Sign up/login with GitHub account
- [ ] Connect your GitHub repository

### ✅ **Step 5: Deploy PostgreSQL Database**
- [ ] In Render Dashboard, click "New" → "PostgreSQL"
- [ ] Configure database:
  - **Name**: `dental-ai-db`
  - **Database**: `dental_ai_production`
  - **User**: `dental_ai_user`
  - **Plan**: Starter ($7/month)
- [ ] Click "Create Database"
- [ ] Wait for database to be ready (green status)
- [ ] Copy the **Internal Database URL**

### ✅ **Step 6: Deploy Web Service**
- [ ] In Render Dashboard, click "New" → "Web Service"
- [ ] Connect your GitHub repository: `scherkao31/dental-app`
- [ ] Configure web service:
  - **Name**: `dental-ai-app`
  - **Runtime**: `Python 3`
  - **Build Command**: `pip install -r requirements.txt`
  - **Start Command**: `gunicorn --bind 0.0.0.0:$PORT app:app`
  - **Plan**: Starter ($7/month)

### ✅ **Step 7: Environment Variables**
Set these environment variables in Render:
- [ ] `OPENAI_API_KEY` = `your_openai_api_key`
- [ ] `DATABASE_URL` = `postgresql://...` (from Step 5)
- [ ] `FLASK_ENV` = `production`
- [ ] `RENDER` = `true`

### ✅ **Step 8: Deploy**
- [ ] Click "Create Web Service"
- [ ] Wait for deployment to complete (10-15 minutes)
- [ ] Check deployment logs for errors

## Post-Deployment

### ✅ **Step 9: Verify Deployment**
- [ ] Visit your Render app URL
- [ ] Check `/health` endpoint works
- [ ] Verify database connection is working
- [ ] Test basic functionality

### ✅ **Step 10: Data Restoration**
- [ ] Access Render Shell or use deployment script
- [ ] Run the generated restore script:
  ```bash
  python restore_postgresql_*.py
  ```
- [ ] Verify data was restored correctly

### ✅ **Step 11: Final Testing**
- [ ] Test all major features:
  - [ ] Patient management
  - [ ] Appointment scheduling
  - [ ] Treatment planning
  - [ ] AI chat functionality
  - [ ] Document generation
- [ ] Verify vector database is working
- [ ] Test file uploads/downloads

## Troubleshooting

### Common Issues:
1. **Database connection errors**
   - Check DATABASE_URL format
   - Verify PostgreSQL service is running

2. **OpenAI API errors**
   - Verify API key is set correctly
   - Check API key has sufficient credits

3. **Vector database issues**
   - Check if ChromaDB directory is writable
   - Verify sentence-transformers model downloads

4. **Memory issues**
   - Consider upgrading to higher plan
   - Optimize vector database size

### Support Resources:
- [Render Documentation](https://render.com/docs)
- [PostgreSQL on Render](https://render.com/docs/postgresql-creating-connecting)
- Check deployment logs in Render Dashboard

## Production Monitoring

### ✅ **Step 12: Set Up Monitoring**
- [ ] Configure health checks
- [ ] Set up email notifications
- [ ] Monitor resource usage
- [ ] Set up automatic backups

### ✅ **Step 13: Custom Domain (Optional)**
- [ ] Purchase domain
- [ ] Configure DNS settings
- [ ] Add custom domain in Render
- [ ] Set up SSL certificate

## Security Checklist

- [ ] All API keys are in environment variables
- [ ] Database credentials are secure
- [ ] Debug mode is disabled in production
- [ ] CORS is properly configured
- [ ] File uploads are validated

## Backup Strategy

- [ ] Schedule regular database backups
- [ ] Export vector database periodically
- [ ] Keep local backups of critical data
- [ ] Test restore procedures

---

## 🎉 Deployment Complete!

Your Dental AI application should now be running on Render at:
`https://your-app-name.onrender.com`

Remember to:
- Monitor performance and logs
- Keep dependencies updated
- Regularly backup your data
- Test new features in staging first 