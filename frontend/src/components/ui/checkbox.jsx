import * as React from "react"

const Checkbox = React.forwardRef(({ className, checked, onChange, ...props }, ref) => {
  return (
    <div className="relative inline-flex items-center">
      <input
        type="checkbox"
        ref={ref}
        checked={checked}
        onChange={(e) => onChange?.(e.target.checked)}
        className={`
          peer h-4 w-4 shrink-0 rounded-sm border border-primary
          ring-offset-background focus-visible:outline-none focus-visible:ring-2 
          focus-visible:ring-ring focus-visible:ring-offset-2 
          disabled:cursor-not-allowed disabled:opacity-50
          ${checked ? 'bg-primary text-primary-foreground' : 'bg-white'}
          ${className}
        `}
        {...props}
      />
      <div className={`
        pointer-events-none absolute inset-0 hidden h-4 w-4 
        ${checked ? 'flex items-center justify-center' : ''}
      `}>
        {checked && (
          <svg
            className="h-3 w-3 text-white"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="3"
          >
            <polyline points="20 6 9 17 4 12" />
          </svg>
        )}
      </div>
    </div>
  )
})

Checkbox.displayName = "Checkbox"

export { Checkbox }
