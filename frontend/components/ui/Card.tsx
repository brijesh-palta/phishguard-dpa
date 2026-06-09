import { cn } from '@/lib/utils'

interface CardProps {
  className?: string
  children: React.ReactNode
}

export function Card({ className, children }: CardProps) {
  return (
    <div
      className={cn(
        'bg-white border border-gray-200 rounded-lg shadow-sm hover:shadow-md transition-shadow duration-200',
        className
      )}
    >
      {children}
    </div>
  )
}

export function CardHeader({
  className,
  children,
}: {
  className?: string
  children: React.ReactNode
}) {
  return (
    <div
      className={cn(
        'px-6 py-4 border-b border-gray-200 flex items-center justify-between',
        className
      )}
    >
      {children}
    </div>
  )
}

export function CardTitle({
  className,
  children,
}: {
  className?: string
  children: React.ReactNode
}) {
  return (
    <h3 className={cn('text-lg font-semibold text-black', className)}>
      {children}
    </h3>
  )
}

export function CardContent({
  className,
  children,
}: {
  className?: string
  children: React.ReactNode
}) {
  return <div className={cn('px-6 py-4', className)}>{children}</div>
}
