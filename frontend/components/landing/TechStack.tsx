const STACK = ['Next.js', 'FastAPI', 'SQLite', 'Google Medical AI']

export default function TechStack() {
  return (
    <section className="bg-white py-20 sm:py-24">
      <div className="mx-auto max-w-4xl px-6 text-center">
        <h2 className="text-3xl font-bold tracking-tight text-[#1A1A2E] sm:text-4xl">
          Powered by open technology
        </h2>

        <ul className="mt-10 flex flex-wrap items-center justify-center gap-3 sm:gap-4">
          {STACK.map((name) => (
            <li
              key={name}
              className="rounded-full border border-border bg-gray-50 px-5 py-2.5 text-sm font-semibold text-[#1A1A2E]"
            >
              {name}
            </li>
          ))}
        </ul>

        <p className="mt-10 text-sm text-muted-foreground">
          Fully offline-capable — no cloud required for core features
        </p>
      </div>
    </section>
  )
}
