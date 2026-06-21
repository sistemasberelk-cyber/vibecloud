import "./globals.css";

export const metadata = {
  title: "NexPos SaaS POS Terminal",
  description: "Terminal de Ventas Mayorista adaptativa y Marca Blanca",
};

export default function RootLayout({ children }) {
  return (
    <html lang="es">
      <body style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
        {children}
      </body>
    </html>
  );
}
