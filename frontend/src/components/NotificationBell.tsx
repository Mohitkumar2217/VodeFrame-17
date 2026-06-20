'use client';

import { Bell } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';
import { motion, AnimatePresence } from "framer-motion";
import { auth } from "../lib/auth";

interface Notification {
  id: number;
  message: string;
  read: boolean;
  createdAt: string;
}

export default function NotificationBell() {
  const [count, setCount] = useState(0);
  const [open, setOpen] = useState(false);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const hasFetched = useRef(false);
  const loginUser = auth.getUser();

  useEffect(() => {
    if (!loginUser?.id || hasFetched.current) return;
    hasFetched.current = true;

    const fetchNotifications = async () => {
      try {
        const res = await fetch(
          `/api/notifications/${loginUser.id}`
        );

        if (!res.ok) {
          throw new Error('Failed to fetch notifications');
        }

        const data: Notification[] = await res.json();

        setNotifications(data);

        setCount(
          data.filter((item) => !item.read).length
        );
      } catch (error) {
        console.error('Notification Error:', error);
      }
    };

    fetchNotifications();
  }, [loginUser?.id]);

  return (
    <div className="relative">
      <button
        className="relative"
        onClick={() => setOpen((prev) => !prev)}
      >
        <Bell size={22} />

        {count > 0 && (
          <span className="absolute -top-2 -right-2 flex h-5 w-5 items-center justify-center rounded-full bg-red-500 text-xs text-white">
            {count}
          </span>
        )}
      </button>

      {open && (
        <>
          <div className="relative">
            <button onClick={() => setOpen(!open)}>
              {/* Bell Icon */}
            </button>

            <AnimatePresence>
              {open && (
                <motion.div
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  transition={{ duration: 0.2 }}
                  className="absolute right-0 mt-2 z-50 w-80 overflow-hidden rounded-2xl bg-white/10 backdrop-blur-lg border border-white/10 shadow-2xl"
                >
                  <div className="border-b border-white/10 p-4">
                    <h3 className="font-semibold text-white">
                      Notifications
                    </h3>
                  </div>

                  <div className="max-h-96 overflow-y-auto">
                    {notifications.length === 0 ? (
                      <p className="p-4 text-sm text-gray-300">
                        No notifications
                      </p>
                    ) : (
                      notifications.map((notification) => (
                        <button
                          key={notification.id}
                          className={`w-full text-left border-b border-white/10 p-4 transition-colors hover:bg-white/20 ${!notification.read ? "bg-white/5" : ""
                            }`}
                        >
                          <p className="text-sm text-white">
                            {notification.message}
                          </p>

                          <p className="mt-1 text-xs text-gray-300">
                            {new Date(
                              notification.createdAt
                            ).toLocaleString()}
                          </p>
                        </button>
                      ))
                    )}
                  </div>

                  <div className="p-3 border-t border-white/10">
                    <button
                      onClick={() => setOpen(false)}
                      className="w-full rounded-md px-4 py-2 text-white hover:bg-white/20 transition-colors"
                    >
                      Close
                    </button>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </>
      )}
    </div>
  );
}