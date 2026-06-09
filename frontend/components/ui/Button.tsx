import { cn } from '@/lib/utils'

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger'
  size?: 'sm' | 'md' | 'lg'
  isLoading?: boolean
  fullWidth?: boolean
  className?: string
}

export function Button({
  variant = 'primary',
  size = 'md',
  fullWidth = false,
  className,
  disabled,
  isLoading,
  children,
  ...props
}: ButtonProps) {
  const baseStyles =
    'font-medium rounded-lg transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-black disabled:opacity-50 disabled:cursor-not-allowed'

  const variants = {
    primary: 'bg-black text-white hover:bg-gray-800 focus:ring-offset-white',
    secondary:
      'bg-gray-200 text-black hover:bg-gray-300 focus:ring-offset-white',
    ghost:
      'text-black hover:bg-gray-100 focus:ring-offset-white border border-gray-200',
    danger: 'bg-red-600 text-white hover:bg-red-700 focus:ring-offset-white',
  }

  const sizes = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2.5 text-base',
    lg: 'px-6 py-3 text-lg',
  }

  return (
    <button
      className={cn(baseStyles, variants[variant], sizes[size], fullWidth && 'w-full', className)}
      disabled={disabled || isLoading}
      {...props}
    >
      {isLoading ? (
        <span className="flex items-center gap-2">
          <span className="animate-spin">⟳</span>
          {children}
        </span>
      ) : (
        children
      )}
    </button>
  )
}
