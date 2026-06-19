/**
 * 🔥 Button Component - Premium Design System
 * Nível: Enterprise SaaS (Linear, Notion, Stripe)
 */

'use client';

import React from 'react';
import { cn } from '@/lib/utils';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  isLoading?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
  fullWidth?: boolean;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({
    className,
    variant = 'primary',
    size = 'md',
    isLoading = false,
    leftIcon,
    rightIcon,
    fullWidth = false,
    children,
    disabled,
    ...props
  }, ref) => {
    const baseStyles = `
      inline-flex items-center justify-center gap-2
      font-semibold rounded-xl
      transition-all duration-200 ease-out
      focus:outline-none focus:ring-2 focus:ring-offset-2
      disabled:opacity-50 disabled:cursor-not-allowed
      active:scale-[0.98]
    `;

    const variants = {
      primary: `
        bg-gradient-to-r from-[#FF6B4A] to-[#FF8F7A]
        text-white shadow-lg shadow-[#FF6B4A]/25
        hover:shadow-xl hover:shadow-[#FF6B4A]/30
        hover:-translate-y-0.5
        focus:ring-[#FF6B4A]/50
      `,
      secondary: `
        bg-[#F6F9FC] text-[#1F2937]
        border border-[#E3E8EE]
        hover:bg-[#E3E8EE] hover:border-[#C9D2DC]
        focus:ring-[#C9D2DC]
      `,
      ghost: `
        bg-transparent text-[#6B7280]
        hover:bg-[#F6F9FC] hover:text-[#1F2937]
        focus:ring-[#E3E8EE]
      `,
      danger: `
        bg-gradient-to-r from-[#FF4444] to-[#FF6B6B]
        text-white shadow-lg shadow-[#FF4444]/25
        hover:shadow-xl hover:shadow-[#FF4444]/30
        hover:-translate-y-0.5
        focus:ring-[#FF4444]/50
      `,
    };

    const sizes = {
      sm: 'px-3 py-2 text-sm',
      md: 'px-5 py-2.5 text-sm',
      lg: 'px-6 py-3 text-base',
    };

    return (
      <button
        ref={ref}
        className={cn(
          baseStyles,
          variants[variant],
          sizes[size],
          fullWidth && 'w-full',
          isLoading && 'cursor-wait opacity-80',
          className
        )}
        disabled={disabled || isLoading}
        {...props}
      >
        {isLoading && (
          <svg
            className="animate-spin h-4 w-4"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
          >
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            />
          </svg>
        )}
        {!isLoading && leftIcon}
        {children}
        {!isLoading && rightIcon}
      </button>
    );
  }
);

Button.displayName = 'Button';

export default Button;
