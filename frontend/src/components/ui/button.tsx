import * as React from 'react'
import { Slot } from '@radix-ui/react-slot'
import { cva, type VariantProps } from 'class-variance-authority'
import { cn } from '@/lib/utils'

const buttonVariants = cva(
  'inline-flex items-center justify-center whitespace-nowrap rounded-pos font-semibold transition-all duration-200 focus-visible:outline-none focus-visible:ring-4 disabled:pointer-events-none disabled:opacity-50 active:scale-95',
  {
    variants: {
      variant: {
        default: 'bg-primary text-white hover:bg-primary-dark focus-visible:ring-primary/30',
        success: 'bg-success text-white hover:bg-success-dark focus-visible:ring-success/30',
        warning: 'bg-warning text-white hover:bg-warning-dark focus-visible:ring-warning/30',
        danger: 'bg-danger text-white hover:bg-danger-dark focus-visible:ring-danger/30',
        outline: 'border-2 border-border bg-transparent hover:bg-gray-100 focus-visible:ring-gray-300/30',
        ghost: 'hover:bg-gray-100 focus-visible:ring-gray-300/30',
        link: 'text-primary underline-offset-4 hover:underline',
      },
      size: {
        default: 'min-h-btn px-6 py-3 text-pos-base',
        sm: 'h-10 px-4 py-2 text-sm',
        lg: 'min-h-btn-lg px-8 py-4 text-pos-lg',
        xl: 'min-h-btn-xl px-10 py-5 text-pos-xl',
        icon: 'h-12 w-12',
        'icon-lg': 'h-16 w-16',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'default',
    },
  }
)

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : 'button'
    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    )
  }
)
Button.displayName = 'Button'

export { Button, buttonVariants }
