import clsx from 'clsx'

export function cn(...classes: (string | undefined | null | false)[]): string {
  return clsx(...classes)
}
