import PageHeader from '@/components/ui/PageHeader'

export default function Page() {
  return (
    <div className="flex-1 overflow-y-auto p-4 md:p-6">
      <PageHeader title="Admin Dashboard" subtitle="System administration" />
      <div className="rounded-xl border border-dashed border-gray-200 bg-white p-12 text-center">
        <p className="text-sm text-gray-400">Coming soon</p>
      </div>
    </div>
  )
}
