import { NavLink } from "react-router-dom"
import { FileText, MessageSquare, BarChart3, BookOpen } from "lucide-react"
import { cn } from "@/lib/utils"

const navItems = [
  { to: "/", label: "Documents", icon: FileText },
  { to: "/chat", label: "Chat", icon: MessageSquare },
  { to: "/status", label: "Status", icon: BarChart3 },
]

export function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-background">
      <header className="sticky top-0 z-40 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="flex h-14 items-center gap-4 px-4 max-w-5xl mx-auto">
          <BookOpen className="h-5 w-5 text-primary" />
          <span className="font-semibold">AI Research Assistant</span>
          <nav className="flex items-center gap-1 ml-auto">
            {navItems.map(({ to, label, icon: Icon }) => (
              <NavLink
                key={to}
                to={to}
                className={({ isActive }) =>
                  cn(
                    "inline-flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm font-medium transition-colors",
                    isActive
                      ? "bg-primary/10 text-primary"
                      : "text-muted-foreground hover:text-foreground"
                  )
                }
              >
                <Icon className="h-4 w-4" />
                {label}
              </NavLink>
            ))}
          </nav>
        </div>
      </header>
      <main className="max-w-5xl mx-auto p-4">
        {children}
      </main>
    </div>
  )
}
