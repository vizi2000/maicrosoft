/**
 * NodePalette - Sidebar with draggable particles
 * Grouped by category, searchable
 */

import { useState, useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  MagnifyingGlassIcon,
  GlobeAltIcon,
  CircleStackIcon,
  DocumentIcon,
  ArrowPathIcon,
  ArrowsRightLeftIcon,
  ArrowPathRoundedSquareIcon,
  CpuChipIcon,
  ArchiveBoxIcon,
  QueueListIcon,
  DocumentTextIcon,
} from '@heroicons/react/24/outline'
import { primitivesApi } from '../../api/client'
import clsx from 'clsx'

const categoryLabels: Record<string, string> = {
  data: 'Data',
  transform: 'Transform',
  control: 'Control Flow',
  storage: 'Storage',
  messaging: 'Messaging',
  ai: 'AI/LLM',
  observability: 'Observability',
  scaffold: 'Scaffolding',
}

const categoryColors: Record<string, string> = {
  data: 'bg-blue-500',
  transform: 'bg-purple-500',
  control: 'bg-amber-500',
  storage: 'bg-emerald-500',
  messaging: 'bg-red-500',
  ai: 'bg-indigo-500',
  observability: 'bg-slate-500',
  scaffold: 'bg-cyan-500',
}

const particleIcons: Record<string, React.ComponentType<any>> = {
  P001: GlobeAltIcon,
  P002: CircleStackIcon,
  P003: DocumentIcon,
  P004: ArrowPathIcon,
  P005: ArrowsRightLeftIcon,
  P006: ArrowPathRoundedSquareIcon,
  P007: CpuChipIcon,
  P008: ArchiveBoxIcon,
  P009: QueueListIcon,
  P010: DocumentTextIcon,
}

interface Primitive {
  id: string
  name: string
  description: string
  category: string
  status: string
}

export default function NodePalette() {
  const [search, setSearch] = useState('')
  const [expandedCategories, setExpandedCategories] = useState<Set<string>>(
    new Set(['data', 'control'])
  )

  // Fetch primitives from API
  const { data: primitives = [], isLoading } = useQuery({
    queryKey: ['primitives'],
    queryFn: async () => {
      const response = await primitivesApi.list()
      return response.data.primitives || response.data
    },
  })

  // Filter and group by category
  const filteredPrimitives = useMemo(() => {
    const filtered = primitives.filter((p: Primitive) =>
      p.name.toLowerCase().includes(search.toLowerCase()) ||
      p.description.toLowerCase().includes(search.toLowerCase())
    )

    // Group by category
    const grouped: Record<string, Primitive[]> = {}
    for (const p of filtered) {
      const cat = p.category || 'other'
      if (!grouped[cat]) grouped[cat] = []
      grouped[cat].push(p)
    }

    return grouped
  }, [primitives, search])

  // Handle drag start
  const handleDragStart = (event: React.DragEvent, primitive: Primitive) => {
    event.dataTransfer.setData(
      'application/maicrosoft-primitive',
      JSON.stringify(primitive)
    )
    event.dataTransfer.effectAllowed = 'move'
  }

  // Toggle category expansion
  const toggleCategory = (category: string) => {
    setExpandedCategories((prev) => {
      const next = new Set(prev)
      if (next.has(category)) {
        next.delete(category)
      } else {
        next.add(category)
      }
      return next
    })
  }

  return (
    <div className="w-64 bg-white border-r border-gray-200 flex flex-col h-full">
      {/* Search */}
      <div className="p-3 border-b border-gray-200">
        <div className="relative">
          <MagnifyingGlassIcon className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search particles..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>
      </div>

      {/* Primitives list */}
      <div className="flex-1 overflow-y-auto p-2">
        {isLoading ? (
          <div className="text-center py-4 text-gray-500">Loading...</div>
        ) : (
          Object.entries(filteredPrimitives).map(([category, items]) => (
            <div key={category} className="mb-2">
              {/* Category header */}
              <button
                onClick={() => toggleCategory(category)}
                className="w-full flex items-center justify-between px-2 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-100 rounded"
              >
                <span>{categoryLabels[category] || category}</span>
                <span className="text-xs text-gray-400">{items.length}</span>
              </button>

              {/* Category items */}
              {expandedCategories.has(category) && (
                <div className="mt-1 space-y-1">
                  {items.map((primitive) => {
                    const Icon = particleIcons[primitive.id] || DocumentIcon
                    return (
                      <div
                        key={primitive.id}
                        draggable
                        onDragStart={(e) => handleDragStart(e, primitive)}
                        className={clsx(
                          'flex items-center gap-2 px-2 py-2 rounded-lg cursor-grab active:cursor-grabbing transition-colors',
                          'hover:bg-gray-100 border border-transparent hover:border-gray-200'
                        )}
                      >
                        <div
                          className={clsx(
                            'w-8 h-8 rounded flex items-center justify-center text-white',
                            categoryColors[category] || 'bg-gray-500'
                          )}
                        >
                          <Icon className="w-4 h-4" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="text-sm font-medium text-gray-900 truncate">
                            {primitive.name}
                          </div>
                          <div className="text-xs text-gray-500 truncate">
                            {primitive.id}
                          </div>
                        </div>
                      </div>
                    )
                  })}
                </div>
              )}
            </div>
          ))
        )}
      </div>

      {/* Help text */}
      <div className="p-3 border-t border-gray-200 bg-gray-50">
        <p className="text-xs text-gray-500 text-center">
          Drag particles to the canvas to build your workflow
        </p>
      </div>
    </div>
  )
}
