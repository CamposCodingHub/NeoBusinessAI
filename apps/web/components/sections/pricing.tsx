"use client";

import { motion } from "framer-motion";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Check } from "lucide-react";
import Link from "next/link";

const plans = [
  {
    name: "Starter",
    price: "R$ 49,90",
    period: "/mês",
    description: "Para advogados e escritórios pequenos",
    features: [
      "10 documentos/mês",
      "100 requisições IA",
      "1GB storage",
      "1 usuário",
      "OCR básico",
      "5 templates jurídicos",
    ],
    cta: "Começar Grátis",
    popular: false,
  },
  {
    name: "Professional",
    price: "R$ 149,90",
    period: "/mês",
    description: "Para escritórios em crescimento",
    features: [
      "100 documentos/mês",
      "1.000 requisições IA",
      "10GB storage",
      "5 usuários",
      "OCR avançado",
      "Todos templates",
      "API access",
      "Suporte prioritário",
    ],
    cta: "Começar Agora",
    popular: true,
  },
  {
    name: "Business",
    price: "R$ 499,90",
    period: "/mês",
    description: "Para escritórios médios e grandes",
    features: [
      "1.000 documentos/mês",
      "10.000 requisições IA",
      "100GB storage",
      "25 usuários",
      "OCR enterprise",
      "Todos templates",
      "API access",
      "Suporte dedicado",
      "Custom branding",
    ],
    cta: "Falar com Vendas",
    popular: false,
  },
];

export function PricingSection() {
  return (
    <section id="pricing" className="py-24">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <motion.h2
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-3xl sm:text-4xl lg:text-5xl font-bold mb-4"
          >
            Planos <span className="gradient-text">Transparentes</span>
          </motion.h2>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            Escolha o plano ideal para seu escritório. Todos incluem 14 dias de trial.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {plans.map((plan, index) => (
            <motion.div
              key={plan.name}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: index * 0.1 }}
            >
              <Card className={`h-full relative ${plan.popular ? "border-2 border-legal-500 shadow-xl" : ""}`}>
                {plan.popular && (
                  <div className="absolute -top-4 left-1/2 -translate-x-1/2">
                    <span className="bg-gradient-to-r from-legal-600 to-gold-500 text-white text-xs font-semibold px-4 py-1 rounded-full">
                      Mais Popular
                    </span>
                  </div>
                )}
                <CardHeader className="text-center pb-4">
                  <h3 className="text-xl font-semibold">{plan.name}</h3>
                  <p className="text-sm text-muted-foreground">{plan.description}</p>
                  <div className="mt-4">
                    <span className="text-4xl font-bold">{plan.price}</span>
                    <span className="text-muted-foreground">{plan.period}</span>
                  </div>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-3 mb-6">
                    {plan.features.map((feature) => (
                      <li key={feature} className="flex items-start space-x-3">
                        <Check className="w-5 h-5 text-green-500 flex-shrink-0 mt-0.5" />
                        <span className="text-sm">{feature}</span>
                      </li>
                    ))}
                  </ul>
                  <Link href="/register">
                    <Button
                      className={`w-full ${
                        plan.popular
                          ? "bg-gradient-to-r from-legal-600 to-gold-500"
                          : ""
                      }`}
                      variant={plan.popular ? "default" : "outline"}
                    >
                      {plan.cta}
                    </Button>
                  </Link>
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
