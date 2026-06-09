import React from 'react'
import { cn } from '@/lib/utils'

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string
  error?: string
  fullWidth?: boolean
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({
    label,
    error,
    fullWidth = false,
    className,
    ...props
  }: InputProps, ref) => {
    return (
      <div className={cn('flex flex-col gap-1.5', fullWidth && 'w-full')}>
        {label && (
          <label className="text-sm font-medium text-gray-700">{label}</label>
        )}
        <input
          className={cn(
            'px-4 py-2.5 border border-gray-300 rounded-lg text-black placeholder-gray-400 transition-all duration-200',
            'focus:outline-none focus:ring-2 focus:ring-black focus:border-black',
            'disabled:bg-gray-50 disabled:cursor-not-allowed',
            error && 'border-red-500 focus:ring-red-500',
            className
          )}
          ref={ref}
          {...props}
        />
        {error && <span className="text-sm text-red-600">{error}</span>}
      </div>
    )
  }
)

Input.displayName = 'Input'
