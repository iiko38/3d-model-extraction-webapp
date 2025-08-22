# 3D Model Library Webapp

A modern web application for managing 3D model files with beautiful UI built with Next.js, Supabase, and shadcn/ui.

## Features

- 📁 **File Management** - View and manage 3D model files
- 🃏 **Product Cards** - Beautiful card-based product display
- 📊 **Statistics Dashboard** - Analytics and insights
- 🎨 **Modern UI** - Built with shadcn/ui components
- 📱 **Responsive Design** - Works on all devices
- 🔗 **Real-time Data** - Connected to Supabase database

## Tech Stack

- **Framework:** Next.js 14
- **Database:** Supabase
- **UI Components:** shadcn/ui
- **Styling:** Tailwind CSS
- **Language:** TypeScript

## Getting Started

1. **Clone the repository**
2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Set up environment variables:**
   ```bash
   cp .env.example .env.local
   ```
   Then add your Supabase credentials to `.env.local`

4. **Run the development server:**
   ```bash
   npm run dev
   ```

5. **Open [http://localhost:3000](http://localhost:3000)**

## Deployment

This app is configured for deployment on Vercel. Simply connect your GitHub repository to Vercel and add your environment variables in the Vercel dashboard.

## Pages

- **Home (`/`)** - File table view
- **Cards (`/cards`)** - Product card grid
- **Stats (`/stats`)** - Analytics dashboard

## Environment Variables

- `NEXT_PUBLIC_SUPABASE_URL` - Your Supabase project URL
- `NEXT_PUBLIC_SUPABASE_ANON_KEY` - Your Supabase anonymous key
