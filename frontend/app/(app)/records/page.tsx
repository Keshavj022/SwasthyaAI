import PageHeader from '@/components/ui/PageHeader'

export default function Page() {
  return (
    <div>
      <PageHeader title="My Records" subtitle="Your medical history" />
      <div className="rounded-xl border border-dashed border-gray-200 bg-white p-12 text-center">
        <p className="text-sm text-gray-400">Coming soon</p>
      </div>
    </div>
  )
}
