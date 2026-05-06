"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { 
  Users, 
  FileText, 
  CreditCard, 
  Activity,
  TrendingUp,
  TrendingDown
} from "lucide-react";

const stats = [
  {
    title: "Total de Usuários",
    value: "2,543",
    change: "+12.5%",
    trend: "up",
    icon: Users,
  },
  {
    title: "Documentos Processados",
    value: "45,231",
    change: "+23.1%",
    trend: "up",
    icon: FileText,
  },
  {
    title: "Receita Mensal",
    value: "R$ 89.4K",
    change: "+8.2%",
    trend: "up",
    icon: CreditCard,
  },
  {
    title: "Taxa de Conversão",
    value: "3.24%",
    change: "-2.1%",
    trend: "down",
    icon: Activity,
  },
];

export default function AdminDashboard() {
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-legal-600 to-gold-500 flex items-center justify-center">
              <Activity className="w-5 h-5 text-white" />
            </div>
            <h1 className="text-xl font-bold">NeoBusiness Admin</h1>
          </div>
          <div className="flex items-center space-x-4">
            <span className="text-sm text-gray-600">Admin</span>
            <div className="w-8 h-8 rounded-full bg-gray-200" />
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <h2 className="text-2xl font-bold mb-6">Dashboard</h2>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {stats.map((stat) => (
            <Card key={stat.title}>
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600">{stat.title}</p>
                    <p className="text-2xl font-bold mt-1">{stat.value}</p>
                    <div className="flex items-center mt-2">
                      {stat.trend === "up" ? (
                        <TrendingUp className="w-4 h-4 text-green-500 mr-1" />
                      ) : (
                        <TrendingDown className="w-4 h-4 text-red-500 mr-1" />
                      )}
                      <span
                        className={`text-sm ${
                          stat.trend === "up" ? "text-green-500" : "text-red-500"
                        }`}
                      >
                        {stat.change}
                      </span>
                      <span className="text-sm text-gray-400 ml-1">vs mês anterior</span>
                    </div>
                  </div>
                  <div className="w-12 h-12 rounded-lg bg-blue-100 flex items-center justify-center">
                    <stat.icon className="w-6 h-6 text-blue-600" />
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Recent Users */}
          <Card className="lg:col-span-2">
            <CardHeader>
              <CardTitle>Usuários Recentes</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {[
                  { name: "João Silva", email: "joao@escritorio.com", plan: "Professional", date: "2 min atrás" },
                  { name: "Maria Santos", email: "maria@advogados.com", plan: "Business", date: "15 min atrás" },
                  { name: "Carlos Oliveira", email: "carlos@juridico.com", plan: "Starter", date: "1 hora atrás" },
                  { name: "Ana Pereira", email: "ana@law.com", plan: "Professional", date: "2 horas atrás" },
                ].map((user, index) => (
                  <div key={index} className="flex items-center justify-between py-3 border-b last:border-0">
                    <div className="flex items-center space-x-3">
                      <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-400 to-blue-600 flex items-center justify-center text-white font-semibold">
                        {user.name.charAt(0)}
                      </div>
                      <div>
                        <p className="font-medium">{user.name}</p>
                        <p className="text-sm text-gray-500">{user.email}</p>
                      </div>
                    </div>
                    <div className="text-right">
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                        {user.plan}
                      </span>
                      <p className="text-sm text-gray-400 mt-1">{user.date}</p>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* System Status */}
          <Card>
            <CardHeader>
              <CardTitle>Status do Sistema</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {[
                  { service: "API", status: "operational", uptime: "99.9%" },
                  { service: "Database", status: "operational", uptime: "99.9%" },
                  { service: "Storage", status: "operational", uptime: "99.9%" },
                  { service: "AI Service", status: "degraded", uptime: "98.2%" },
                ].map((service) => (
                  <div key={service.service} className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <div
                        className={`w-3 h-3 rounded-full ${
                          service.status === "operational"
                            ? "bg-green-500"
                            : service.status === "degraded"
                            ? "bg-yellow-500"
                            : "bg-red-500"
                        }`}
                      />
                      <span className="font-medium">{service.service}</span>
                    </div>
                    <span className="text-sm text-gray-500">{service.uptime}</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  );
}
