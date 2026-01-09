import { Link, useLocation } from 'react-router-dom'
import {
  HomeIcon,
  BoltIcon,
  DocumentDuplicateIcon,
  ClockIcon,
  KeyIcon,
  CodeBracketIcon,
  Cog6ToothIcon,
} from '@heroicons/react/24/outline'
import clsx from 'clsx'

const navigation = [
  { name: 'Dashboard', href: '/', icon: HomeIcon },
  { name: 'Workflows', href: '/workflows', icon: BoltIcon },
  { name: 'Templates', href: '/templates', icon: DocumentDuplicateIcon },
  { name: 'Run History', href: '/runs', icon: ClockIcon },
  { name: 'Secrets', href: '/secrets', icon: KeyIcon },
  { name: 'Analyze Repo', href: '/analyze', icon: CodeBracketIcon },
  { name: 'Settings', href: '/settings', icon: Cog6ToothIcon },
]

export default function Sidebar() {
  const location = useLocation()

  return (
    <div className="w-64 bg-gray-900 text-white">
      <div className="p-4">
        <h1 className="text-xl font-bold">Maicrosoft</h1>
        <p className="text-xs text-gray-400">Primitives-First AI</p>
      </div>
      <nav className="mt-4">
        {navigation.map((item) => (
          <Link
            key={item.name}
            to={item.href}
            className={clsx(
              'flex items-center px-4 py-3 text-sm',
              location.pathname === item.href
                ? 'bg-gray-800 text-white'
                : 'text-gray-300 hover:bg-gray-800'
            )}
          >
            <item.icon className="w-5 h-5 mr-3" />
            {item.name}
          </Link>
        ))}
      </nav>
    </div>
  )
}
