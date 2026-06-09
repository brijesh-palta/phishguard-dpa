import * as React from 'react'
import { cn } from '@/lib/utils'

interface TextareaProps
  extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string
  error?: string
  fullWidth?: boolean
}

export const Textarea = React.forwardRef<HTMLTextAreaElement, TextareaProps>(
  (
    {
      label,
      error,
      fullWidth = false,
      className,
      ...props
    }: TextareaProps,
    ref
  ) => {
    return (
      <div className={cn('flex flex-col gap-1.5', fullWidth && 'w-full')}>
        {label && (
          <label className="text-sm font-medium text-gray-700">{label}</label>
        )}
        <textarea
          ref={ref}
          className={cn(
            'px-4 py-2.5 border border-gray-300 rounded-lg text-black placeholder-gray-400 transition-all duration-200 font-sans',
            'focus:outline-none focus:ring-2 focus:ring-black focus:border-black',
            'disabled:bg-gray-50 disabled:cursor-not-allowed',
            error && 'border-red-500 focus:ring-red-500',
            className
          )}
          {...props}
        />
        {error && <span className="text-sm text-red-600">{error}</span>}
      </div>
    )
  }
)

Textarea.displayName = 'Textarea'
