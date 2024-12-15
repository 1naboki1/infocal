import * as React from "react"

const buttonVariants = {
  default: "bg-gray-900 text-white hover:bg-gray-800",
  destructive: "bg-red-500 text-white hover:bg-red-600",
  outline: "border border-gray-200 bg-white hover:bg-gray-100",
  secondary: "bg-gray-100 text-gray-900 hover:bg-gray-200",
  ghost: "hover:bg-gray-100",
  link: "text-blue-500 underline-offset-4 hover:underline"
}

const buttonSizes = {
  default: "h-10 px-4 py-2",
  sm: "h-9 rounded-md px-3",
  lg: "h-11 rounded-md px-8",
  icon: "h-10 w-10"
}

const Button = React.forwardRef(({
  className,
  variant = "default",
  size = "default",
  ...props
}, ref) => {
  return (
    <button
      className={`
        inline-flex items-center justify-center rounded-md text-sm font-medium
        transition-colors focus-visible:outline-none focus-visible:ring-2
        focus-visible:ring-ring focus-visible:ring-offset-2 disabled:opacity-50
        disabled:pointer-events-none ring-offset-background
        ${buttonVariants[variant]}
        ${buttonSizes[size]}
        ${className}
      `}
      ref={ref}
      {...props}
    />
  )
})
Button.displayName = "Button"

export { Button }
