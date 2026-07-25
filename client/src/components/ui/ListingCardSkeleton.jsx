import { Skeleton } from './Skeleton'

export function ListingCardSkeleton() {
  return (
    <div className="flex flex-col border border-gray-100 dark:border-slate-800 rounded-lg overflow-hidden w-full bg-white dark:bg-slate-900 shadow-sm">
      {/* One large skeleton for the image */}
      <Skeleton className="h-48 w-full rounded-t-lg" />
      
      <div className="p-4">
        {/* A medium skeleton below it for the title */}
        <Skeleton className="h-6 w-3/4 mt-4" />
        
        {/* A small skeleton for the price */}
        <Skeleton className="h-5 w-1/2 mt-2" />
        
        {/* A row of small circular/rectangular skeletons for the amenities at the bottom */}
        <div className="flex gap-2 mt-4">
          <Skeleton className="h-6 w-8 rounded-md" />
          <Skeleton className="h-6 w-8 rounded-md" />
          <Skeleton className="h-6 w-8 rounded-md" />
          <Skeleton className="h-6 w-8 rounded-md" />
        </div>
      </div>
    </div>
  )
}