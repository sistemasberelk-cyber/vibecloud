import { getBaseURL } from "@lib/util/env"
import { Metadata } from "next"
import "styles/globals.css"
import React from "react"

export const metadata: Metadata = {
  metadataBase: new URL(getBaseURL()),
}

async function getSDUIConfig(tenantId: number, page: string) {
  try {
    const vibecloudUrl = process.env.NEXT_PUBLIC_VIBECLOUD_URL || "http://localhost:8000"
    const res = await fetch(`${vibecloudUrl}/api/v1/ui-config/public/${tenantId}/${page}`, {
      next: { revalidate: 30 }
    })
    if (!res.ok) return null
    return res.json()
  } catch (err) {
    console.error("Failed to fetch SDUI config", err)
    return null
  }
}

export default async function RootLayout(props: { children: React.ReactNode }) {
  const config = await getSDUIConfig(1, "storefront_home")
  const primaryColor = config?.theme?.primary_color || "#4F46E5"
  const secondaryColor = config?.theme?.secondary_color || "#10B981"
  const themeMode = config?.theme?.mode || "dark"

  return (
    <html lang="en" data-mode={themeMode} style={{ 
      "--primary-sdui": primaryColor,
      "--secondary-sdui": secondaryColor
    } as React.CSSProperties}>
      <body>
        <main className="relative">{props.children}</main>
      </body>
    </html>
  )
}
