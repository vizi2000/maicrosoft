import { useAuthStore } from '../../stores/authStore'

export default function Header() {
  const { user, logout } = useAuthStore()

  return (
    <header className="bg-white shadow-sm border-b">
      <div className="flex items-center justify-between px-6 py-4">
        <div></div>
        <div className="flex items-center gap-4">
          {user && (
            <>
              <span className="text-sm text-gray-600">{user.email}</span>
              <button
                onClick={logout}
                className="text-sm text-red-600 hover:text-red-800"
              >
                Logout
              </button>
            </>
          )}
        </div>
      </div>
    </header>
  )
}
