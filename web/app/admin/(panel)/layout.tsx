import { requireAdmin } from '@/lib/auth'
import { AdminNav } from '@/components/AdminNav'
import { logout } from '../login/actions'

export const dynamic = 'force-dynamic'

export default async function PanelLayout({ children }: { children: React.ReactNode }) {
  await requireAdmin()
  return (
    <div className="flex flex-col gap-6 lg:flex-row">
      <AdminNav logout={logout} />
      <div className="min-w-0 flex-1">{children}</div>
    </div>
  )
}
