/**
 * Utility functions for the frontend
 */

import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

/**
 * Combines class names using clsx and tailwind-merge
 * This allows for dynamic class names that properly merge Tailwind classes
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/**
 * Format date to locale string
 */
export function formatDate(date: Date | string): string {
  const d = typeof date === 'string' ? new Date(date) : date;
  return d.toLocaleDateString('pt-BR', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  });
}

/**
 * Format number with Brazilian locale
 */
export function formatNumber(num: number): string {
  return num.toLocaleString('pt-BR');
}

/**
 * Truncate text with ellipsis
 */
export function truncate(text: string, length: number): string {
  if (text.length <= length) return text;
  return text.slice(0, length) + '...';
}

/**
 * Delay function for async operations
 */
export function delay(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Generate random ID
 */
export function generateId(): string {
  return Math.random().toString(36).substring(2, 15);
}

/**
 * Check if code is running on client side
 */
export function isClient(): boolean {
  return typeof window !== 'undefined';
}

/**
 * Safely access localStorage
 */
export function getLocalStorage(key: string): string | null {
  if (!isClient()) return null;
  try {
    return localStorage.getItem(key);
  } catch {
    return null;
  }
}

export function setLocalStorage(key: string, value: string): void {
  if (!isClient()) return;
  try {
    localStorage.setItem(key, value);
  } catch {
    // Ignore errors (e.g., quota exceeded)
  }
}
