# 🚀 Next.js Setup Guide

## **Step 1: Verify Node.js Installation**

After installing Node.js, you need to restart your terminal or add it to PATH.

### **Option A: Restart Terminal**
1. Close your current PowerShell/Command Prompt
2. Open a new PowerShell/Command Prompt
3. Try: `node --version`

### **Option B: Manual PATH Setup**
1. Find where Node.js was installed (usually `C:\Program Files\nodejs\`)
2. Add to PATH environment variable
3. Restart terminal

## **Step 2: Install Dependencies**

Once Node.js is working:

```bash
cd webapp
npm install
```

## **Step 3: Environment Variables**

Create `.env.local` file in the `webapp` directory:

```bash
NEXT_PUBLIC_SUPABASE_URL=https://jcmnuxlusnfhusbulhag.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImpjbW51eGx1c25maHVzYnVsaGFnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTU4NjY0NDQsImV4cCI6MjA3MTQ0MjQ0NH0.OktEF3rXOxvJcy5PZj52xGezQYKvUG-S9R5Vfb-HNwI
```

## **Step 4: Run Development Server**

```bash
npm run dev
```

## **Step 5: Deploy to Vercel**

```bash
npm install -g vercel
vercel --prod
```

## **Troubleshooting**

### **Node.js not found:**
- Restart terminal after installation
- Check PATH environment variable
- Reinstall Node.js if needed

### **npm install fails:**
- Clear npm cache: `npm cache clean --force`
- Delete `node_modules` and `package-lock.json`
- Run `npm install` again

### **Build errors:**
- Check TypeScript errors
- Verify environment variables
- Check Supabase connection
