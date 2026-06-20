"use client";

import React, { useState, useEffect } from "react";
import Image from "next/image";
import Link from "next/link";
import { useRouter, usePathname } from "next/navigation";
import { auth } from "../lib/auth";
import { motion, AnimatePresence } from "framer-motion";
import NotificationBell from "./NotificationBell";

const Navigation = () => {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [isLanguageMenuOpen, setIsLanguageMenuOpen] = useState(false);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const router = useRouter();
  const pathname = usePathname();

  // Authentication Check 
  useEffect(() => {
    const checkAuth = () => {
      setIsAuthenticated(auth.isAuthenticated());
    };
    checkAuth();

    const handleStorageChange = () => checkAuth();
    window.addEventListener('storage', handleStorageChange);

    return () => window.removeEventListener('storage', handleStorageChange);
  }, [pathname]);

  const navigationItems = [
    { name: "Add & Manage DPR", href: "/portal" },
    { name: "AI Chatbot", href: "/chatbot" },
    { name: "Evaluation Demo", href: "/demo" },
    { name: "How to Analyze DPR", href: "/details" },
  ];

  const handleScrollTo = (href: string) => {
    const targetId = href.substring(1);
    const element = document.getElementById(targetId);
    if (element) {
      element.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  };

  const handleNavigation = (href: string) => {
    if (href.startsWith("/")) router.push(href);
    else handleScrollTo(href);
  };

  const languages = [
    { code: "en", nativeName: "English" },
    { code: "hi", nativeName: "हिंदी" },
    { code: "as", nativeName: "অসমীয়া" },
    { code: "bn", nativeName: "বাংলা" },
  ];

  const [currentLanguage, setCurrentLanguage] = useState(languages[0]);

  const handleLogout = () => {
    auth.logout();
    router.push("/");
  };

  return (
    <header className="fixed top-0 left-0 w-full z-50">
      <div className="backdrop-blur-md bg-black/30 border-b border-white/20 shadow-lg rounded-b-2xl">
        <div className="flex items-center justify-between px-6 md:px-12 h-20">

          {/* Logo */}
          <Link href="/" className="flex items-center gap-4">
            <Image
              src="/mdoner-logo-dark.png"
              alt="DPR Portal Logo"
              width={260}
              height={80}
              className="h-12 w-auto"
            />
          </Link>

          {/* Desktop Nav */}
          <div className="hidden md:flex items-center gap-6">
            <nav className="flex gap-4">
              {navigationItems.map((item) => (
                <button
                  key={item.name}
                  onClick={() => handleNavigation(item.href)}
                  className="relative text-sm font-medium text-gray-300 hover:text-blue-400"
                >
                  {item.name}
                </button>
              ))}
              {isAuthenticated ? <NotificationBell /> : <></>}
            </nav>

            {/* Language Drop-down */}
            <div className="relative">
              <button
                onClick={() => setIsLanguageMenuOpen(!isLanguageMenuOpen)}
                className="flex items-center gap-2 bg-white/10 text-white px-4 py-2 rounded-xl"
              >
                {currentLanguage.nativeName}
              </button>

              <AnimatePresence>
                {isLanguageMenuOpen && (
                  <motion.div
                    initial={{ opacity: 0, y: -10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                    className="absolute right-0 mt-2 w-56 bg-white/10 p-2 rounded-2xl"
                  >
                    {languages.map((lang) => (
                      <button
                        key={lang.code}
                        onClick={() => {
                          setCurrentLanguage(lang);
                          setIsLanguageMenuOpen(false);
                        }}
                        className="w-full text-left px-4 py-2 text-white hover:bg-white/20 rounded-md"
                      >
                        {lang.nativeName}
                      </button>
                    ))}
                  </motion.div>
                )}
              </AnimatePresence>
            </div>

            {/* Auth */}
            {isAuthenticated ? (
              <button
                onClick={handleLogout}
                className="bg-red-600 px-4 py-2 rounded-md text-white"
              >
                Logout
              </button>
            ) : (
              <Link
                href="/login"
                className="bg-blue-600 px-4 py-2 rounded-md text-white"
              >
                Login to Access
              </Link>
            )}

          </div>

          {/* Mobile Menu Toggle */}
          <div className="md:hidden text-gray-300 flex gap-5">
            <NotificationBell/>
            <button
              onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)} 
            >
              ☰
            </button>
          </div>
        </div>

        <AnimatePresence>
          {isMobileMenuOpen && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              exit={{ opacity: 0, height: 0 }}
              transition={{ duration: 0.3 }}
              className="md:hidden overflow-hidden bg-black/80 px-4 py-4"
            >
              <div className="flex flex-col space-y-3">
                {navigationItems.map((item) => (
                  <button
                    key={item.name}
                    onClick={() => {
                      handleNavigation(item.href);
                      setIsMobileMenuOpen(false);
                    }}
                    className="text-left text-gray-300 hover:text-white transition-colors"
                  >
                    {item.name}
                  </button>
                ))}
                {isAuthenticated ? (
                  <button
                    onClick={handleLogout}
                    className="bg-red-600 px-4 py-2 rounded-md text-white"
                  >
                    Logout
                  </button>
                ) : (
                  <Link
                    href="/login"
                    className="bg-blue-600 px-4 py-2 rounded-md text-white"
                  >
                    Login to Access
                  </Link>
                )}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </header>
  );
};

export default Navigation;
