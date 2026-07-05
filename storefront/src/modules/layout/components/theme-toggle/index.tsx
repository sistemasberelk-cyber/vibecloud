"use client"

import React, { useCallback, useEffect, useState } from "react"

const STORAGE_KEY = "vibecloud-theme-mode"

type ThemeMode = "dark" | "light"

/**
 * Sol/Luna theme toggle — floating pill button with smooth icon morph.
 * Reads/writes `data-mode` on `<html>` and persists choice to localStorage.
 */
const ThemeToggle: React.FC = () => {
  const [mode, setMode] = useState<ThemeMode>("dark")
  const [mounted, setMounted] = useState(false)

  // On mount: read localStorage or fall back to current DOM attribute
  useEffect(() => {
    const saved = localStorage.getItem(STORAGE_KEY) as ThemeMode | null
    const current =
      saved ||
      (document.documentElement.getAttribute("data-mode") as ThemeMode) ||
      "dark"

    setMode(current)
    document.documentElement.setAttribute("data-mode", current)
    setMounted(true)
  }, [])

  const toggle = useCallback(() => {
    setMode((prev) => {
      const next: ThemeMode = prev === "dark" ? "light" : "dark"
      document.documentElement.setAttribute("data-mode", next)
      localStorage.setItem(STORAGE_KEY, next)
      return next
    })
  }, [])

  // Avoid hydration flash — render nothing until client-side mount
  if (!mounted) return null

  const isDark = mode === "dark"

  return (
    <button
      type="button"
      onClick={toggle}
      aria-label={`Switch to ${isDark ? "light" : "dark"} mode`}
      className="
        group relative z-50
        flex items-center justify-center
        h-10 w-10 rounded-full
        bg-white/10 dark:bg-white/5
        backdrop-blur-xl
        border border-white/20 dark:border-white/10
        shadow-lg shadow-black/5
        hover:bg-white/20 dark:hover:bg-white/10
        hover:border-white/30 dark:hover:border-white/20
        hover:shadow-xl hover:shadow-black/10
        active:scale-95
        transition-all duration-300 ease-out
        cursor-pointer
      "
    >
      {/* Sun icon */}
      <svg
        xmlns="http://www.w3.org/2000/svg"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth={2}
        strokeLinecap="round"
        strokeLinejoin="round"
        className={`
          absolute h-5 w-5 text-amber-400
          transition-all duration-500 ease-[cubic-bezier(0.34,1.56,0.64,1)]
          ${isDark ? "rotate-90 scale-0 opacity-0" : "rotate-0 scale-100 opacity-100"}
        `}
      >
        <circle cx="12" cy="12" r="5" />
        <line x1="12" y1="1" x2="12" y2="3" />
        <line x1="12" y1="21" x2="12" y2="23" />
        <line x1="4.22" y1="4.22" x2="5.64" y2="5.64" />
        <line x1="18.36" y1="18.36" x2="19.78" y2="19.78" />
        <line x1="1" y1="12" x2="3" y2="12" />
        <line x1="21" y1="12" x2="23" y2="12" />
        <line x1="4.22" y1="19.78" x2="5.64" y2="18.36" />
        <line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
      </svg>

      {/* Moon icon */}
      <svg
        xmlns="http://www.w3.org/2000/svg"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth={2}
        strokeLinecap="round"
        strokeLinejoin="round"
        className={`
          absolute h-5 w-5 text-indigo-300
          transition-all duration-500 ease-[cubic-bezier(0.34,1.56,0.64,1)]
          ${isDark ? "rotate-0 scale-100 opacity-100" : "-rotate-90 scale-0 opacity-0"}
        `}
      >
        <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
      </svg>
    </button>
  )
}

export default ThemeToggle
