'use client'

import { useState, useMemo } from 'react'
import { ChevronLeft, ChevronRight } from 'lucide-react'
import {
  startOfMonth, endOfMonth, eachDayOfInterval, startOfWeek, endOfWeek,
  format, isSameDay, isBefore, startOfToday, addMonths, subMonths,
} from 'date-fns'

interface DateTimeSlotPickerProps {
  /** Available slot datetimes (ISO strings) */
  slots: string[]
  /** Currently selected datetime (ISO string or null) */
  selected: string | null
  onChange: (iso: string) => void
}

const WEEKDAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

function formatTime(iso: string): string {
  try {
    return new Date(iso).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  } catch { return iso }
}

export function DateTimeSlotPicker({ slots, selected, onChange }: DateTimeSlotPickerProps) {
  const [viewMonth, setViewMonth] = useState(() => new Date())
  const today = startOfToday()

  // Set of date strings (yyyy-MM-dd) that have at least one available slot
  const availableDates = useMemo(
    () => new Set(slots.map((s) => format(new Date(s), 'yyyy-MM-dd'))),
    [slots]
  )

  // Calendar grid: full weeks covering the view month (Mon-Sun)
  const calendarDays = useMemo(() => {
    const start = startOfWeek(startOfMonth(viewMonth), { weekStartsOn: 1 })
    const end = endOfWeek(endOfMonth(viewMonth), { weekStartsOn: 1 })
    return eachDayOfInterval({ start, end })
  }, [viewMonth])

  const selectedDate = selected ? new Date(selected) : null

  function handleDayClick(day: Date) {
    if (isBefore(day, today)) return
    const key = format(day, 'yyyy-MM-dd')
    if (!availableDates.has(key)) return
    // Auto-select the first available slot on that day
    const firstSlot = slots.find((s) => format(new Date(s), 'yyyy-MM-dd') === key)
    if (firstSlot) onChange(firstSlot)
  }

  // Time slots for the currently selected date
  const timeSlotsForDay = useMemo(() => {
    if (!selectedDate) return []
    const key = format(selectedDate, 'yyyy-MM-dd')
    return slots.filter((s) => format(new Date(s), 'yyyy-MM-dd') === key)
  }, [slots, selectedDate])

  return (
    <div className="space-y-4">
      {/* Month navigator */}
      <div className="flex items-center justify-between">
        <button
          type="button"
          onClick={() => setViewMonth((m) => subMonths(m, 1))}
          className="p-1.5 rounded-lg hover:bg-gray-100 text-gray-600"
        >
          <ChevronLeft size={16} />
        </button>
        <span className="text-sm font-semibold text-gray-900">
          {format(viewMonth, 'MMMM yyyy')}
        </span>
        <button
          type="button"
          onClick={() => setViewMonth((m) => addMonths(m, 1))}
          className="p-1.5 rounded-lg hover:bg-gray-100 text-gray-600"
        >
          <ChevronRight size={16} />
        </button>
      </div>

      {/* Weekday headers */}
      <div className="grid grid-cols-7 text-center">
        {WEEKDAYS.map((d) => (
          <div key={d} className="text-xs font-medium text-gray-400 py-1">{d}</div>
        ))}
      </div>

      {/* Day grid */}
      <div className="grid grid-cols-7 gap-y-0.5">
        {calendarDays.map((day) => {
          const key = format(day, 'yyyy-MM-dd')
          const isAvail = availableDates.has(key)
          const isPast = isBefore(day, today)
          const isSelected = selectedDate ? isSameDay(day, selectedDate) : false
          const isCurrentMonth =
            day.getMonth() === viewMonth.getMonth() &&
            day.getFullYear() === viewMonth.getFullYear()

          let btnClass = 'w-8 h-8 mx-auto rounded-full flex items-center justify-center text-xs transition-colors '
          if (isSelected) {
            btnClass += 'bg-teal-600 text-white font-semibold'
          } else if (isAvail && !isPast && isCurrentMonth) {
            btnClass += 'bg-teal-50 text-teal-700 font-medium cursor-pointer hover:bg-teal-100'
          } else {
            btnClass += 'text-gray-300 cursor-default'
          }

          return (
            <div key={key} className="py-0.5 flex justify-center">
              <button
                type="button"
                className={btnClass}
                onClick={() => handleDayClick(day)}
                disabled={!isAvail || isPast || !isCurrentMonth}
                tabIndex={isAvail && !isPast && isCurrentMonth ? 0 : -1}
              >
                {format(day, 'd')}
              </button>
            </div>
          )
        })}
      </div>

      {/* Time slot chips */}
      {selectedDate && (
        <div>
          <p className="text-xs font-medium text-gray-500 mb-2">
            Available times for {format(selectedDate, 'EEE, d MMM')}
          </p>
          {timeSlotsForDay.length === 0 ? (
            <p className="text-xs text-gray-400">No times available for this date.</p>
          ) : (
            <div className="flex flex-wrap gap-2">
              {timeSlotsForDay.map((slot) => (
                <button
                  key={slot}
                  type="button"
                  onClick={() => onChange(slot)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                    selected === slot
                      ? 'bg-teal-600 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-teal-50 hover:text-teal-700'
                  }`}
                >
                  {formatTime(slot)}
                </button>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
