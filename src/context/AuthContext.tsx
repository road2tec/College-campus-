"use client";
import { Admin } from "@/Types";
import { createContext, useContext, useState, useEffect, ReactNode } from "react";
import { useRouter } from "next/navigation";

interface UserContextType {
  user: Admin | null;
  setUser: (user: Admin | null) => void;
  login: (userData: Admin) => void;
  logout: () => void;
  isLoading: boolean;
}

const AuthContext = createContext<UserContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<Admin | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    // Check local storage on initial load
    const stored = localStorage.getItem("vidya_admin_user");
    if (stored) {
      try {
        setUser(JSON.parse(stored));
      } catch (e) {
        console.error("Failed to parse user data");
        localStorage.removeItem("vidya_admin_user");
      }
    }
    setIsLoading(false);
  }, []);

  const login = (userData: Admin) => {
    setUser(userData);
    localStorage.setItem("vidya_admin_user", JSON.stringify(userData));
    router.push("/admin/dashboard");
  };

  const logout = () => {
    setUser(null);
    localStorage.removeItem("vidya_admin_user");
    router.push("/login");
  };

  return (
    <AuthContext.Provider value={{ user, setUser, login, logout, isLoading }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};
