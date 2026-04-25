"use client";

import { useEffect, useRef } from "react";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { logoutAction } from "../actions/auth";

export default function UserMenu() {
  const menuRef = useRef<HTMLDetailsElement>(null);
  const pathname = usePathname();

  useEffect(() => {
    if (menuRef.current) {
      menuRef.current.open = false;
    }
  }, [pathname]);

  useEffect(() => {
    const closeOnOutsideClick = (event: MouseEvent) => {
      const menu = menuRef.current;
      if (menu?.open && event.target instanceof Node && !menu.contains(event.target)) {
        menu.open = false;
      }
    };

    document.addEventListener("mousedown", closeOnOutsideClick);
    return () => document.removeEventListener("mousedown", closeOnOutsideClick);
  }, []);

  const closeMenu = () => {
    if (menuRef.current) {
      menuRef.current.open = false;
    }
  };

  return (
    <details className="user-menu" ref={menuRef}>
      <summary className="user-menu-trigger">
        <span className="avatar-shell minimal" aria-hidden="true" />
        <span className="user-menu-arrow" aria-hidden="true">
          ▾
        </span>
      </summary>

      <div className="user-menu-panel">
        <Link href="/account" className="user-menu-item" onClick={closeMenu}>
          Account
        </Link>
        <form
          action={async () => {
            closeMenu();
            await logoutAction();
          }}
        >
          <button type="submit" className="user-menu-item danger">
            Log out
          </button>
        </form>
      </div>
    </details>
  );
}
