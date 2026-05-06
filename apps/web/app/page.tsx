import { Metadata } from "next";
import { HeroSection } from "@/components/sections/hero";
import { FeaturesSection } from "@/components/sections/features";
import { PricingSection } from "@/components/sections/pricing";
import { CTASection } from "@/components/sections/cta";
import { Navbar } from "@/components/navbar";
import { Footer } from "@/components/footer";

export const metadata: Metadata = {
  title: "NeoBusiness AI - Plataforma Jurídica Enterprise",
  description: "Transforme seu escritório com IA. Análise de documentos, geração de peças jurídicas e automação inteligente.",
};

export default function HomePage() {
  return (
    <main className="min-h-screen bg-gradient-to-b from-background to-muted/20">
      <Navbar />
      <HeroSection />
      <FeaturesSection />
      <PricingSection />
      <CTASection />
      <Footer />
    </main>
  );
}
