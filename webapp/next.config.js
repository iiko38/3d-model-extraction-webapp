/** @type {import('next').NextConfig} */
const nextConfig = {
  images: {
    domains: ['jcmnuxlusnfhusbulhag.supabase.co'],
    unoptimized: true,
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 'jcmnuxlusnfhusbulhag.supabase.co',
        port: '',
        pathname: '/storage/v1/object/public/**',
      },
    ],
  },
}

module.exports = nextConfig
