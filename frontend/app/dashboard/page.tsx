import PageContainer from "@/components/PageContainer";

export default function DashboardPage() {
  return (
    <PageContainer
      title="Dashboard"
      description="System overview, agent status, and key metrics at a glance."
      icon="📊"
    >
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {[
          { label: "Active Agents", value: "--", color: "blue" },
          { label: "Sessions Today", value: "--", color: "green" },
          { label: "System Status", value: "Offline", color: "yellow" },
        ].map((card) => (
          <div
            key={card.label}
            className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm"
          >
            <p className="text-sm font-medium text-gray-500">{card.label}</p>
            <p className={`text-3xl font-bold mt-2 text-${card.color}-600`}>
              {card.value}
            </p>
          </div>
        ))}
      </div>

      <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">
          Recent Activity
        </h2>
        <p className="text-gray-500 text-sm">
          No activity yet. Start a chat session or run a diagnostic to see
          activity here.
        </p>
      </div>
    </PageContainer>
  );
}
