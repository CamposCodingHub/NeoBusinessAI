"use client";

import { motion } from "framer-motion";
import { Card, CardContent } from "@/components/ui/card";
import { 
  FileText, 
  Brain, 
  Scale, 
  Shield, 
  Zap, 
  Users,
  Clock,
  Lock
} from "lucide-react";

const features = [
  {
    icon: FileText,
    title: "Análise de Documentos",
    description: "Extraia insights automáticos de contratos, petições e documentos jurídicos com OCR avançado.",
    color: "from-blue-500 to-cyan-500",
  },
  {
    icon: Brain,
    title: "IA Jurídica Especializada",
    description: "Gere peças processuais, contestações e recursos com auxílio de IA treinada em direito.",
    color: "from-purple-500 to-pink-500",
  },
  {
    icon: Scale,
    title: "Pesquisa Jurisprudencial",
    description: "Acesse jurisprudência, doutrina e legislação relevante para seus casos em segundos.",
    color: "from-amber-500 to-orange-500",
  },
  {
    icon: Shield,
    title: "Segurança Enterprise",
    description: "Dados protegidos com criptografia, isolamento multi-tenant e compliance LGPD.",
    color: "from-green-500 to-emerald-500",
  },
  {
    icon: Zap,
    title: "Processamento Rápido",
    description: "Análise de documentos em segundos com infraestrutura de alta performance.",
    color: "from-yellow-500 to-amber-500",
  },
  {
    icon: Users,
    title: "Colaboração em Equipe",
    description: "Compartilhe documentos e insights com sua equipe de forma segura e organizada.",
    color: "from-indigo-500 to-blue-500",
  },
  {
    icon: Clock,
    title: "Automação de Workflows",
    description: "Automatize tarefas repetitivas e ganhe tempo para focar no que realmente importa.",
    color: "from-rose-500 to-pink-500",
  },
  {
    icon: Lock,
    title: "Controle de Acesso",
    description: "RBAC avançado com permissões granulares para diferentes níveis de usuários.",
    color: "from-slate-500 to-gray-500",
  },
];

export function FeaturesSection() {
  return (
    <section id="features" className="py-24 bg-muted/50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-16">
          <motion.h2
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5 }}
            className="text-3xl sm:text-4xl lg:text-5xl font-bold mb-4"
          >
            Recursos <span className="gradient-text">Poderosos</span>
          </motion.h2>
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5, delay: 0.1 }}
            className="text-lg text-muted-foreground max-w-2xl mx-auto"
          >
            Tudo que seu escritório precisa para trabalhar com eficiência e precisão
          </motion.p>
        </div>

        {/* Features Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {features.map((feature, index) => (
            <motion.div
              key={feature.title}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: index * 0.1 }}
            >
              <Card className="h-full hover-lift group border-0 shadow-lg bg-gradient-to-br from-background to-muted/50">
                <CardContent className="p-6">
                  <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${feature.color} flex items-center justify-center mb-4 group-hover:scale-110 transition-transform`}>
                    <feature.icon className="w-6 h-6 text-white" />
                  </div>
                  <h3 className="text-lg font-semibold mb-2">{feature.title}</h3>
                  <p className="text-sm text-muted-foreground">{feature.description}</p>
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
