import type * as React from "react"
import { Slot } from "@radix-ui/react-slot"
import { cva, type VariantProps } from "class-variance-authority"

import { cn } from "@/lib/utils"

const buttonVariants = cva(
  "inline-flex items-center justify-center whitespace-nowrap rounded-lg text-sm font-medium transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        default: "bg-gray-900 text-white shadow-md hover:bg-gray-800 hover:shadow-lg transform hover:scale-[1.02]",
        destructive: "bg-red-500 text-white shadow-md hover:bg-red-600 hover:shadow-lg transform hover:scale-[1.02]",
        outline:
          "border-2 border-gray-300 bg-transparent hover:bg-gray-50 hover:border-gray-400 text-gray-700 hover:text-gray-900",
        secondary: "bg-gray-100 text-gray-900 shadow-sm hover:bg-gray-200 hover:shadow-md transform hover:scale-[1.02]",
        ghost: "hover:bg-gray-100 hover:text-gray-900 transition-colors duration-200",
        link: "text-gray-900 underline-offset-4 hover:underline",
      },
      size: {
        default: "h-10 px-4 py-2",
        sm: "h-8 rounded-md px-3 text-xs",
        lg: "h-12 rounded-xl px-8 text-base",
        icon: "h-10 w-10",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  },
)

function Button({
  className,
  variant,
  size,
  asChild = false,
  ...props
}: React.ComponentProps<"button"> &
  VariantProps<typeof buttonVariants> & {
    asChild?: boolean
  }) {
  const Comp = asChild ? Slot : "button"

  return <Comp data-slot="button" className={cn(buttonVariants({ variant, size, className }))} {...props} />
}

export { Button, buttonVariants }
