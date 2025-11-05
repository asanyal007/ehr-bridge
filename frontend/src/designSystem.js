/**
 * Design System Constants
 * Centralized design tokens for consistent UI/UX
 */

export const colors = {
  primary: {
    50: '#fef3c7',
    100: '#fde68a',
    200: '#fcd34d',
    300: '#fbbf24',
    400: '#f59e0b',
    500: '#f59e0b',
    600: '#d97706',
    700: '#b45309',
    800: '#92400e',
    900: '#78350f'
  },
  success: {
    50: '#d1fae5',
    100: '#a7f3d0',
    200: '#6ee7b7',
    300: '#34d399',
    400: '#10b981',
    500: '#059669',
    600: '#059669',
    700: '#047857',
    800: '#065f46',
    900: '#064e3b'
  },
  danger: {
    50: '#fee2e2',
    100: '#fecaca',
    200: '#fca5a5',
    300: '#f87171',
    400: '#ef4444',
    500: '#dc2626',
    600: '#dc2626',
    700: '#b91c1c',
    800: '#991b1b',
    900: '#7f1d1d'
  },
  info: {
    50: '#dbeafe',
    100: '#bfdbfe',
    200: '#93c5fd',
    300: '#60a5fa',
    400: '#3b82f6',
    500: '#2563eb',
    600: '#2563eb',
    700: '#1d4ed8',
    800: '#1e40af',
    900: '#1e3a8a'
  },
  warning: {
    50: '#fef3c7',
    100: '#fde68a',
    200: '#fcd34d',
    300: '#fbbf24',
    400: '#f59e0b',
    500: '#f59e0b',
    600: '#d97706',
    700: '#b45309',
    800: '#92400e',
    900: '#78350f'
  },
  neutral: {
    50: '#f9fafb',
    100: '#f3f4f6',
    200: '#e5e7eb',
    300: '#d1d5db',
    400: '#9ca3af',
    500: '#6b7280',
    600: '#4b5563',
    700: '#374151',
    800: '#1f2937',
    900: '#111827'
  }
};

export const spacing = {
  xs: '0.5rem',   // 8px
  sm: '1rem',     // 16px
  md: '1.5rem',   // 24px
  lg: '2rem',     // 32px
  xl: '3rem',     // 48px
  '2xl': '4rem',  // 64px
  '3xl': '6rem'   // 96px
};

export const shadows = {
  card: 'shadow-md hover:shadow-lg transition-shadow duration-200',
  modal: 'shadow-2xl',
  button: 'shadow-sm hover:shadow-md transition-shadow duration-150',
  dropdown: 'shadow-lg'
};

export const components = {
  button: {
    primary: 'bg-amber-600 hover:bg-amber-700 text-white font-semibold py-2 px-4 rounded-lg shadow-sm transition-all duration-150 disabled:opacity-50 disabled:cursor-not-allowed',
    secondary: 'bg-white hover:bg-gray-50 text-gray-700 border-2 border-gray-300 font-semibold py-2 px-4 rounded-lg transition-all duration-150 disabled:opacity-50',
    danger: 'bg-red-600 hover:bg-red-700 text-white font-semibold py-2 px-4 rounded-lg shadow-sm transition-all duration-150',
    success: 'bg-green-600 hover:bg-green-700 text-white font-semibold py-2 px-4 rounded-lg shadow-sm transition-all duration-150',
    ghost: 'hover:bg-gray-100 text-gray-700 py-2 px-4 rounded-lg transition-colors duration-150',
    outline: 'border-2 border-amber-600 text-amber-600 hover:bg-amber-50 font-semibold py-2 px-4 rounded-lg transition-all duration-150'
  },
  card: 'bg-white rounded-xl shadow-md border border-gray-200 p-6 transition-shadow duration-200',
  cardCompact: 'bg-white rounded-lg shadow-sm border border-gray-200 p-4',
  input: 'border-2 border-gray-300 rounded-lg px-4 py-2 focus:border-amber-500 focus:ring-2 focus:ring-amber-200 focus:outline-none transition-colors duration-150',
  select: 'border-2 border-gray-300 rounded-lg px-4 py-2 focus:border-amber-500 focus:ring-2 focus:ring-amber-200 focus:outline-none transition-colors duration-150 bg-white',
  badge: {
    success: 'bg-green-100 text-green-800 px-3 py-1 rounded-full text-xs font-semibold',
    warning: 'bg-yellow-100 text-yellow-800 px-3 py-1 rounded-full text-xs font-semibold',
    error: 'bg-red-100 text-red-800 px-3 py-1 rounded-full text-xs font-semibold',
    info: 'bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-xs font-semibold',
    neutral: 'bg-gray-100 text-gray-800 px-3 py-1 rounded-full text-xs font-semibold'
  },
  table: {
    wrapper: 'overflow-x-auto',
    table: 'w-full',
    thead: 'bg-gray-50 border-b-2 border-gray-200',
    th: 'px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider',
    tbody: 'divide-y divide-gray-200',
    tr: 'hover:bg-gray-50 transition-colors duration-100',
    td: 'px-4 py-3 text-sm'
  }
};

export const typography = {
  h1: 'text-3xl font-bold text-gray-900 mb-2',
  h2: 'text-2xl font-semibold text-gray-800 mb-4',
  h3: 'text-xl font-semibold text-gray-700 mb-3',
  h4: 'text-lg font-semibold text-gray-700 mb-2',
  label: 'text-sm font-semibold text-gray-700 mb-2 block',
  caption: 'text-xs text-gray-500',
  body: 'text-sm text-gray-700',
  mono: 'font-mono text-sm'
};

export const animations = {
  fadeIn: 'animate-fade-in',
  slideInRight: 'animate-slide-in-right',
  slideInLeft: 'animate-slide-in-left',
  pulse: 'animate-pulse',
  spin: 'animate-spin'
};

export const breakpoints = {
  sm: '640px',
  md: '768px',
  lg: '1024px',
  xl: '1280px',
  '2xl': '1536px'
};

