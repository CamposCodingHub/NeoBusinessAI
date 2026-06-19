/**
 * 🔥 Card Component - Premium Design System
 * Nível: Enterprise SaaS (Linear, Notion, Stripe)
 */

'use client';

import React from 'react';
import { cn } from '@/lib/utils';

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'elevated' | 'glass' | 'interactive';
  padding?: 'none' | 'sm' | 'md' | 'lg';
}

export const Card = React.forwardRef<HTMLDivElement, CardProps>(
  ({
    className,
    variant = 'default',
    padding = 'md',
    children,
    ...props
  }, ref) => {
    const baseStyles = `
      rounded-2xl overflow-hidden
      transition-all duration-300 ease-out
    `;

    const variants = {
      default: `
        bg-white border border-[#E3E8EE]
        shadow-[0_4px_12px_rgba(0,0,0,0.05)]
        hover:shadow-[0_8px_24px_rgba(0,0,0,0.06)]
      `,
      elevated: `
        bg-white border border-[#E3E8EE]
        shadow-[0_16px_48px_rgba(0,0,0,0.08)]
      `,
      glass: `
        bg-white/80 backdrop-blur-xl
        border border-white/20
        shadow-[0_8px_32px_rgba(0,0,0,0.08)]
      `,
      interactive: `
        bg-white border border-[#E3E8EE]
        shadow-[0_4px_12px_rgba(0,0,0,0.05)]
        hover:shadow-[0_16px_48px_rgba(0,0,0,0.08)]
        hover:-translate-y-1
        cursor-pointer
      `,
    };

    const paddings = {
      none: '',
      sm: 'p-4',
      md: 'p-6',
      lg: 'p-8',
    };

    return (
      <div
        ref={ref}
        className={cn(
          baseStyles,
          variants[variant],
          paddings[padding],
          className
        )}
        {...props}
      >
        {children}
      </div>
    );
  }
);

Card.displayName = 'Card';

// Card Header
interface CardHeaderProps extends React.HTMLAttributes<HTMLDivElement> {
  title?: string;
  subtitle?: string;
  action?: React.ReactNode;
}

export const CardHeader = React.forwardRef<HTMLDivElement, CardHeaderProps>(
  ({ className, title, subtitle, action, children, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn(
          'flex items-start justify-between gap-4 pb-4 border-b border-[#E3E8EE]',
          className
        )}
        {...props}
      >
        <div className="flex-1 min-w-0">
          {title && (
            <h3 className="text-lg font-semibold text-[#111827] truncate">
              {title}
            </h3>
          )}
          {subtitle && (
            <p className="text-sm text-[#6B7280] mt-1">
              {subtitle}
            </p>
          )}
          {children}
        </div>
        {action && (
          <div className="flex-shrink-0">
            {action}
          </div>
        )}
      </div>
    );
  }
);

CardHeader.displayName = 'CardHeader';

// Card Content
export const CardContent = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, children, ...props }, ref) => {
  return (
    <div
      ref={ref}
      className={cn('pt-4', className)}
      {...props}
    >
      {children}
    </div>
  );
});

CardContent.displayName = 'CardContent';

// Card Footer
export const CardFooter = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, children, ...props }, ref) => {
  return (
    <div
      ref={ref}
      className={cn(
        'flex items-center gap-3 pt-4 mt-4 border-t border-[#E3E8EE]',
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
});

CardFooter.displayName = 'CardFooter';

export default Card;
