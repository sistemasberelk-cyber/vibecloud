"use client"

import { useEffect, useState } from "react"

export default function ThemeToggle() {
  const [mode, setMode] = useState<"light" | "dark">("dark")

  useEffect(() => {
    const currentMode = document.documentElement.getAttribute("data-mode") as "light" | "dark"
    if (currentMode) {
      setMode(currentMode)
    }
  }, [])

  const toggleTheme = () => {
    const nextMode = mode === "dark" ? "light" : "dark"
    document.documentElement.setAttribute("data-mode", nextMode)
    setMode(nextMode)
  }

  return (
    <button
      onClick={toggleTheme}
      className="p-2 rounded-lg bg-white/10 hover:bg-white/20 transition-colors border border-white/10 flex items-center justify-center text-white"
      aria-label="Toggle Theme"
      type="button"
    >
      {mode === "dark" ? (
        // Icono de Sol para cambiar a Claro
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-5 h-5">
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 3v2.25m0 13.5V21M4.95 4.95l1.59 1.59m10.91 10.91l1.59 1.59M3 12h2.25m13.5 0H21M4.95 19.05l1.59-1.59m10.91-10.91l1.59-1.59M12 9a3 3 0 100 6 3 3 0 000-6z" />
        </svg>
      ) : (
        // Icono de Luna para cambiar a Oscuro
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-5 h-5">
          <path strokeLinecap="round" strokeLinejoin="round" d="M21.752 15.002A9.718 9.718 0 0118 15.75c-5.385 0-9.75-4.365-9.75-9.75 0-1.33.266-2.597.748-3.752A9.753 9.753 0 003 11.25C3 16.635 7.365 21 12.75 21a9.753 9.753 0 009.002-5.998z" />
        </svg>
      )}
    </button>
  )
}
