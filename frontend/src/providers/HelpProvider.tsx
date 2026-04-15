import React, { createContext, useCallback, useContext, useState } from 'react';

interface HelpContextValue {
  isOpen: boolean;
  activeRoute: string | null;
  open: (route?: string) => void;
  close: () => void;
}

const HelpContext = createContext<HelpContextValue | null>(null);

export function HelpProvider({ children }: { children: React.ReactNode }) {
  const [isOpen, setIsOpen] = useState(false);
  const [activeRoute, setActiveRoute] = useState<string | null>(null);

  const open = useCallback((route?: string) => {
    setActiveRoute(route ?? null);
    setIsOpen(true);
  }, []);

  const close = useCallback(() => {
    setIsOpen(false);
  }, []);

  return (
    <HelpContext.Provider value={{ isOpen, activeRoute, open, close }}>
      {children}
    </HelpContext.Provider>
  );
}

export function useHelp(): HelpContextValue {
  const ctx = useContext(HelpContext);
  if (!ctx) throw new Error('useHelp must be used inside HelpProvider');
  return ctx;
}
