import * as React from "react"

const TooltipProvider = ({ children }) => {
  return <>{children}</>
}

const Tooltip = ({ children }) => {
  return <div>{children}</div>
}

const TooltipTrigger = React.forwardRef(({ className, ...props }, ref) => (
  <button
    ref={ref}
    className={`inline-flex items-center justify-center ${className}`}
    {...props}
  />
))
TooltipTrigger.displayName = "TooltipTrigger"

const TooltipContent = React.forwardRef(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={`
      z-50 px-3 py-1.5 text-sm text-gray-700 bg-white
      rounded-lg shadow-lg border border-gray-200
      animate-in fade-in-0 zoom-in-95
      ${className}
    `}
    {...props}
  />
))
TooltipContent.displayName = "TooltipContent"

export { Tooltip, TooltipTrigger, TooltipContent, TooltipProvider }
