import * as React from 'react'
import { cn } from '@/lib/utils'

export interface InputProps
  extends React.InputHTMLAttributes<HTMLInputElement> {
  icon?: React.ReactNode
}

const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, type, icon, ...props }, ref) => {
    return (
      <div className="relative">
        {icon && (
          <div className="absolute left-4 top-1/2 -translate-y-1/2 text-text-secondary">
            {icon}
          </div>
        )}
        <input
          type={type}
          className={cn(
            'flex w-full min-h-btn rounded-pos border-2 border-border bg-surface px-4 py-3 text-pos-base text-text-primary',
            'placeholder:text-text-secondary',
            'focus:outline-none focus:border-primary focus:ring-4 focus:ring-primary/20',
            'disabled:cursor-not-allowed disabled:opacity-50',
            icon && 'pl-12',
            className
          )}
          ref={ref}
          {...props}
        />
      </div>
    )
  }
)
Input.displayName = 'Input'

export { Input }
