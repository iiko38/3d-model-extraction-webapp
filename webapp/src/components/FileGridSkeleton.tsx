import { Skeleton } from '@/components/ui/skeleton'
import { layout } from '@/lib/design-tokens'

export default function FileGridSkeleton() {
  return (
    <div 
      className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-5"
      style={{ gap: layout['grid-gap'] }}
    >
      {Array.from({ length: 6 }).map((_, index) => (
        <div key={index} className="space-y-3">
          {/* Thumbnail skeleton */}
          <Skeleton className="aspect-square w-full rounded-xl" />
          
          {/* Content skeleton */}
          <div className="space-y-2 px-4" style={{ paddingLeft: layout['card-padding'], paddingRight: layout['card-padding'] }}>
            <Skeleton className="h-4 w-3/4" />
            <Skeleton className="h-3 w-1/2" />
          </div>
        </div>
      ))}
    </div>
  )
}
