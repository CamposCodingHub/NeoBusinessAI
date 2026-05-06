import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Providers } from "@/components/providers";
import { Toaster } from "@/components/ui/toaster";

const inter = Inter({ 
  subsets: ["latin"],
  variable: "--font-sans",
});

export const metadata: Metadata = {
  title: "NeoBusiness AI - Plataforma Jurídica Enterprise",
  description: "Transforme seu escritório com IA. Análise de documentos, geração de peças jurídicas e automação inteligente.",
  keywords: ["IA Jurídica", "Documentos", "Advocacia", "Automação", "Legal Tech"],
  authors: [{ name: "NeoBusiness AI" }],
  openGraph: {
    title: "NeoBusiness AI - Plataforma Jurídica Enterprise",
    description: "Transforme seu escritório com IA",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="pt-BR" suppressHydrationWarning>
      <body className={`${inter.variable} font-sans antialiased`}>
        <Providers>
          {children}
          <Toaster />
        </Providers>
      </body>
    </html>
  );
}
