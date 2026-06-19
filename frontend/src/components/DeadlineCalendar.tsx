"use client";

import { useState, useMemo } from "react";

const colors = {
  primary: "#1e3a5f",
  secondary: "#c9a227",
  accent: "#10b981",
  danger: "#ef4444",
  dark: "#0f172a",
  light: "#f8fafc",
  gray: "#64748b"
};

interface Deadline {
  document_id: number;
  document_name: string;
  document_type: string;
  process_number: string;
  deadline: {
    days: string;
    urgency: string;
    context: string;
  };
  urgency: string;
}

interface DeadlineCalendarProps {
  deadlines: Deadline[];
}

export default function DeadlineCalendar({ deadlines }: DeadlineCalendarProps) {
  const [currentDate, setCurrentDate] = useState(new Date());
  const [selectedDate, setSelectedDate] = useState<Date | null>(null);

  // Navegação
  const prevMonth = () => {
    setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() - 1, 1));
  };

  const nextMonth = () => {
    setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 1));
  };

  // Calcular dias do mês
  const calendarDays = useMemo(() => {
    const year = currentDate.getFullYear();
    const month = currentDate.getMonth();

    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);

    const startDayOfWeek = firstDay.getDay(); // 0 = Domingo
    const daysInMonth = lastDay.getDate();

    const days: Array<{ date: number; deadlines: Deadline[]; isToday: boolean }> = [];

    // Dias vazios antes do início do mês
    for (let i = 0; i < startDayOfWeek; i++) {
      days.push({ date: 0, deadlines: [], isToday: false });
    }

    // Dias do mês
    const today = new Date();
    for (let day = 1; day <= daysInMonth; day++) {
      const currentDayDate = new Date(year, month, day);

      // Simular prazos para dias específicos (para demonstração)
      // Em produção, isso viria de análise de datas reais
      const dayDeadlines = deadlines.filter((dl, idx) => {
        // Distribuir prazos aleatoriamente nos dias para demo
        return (day + idx) % 7 === 0 && idx < 10;
      });

      const isToday =
        today.getDate() === day &&
        today.getMonth() === month &&
        today.getFullYear() === year;

      days.push({ date: day, deadlines: dayDeadlines, isToday });
    }

    return days;
  }, [currentDate, deadlines]);

  const monthNames = [
    "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
  ];

  const weekDays = ["Dom", "Seg", "Ter", "Qua", "Qui", "Sex", "Sáb"];

  const getUrgencyColor = (urgency: string) => {
    switch (urgency) {
      case "high": return colors.danger;
      case "medium": return colors.secondary;
      default: return colors.accent;
    }
  };

  return (
    <div style={{ background: `${colors.primary}20`, borderRadius: "16px", padding: "24px" }}>
      {/* Header do Calendário */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "24px" }}>
        <h3 style={{ color: colors.light, margin: 0, fontSize: "20px" }}>
          📅 {monthNames[currentDate.getMonth()]} {currentDate.getFullYear()}
        </h3>
        <div style={{ display: "flex", gap: "8px" }}>
          <button
            onClick={prevMonth}
            style={{
              padding: "8px 16px",
              background: `${colors.primary}50`,
              border: `1px solid ${colors.primary}50`,
              borderRadius: "8px",
              color: colors.light,
              cursor: "pointer"
            }}
          >
            ← Anterior
          </button>
          <button
            onClick={() => setCurrentDate(new Date())}
            style={{
              padding: "8px 16px",
              background: colors.secondary,
              border: "none",
              borderRadius: "8px",
              color: colors.dark,
              cursor: "pointer",
              fontWeight: 600
            }}
          >
            Hoje
          </button>
          <button
            onClick={nextMonth}
            style={{
              padding: "8px 16px",
              background: `${colors.primary}50`,
              border: `1px solid ${colors.primary}50`,
              borderRadius: "8px",
              color: colors.light,
              cursor: "pointer"
            }}
          >
            Próximo →
          </button>
        </div>
      </div>

      {/* Grade do Calendário */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(7, 1fr)", gap: "8px" }}>
        {/* Cabeçalho dos dias da semana */}
        {weekDays.map((day) => (
          <div
            key={day}
            style={{
              textAlign: "center",
              padding: "12px",
              color: colors.gray,
              fontSize: "14px",
              fontWeight: 600
            }}
          >
            {day}
          </div>
        ))}

        {/* Dias */}
        {calendarDays.map((day, idx) => (
          <div
            key={idx}
            onClick={() => day.date > 0 && setSelectedDate(new Date(currentDate.getFullYear(), currentDate.getMonth(), day.date))}
            style={{
              aspectRatio: "1",
              background: day.date === 0
                ? "transparent"
                : day.isToday
                  ? `${colors.secondary}30`
                  : `${colors.primary}30`,
              border: day.isToday
                ? `2px solid ${colors.secondary}`
                : `1px solid ${colors.primary}30`,
              borderRadius: "8px",
              padding: "8px",
              cursor: day.date > 0 ? "pointer" : "default",
              display: "flex",
              flexDirection: "column",
              gap: "4px",
              minHeight: "80px"
            }}
          >
            {day.date > 0 && (
              <>
                <span style={{
                  color: day.isToday ? colors.secondary : colors.light,
                  fontWeight: day.isToday ? 700 : 400,
                  fontSize: "14px"
                }}>
                  {day.date}
                </span>

                {/* Indicadores de prazos */}
                <div style={{ display: "flex", flexDirection: "column", gap: "2px", flex: 1 }}>
                  {day.deadlines.slice(0, 3).map((dl, dlIdx) => (
                    <div
                      key={dlIdx}
                      style={{
                        background: getUrgencyColor(dl.urgency),
                        height: "6px",
                        borderRadius: "3px",
                        width: "100%"
                      }}
                      title={`${dl.document_name} - ${dl.deadline.days} dias`}
                    />
                  ))}
                  {day.deadlines.length > 3 && (
                    <span style={{ color: colors.gray, fontSize: "10px", textAlign: "center" }}>
                      +{day.deadlines.length - 3}
                    </span>
                  )}
                </div>
              </>
            )}
          </div>
        ))}
      </div>

      {/* Legenda */}
      <div style={{ display: "flex", gap: "16px", marginTop: "16px", justifyContent: "center" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
          <div style={{ width: "12px", height: "12px", background: colors.danger, borderRadius: "2px" }} />
          <span style={{ color: colors.gray, fontSize: "12px" }}>Urgente</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
          <div style={{ width: "12px", height: "12px", background: colors.secondary, borderRadius: "2px" }} />
          <span style={{ color: colors.gray, fontSize: "12px" }}>Médio</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
          <div style={{ width: "12px", height: "12px", background: colors.accent, borderRadius: "2px" }} />
          <span style={{ color: colors.gray, fontSize: "12px" }}>Baixo</span>
        </div>
      </div>

      {/* Modal de Detalhes do Dia */}
      {selectedDate && (
        <div
          onClick={() => setSelectedDate(null)}
          style={{
            position: "fixed",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: "rgba(0,0,0,0.8)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 1000
          }}
        >
          <div
            onClick={(e) => e.stopPropagation()}
            style={{
              background: colors.dark,
              border: `1px solid ${colors.primary}50`,
              borderRadius: "16px",
              padding: "24px",
              width: "100%",
              maxWidth: "500px",
              maxHeight: "80vh",
              overflow: "auto"
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
              <h3 style={{ color: colors.light, margin: 0 }}>
                {selectedDate.toLocaleDateString("pt-BR", { weekday: "long", year: "numeric", month: "long", day: "numeric" })}
              </h3>
              <button
                onClick={() => setSelectedDate(null)}
                style={{
                  background: "transparent",
                  border: "none",
                  color: colors.light,
                  fontSize: "24px",
                  cursor: "pointer"
                }}
              >
                ×
              </button>
            </div>

            <div style={{ display: "grid", gap: "12px" }}>
              {calendarDays
                .find(d => d.date === selectedDate.getDate() && d.date > 0)
                ?.deadlines.map((dl, idx) => (
                  <div
                    key={idx}
                    style={{
                      background: `${getUrgencyColor(dl.urgency)}20`,
                      border: `1px solid ${getUrgencyColor(dl.urgency)}50`,
                      borderRadius: "8px",
                      padding: "12px"
                    }}
                  >
                    <div style={{ color: colors.light, fontWeight: 600, marginBottom: "4px" }}>
                      {dl.document_name}
                    </div>
                    <div style={{ color: colors.gray, fontSize: "14px" }}>
                      {dl.deadline.days} dias • {dl.document_type}
                    </div>
                    {dl.process_number && (
                      <div style={{ color: colors.secondary, fontSize: "12px", marginTop: "4px" }}>
                        Processo: {dl.process_number}
                      </div>
                    )}
                  </div>
                )) || (
                  <div style={{ color: colors.gray, textAlign: "center", padding: "24px" }}>
                    Nenhum prazo para este dia.
                  </div>
                )
              }
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
