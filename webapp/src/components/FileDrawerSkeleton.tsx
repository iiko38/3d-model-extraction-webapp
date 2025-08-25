import { Skeleton } from '@/components/ui/skeleton'
import { layout } from '@/lib/design-tokens'

export default function FileDrawerSkeleton() {
  return (
    <div className="space-y-6 p-6" style={{ padding: layout['card-padding'] }}>
      {/* Hero image skeleton */}
      <Skeleton className="aspect-square w-full rounded-2xl" />
      
      {/* Title skeleton */}
      <div className="space-y-2">
        <Skeleton className="h-6 w-3/4" />
        <Skeleton className="h-4 w-1/2" />
      </div>
      
      {/* Essentials pills skeleton */}
      <div className="flex flex-wrap gap-2">
        <Skeleton className="h-6 w-16 rounded-full" />
        <Skeleton className="h-6 w-20 rounded-full" />
        <Skeleton className="h-6 w-12 rounded-full" />
        <Skeleton className="h-6 w-14 rounded-full" />
      </div>
      
      {/* Primary actions skeleton */}
      <div className="flex gap-2">
        <Skeleton className="h-10 w-24" />
        <Skeleton className="h-10 w-20" />
        <Skeleton className="h-10 w-24" />
      </div>
      
      {/* Format switcher skeleton */}
      <div className="space-y-2">
        <Skeleton className="h-4 w-24" />
        <div className="flex gap-1">
          <Skeleton className="h-8 w-16 rounded-lg" />
          <Skeleton className="h-8 w-16 rounded-lg" />
          <Skeleton className="h-8 w-16 rounded-lg" />
        </div>
      </div>
      
      {/* Meta section skeleton */}
      <div className="space-y-3">
        <Skeleton className="h-4 w-16" />
        <div className="space-y-2">
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-3/4" />
          <Skeleton className="h-4 w-1/2" />
        </div>
      </div>
    </div>
  )
}
