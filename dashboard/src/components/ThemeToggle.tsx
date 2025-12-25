"use client";

import * as React from "react";
import { Moon, Sun, Monitor } from "lucide-react";
import { useTheme } from "next-themes";

export function ThemeToggle() {
    const { theme, setTheme } = useTheme();
    const [mounted, setMounted] = React.useState(false);

    React.useEffect(() => {
        setMounted(true);
    }, []);

    if (!mounted) {
        return <div className="p-2 w-9 h-9" />;
    }

    return (
        <div className="flex items-center gap-1 p-1 bg-zinc-50 dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-sm">
            <button
                onClick={() => setTheme("light")}
                className={`p-1.5 rounded-sm transition-colors ${theme === "light"
                    ? "bg-white text-zinc-950 shadow-sm ring-1 ring-zinc-200"
                    : "text-zinc-500 hover:text-zinc-800"
                    }`}
                title="Light Mode"
            >
                <Sun className="w-3.5 h-3.5" />
            </button>
            <button
                onClick={() => setTheme("system")}
                className={`p-1.5 rounded-sm transition-colors ${theme === "system"
                    ? "bg-white dark:bg-zinc-800 text-zinc-950 dark:text-zinc-50 shadow-sm ring-1 ring-zinc-200 dark:ring-zinc-700"
                    : "text-zinc-500 hover:text-zinc-800 dark:hover:text-zinc-300"
                    }`}
                title="System Preference"
            >
                <Monitor className="w-3.5 h-3.5" />
            </button>
            <button
                onClick={() => setTheme("dark")}
                className={`p-1.5 rounded-sm transition-colors ${theme === "dark"
                    ? "bg-zinc-800 text-white shadow-sm ring-1 ring-zinc-700"
                    : "text-zinc-500 hover:text-zinc-300"
                    }`}
                title="Dark Mode"
            >
                <Moon className="w-3.5 h-3.5" />
            </button>
        </div>
    );
}
