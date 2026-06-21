import { NavLink, Route, Routes } from "react-router-dom";

import ClusterDetail from "./pages/ClusterDetail";
import Clusters from "./pages/Clusters";
import Dashboard from "./pages/Dashboard";
import Search from "./pages/Search";

const navItems = [
  { to: "/", label: "Dashboard" },
  { to: "/clusters", label: "Clusters" },
  { to: "/search", label: "Search" },
];

export default function App() {
  return (
    <div className="min-h-screen bg-panel text-ink">
      <header className="border-b border-line bg-white">
        <div className="mx-auto flex max-w-7xl flex-col gap-4 px-4 py-4 sm:flex-row sm:items-center sm:justify-between lg:px-6">
          <div>
            <h1 className="text-xl font-semibold tracking-normal">Passport Monitor</h1>
            <p className="text-sm text-slate-600">Social media intelligence dashboard</p>
          </div>
          <nav className="flex gap-2">
            {navItems.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.to === "/"}
                className={({ isActive }) =>
                  [
                    "rounded-md px-3 py-2 text-sm font-medium transition",
                    isActive
                      ? "bg-ink text-white"
                      : "text-slate-700 hover:bg-slate-100 hover:text-ink",
                  ].join(" ")
                }
              >
                {item.label}
              </NavLink>
            ))}
          </nav>
        </div>
      </header>
      <main className="mx-auto max-w-7xl px-4 py-6 lg:px-6">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/clusters" element={<Clusters />} />
          <Route path="/clusters/:clusterId" element={<ClusterDetail />} />
          <Route path="/search" element={<Search />} />
        </Routes>
      </main>
    </div>
  );
}
