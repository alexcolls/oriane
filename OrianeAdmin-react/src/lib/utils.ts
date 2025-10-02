import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDate(date: string): string {
  return date;
}

export function genHash(n: number) {
  const chars =
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
  let result = "";
  for (let i = 0; i < n; i++) {
    result += chars.charAt(Math.floor(Math.random() * chars.length));
  }
  return result;
}

export function normalizeUrl(baseUrl: string, endsWithSlash = true): string {
  if (baseUrl.startsWith("/") && baseUrl.length > 1) {
    baseUrl = baseUrl.substring(1);
  }
  let normalizedUrl = baseUrl.replace(/([^:]\/)\/+/g, "$1");
  if (endsWithSlash && !normalizedUrl.endsWith("/")) {
    normalizedUrl += "/";
  }
  return normalizedUrl;
}

export function formatNumber (num: number) {
  if (num >= 1000 && num < 1000000) {
    return `${(num / 1000).toFixed(0)}K`;
  } else if (num >= 1000000) {
    return `${(num / 1000000).toFixed(0)}M`;
  }
  return String(num);
};

export function formatDuration(startDate: Date, endDate: Date): string {
  if (!startDate || !endDate) {
    return "Processing...";
  }
  const diffMs = Math.abs(endDate.getTime() - startDate.getTime());
  const days = Math.floor(diffMs / (1000 * 60 * 60 * 24));
  const hours = Math.floor((diffMs % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
  const minutes = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60));
  const seconds = Math.floor((diffMs % (1000 * 60)) / 1000);
  const parts = [];
  if (days > 0) parts.push(`${days}d`);
  if (hours > 0) parts.push(`${hours}h`);
  if (minutes > 0) parts.push(`${minutes}m`);
  if (seconds > 0) parts.push(`${seconds}s`);
  return parts.join(' ') || '0s';
};
