interface AlertProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'info' | 'warning' | 'error' | 'success'
  title?: string
  children: React.ReactNode
}

export function Alert({ variant = 'info', title, children, className, ...props }: AlertProps) {
  const variants = {
    info: {
      bg: 'bg-blue-50',
      border: 'border-blue-200',
      text: 'text-blue-800',
      title: 'text-blue-900',
    },
    warning: {
      bg: 'bg-yellow-50',
      border: 'border-yellow-200',
      text: 'text-yellow-800',
      title: 'text-yellow-900',
    },
    error: {
      bg: 'bg-red-50',
      border: 'border-red-200',
      text: 'text-red-800',
      title: 'text-red-900',
    },
    success: {
      bg: 'bg-green-50',
      border: 'border-green-200',
      text: 'text-green-800',
      title: 'text-green-900',
    },
  }

  const styles = variants[variant]

  return (
    <div
      className={`${styles.bg} border ${styles.border} rounded-lg p-4 ${styles.text} ${className ?? ''}`}
      {...props}
    >
      {title && <h4 className={`font-semibold ${styles.title} mb-1`}>{title}</h4>}
      <div className="text-sm">{children}</div>
    </div>
  )
}
