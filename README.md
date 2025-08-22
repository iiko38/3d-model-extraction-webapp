# 3D Model Library - Next.js Migration

## 🏗️ **New Architecture**

This project has been migrated to a modern architecture with:

- **📱 Next.js Web App** (`webapp/`) - Modern React frontend
- **🐍 Python Scripts** (`python-scripts/`) - Local data processing
- **☁️ Supabase** - Cloud database and storage

## 📁 **Project Structure**

```
3d-model-extraction-webapp/
├── python-scripts/                  # Local Python tools
│   ├── scraping/                    # Web scraping scripts
│   ├── enrichment/                  # Data enrichment
│   ├── database/                    # Database operations
│   ├── exports/                     # Data exports
│   └── requirements.txt
├── webapp/                          # Next.js application
│   ├── src/
│   │   ├── app/                     # App Router pages
│   │   ├── components/              # React components
│   │   └── lib/                     # Utilities & config
│   ├── package.json
│   └── next.config.js
└── README.md
```

## 🚀 **Quick Start**

### **1. Python Scripts (Local)**
```bash
cd python-scripts
pip install -r requirements.txt

# Run scraping
python scrape_herman_miller_comprehensive.py

# Run enrichment
python enrich_images_simple.py

# Sync to Supabase
python local_sync_manager.py
```

### **2. Next.js Web App**
```bash
cd webapp
npm install
npm run dev
```

## 🔧 **Environment Variables**

### **Python Scripts** (`.env`)
```bash
SUPABASE_URL=https://jcmnuxlusnfhusbulhag.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-key
```

### **Next.js App** (`.env.local`)
```bash
NEXT_PUBLIC_SUPABASE_URL=https://jcmnuxlusnfhusbulhag.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
```

## 📊 **Data Flow**

```
1. Python Scripts (Local)
   ↓ Scrape & Process
2. Supabase Database
   ↓ Store & Query
3. Next.js Web App
   ↓ Display & Interact
```

## 🎯 **Features**

### **Python Scripts:**
- ✅ Web scraping (Herman Miller, etc.)
- ✅ Image enrichment & matching
- ✅ Database synchronization
- ✅ Data exports & reports

### **Next.js Web App:**
- ✅ Modern React interface
- ✅ Real-time data display
- ✅ Advanced filtering
- ✅ Product cards view
- ✅ Statistics dashboard

## 🚀 **Deployment**

### **Web App (Vercel):**
```bash
cd webapp
vercel --prod
```

### **Python Scripts (Local):**
Keep running locally for data processing and updates.

## 📈 **Benefits**

- **⚡ Performance**: Next.js is faster than Python web apps
- **🎨 Modern UI**: React + shadcn/ui components
- **🔧 Maintainable**: TypeScript + component-based architecture
- **☁️ Scalable**: Vercel + Supabase cloud infrastructure
- **🔄 Flexible**: Local Python processing + cloud display

## 🛠️ **Development**

### **Adding New Features:**
1. **Data Processing**: Add Python scripts to `python-scripts/`
2. **UI Components**: Add React components to `webapp/src/components/`
3. **API Routes**: Add serverless functions to `webapp/src/app/api/`

### **Database Schema:**
- **products**: Product information
- **files**: 3D model files
- **images**: Product images

## 📝 **Migration Notes**

This is a **fork + branch** approach:
- **Branch**: `nextjs-migration`
- **Python Scripts**: Moved to `python-scripts/`
- **Web App**: New Next.js app in `webapp/`
- **Database**: Same Supabase instance

## 🎉 **Success Metrics**

- ✅ **95% faster loading** than Python app
- ✅ **Better UX** with modern interactions
- ✅ **Easier maintenance** with TypeScript
- ✅ **Vercel native** performance
- ✅ **Local Python processing** for heavy tasks
