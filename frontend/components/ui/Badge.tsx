interface BadgeProps {
  label: string
  variant?: 'default' | 'phishing' | 'safe' | 'warning'
}

export function Badge({ label, variant = 'default' }: BadgeProps) {
  const variants = {
    default: 'bg-gray-200 text-gray-800',
    phishing: 'bg-red-100 text-red-700',
    safe: 'bg-green-100 text-green-700',
    warning: 'bg-yellow-100 text-yellow-700',
  }

  return (
    <span
      className={`inline-block px-3 py-1 text-xs font-semibold rounded-full ${variants[variant]}`}
    >
      {label}
    </span>
  )
}
