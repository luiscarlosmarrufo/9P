import Link from "next/link";
import { Button } from "@/components/ui/button";

export default function Navigation() {
  return (
    <nav className="w-full bg-white/80 backdrop-blur-sm border-b border-gray-200 fixed top-0 z-50">
      <div className="container mx-auto px-4 py-4 flex items-center justify-between">
        <Link href="/" className="flex items-center">
          <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
            9P Social Analytics
          </h1>
        </Link>
        <div className="flex items-center gap-4">
          <Link href="/settings">
            <Button variant="outline">Settings</Button>
          </Link>
        </div>
      </div>
    </nav>
  );
}
