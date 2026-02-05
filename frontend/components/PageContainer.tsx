interface PageContainerProps {
  children: React.ReactNode
  title: string
  description?: string
  icon?: string
}

export default function PageContainer({
  children,
  title,
  description,
  icon
}: PageContainerProps) {
  return (
    <div className="p-8">
      {/* Page Header */}
      <div className="mb-8">
        <div className="flex items-center space-x-3 mb-2">
          {icon && <span className="text-4xl">{icon}</span>}
          <h1 className="text-3xl font-bold text-gray-900">{title}</h1>
        </div>
        {description && (
          <p className="text-gray-600 max-w-3xl">{description}</p>
        )}
      </div>

      {/* Page Content */}
      <div className="space-y-6">
        {children}
      </div>
    </div>
  )
}
