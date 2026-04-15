import React, { useEffect, useRef, useState } from 'react';
import { useLocation } from 'react-router-dom';
import {
  X,
  ChevronRight,
  Lightbulb,
  CheckCircle2,
  BookOpen,
  Construction,
} from 'lucide-react';
import { useHelp } from '@/hooks/useHelp';
import { HELP_DATA, getHelpForRoute, type ScreenHelp } from './helpData';

export function HelpDrawer() {
  const { isOpen, activeRoute, close } = useHelp();
  const location = useLocation();
  const drawerRef = useRef<HTMLDivElement>(null);

  // Determine active screen — prefer explicitly requested route, else current page
  const resolvedRoute = activeRoute ?? location.pathname;
  const initialScreen =
    getHelpForRoute(resolvedRoute) ?? HELP_DATA[0];

  const [selectedScreen, setSelectedScreen] = useState<ScreenHelp>(initialScreen);

  // Sync selectedScreen when open / activeRoute changes
  useEffect(() => {
    if (isOpen) {
      const screen = getHelpForRoute(activeRoute ?? location.pathname) ?? HELP_DATA[0];
      setSelectedScreen(screen);
    }
  }, [isOpen, activeRoute, location.pathname]);

  // Keyboard: Esc to close, ? to open (when not typing in an input)
  const { open } = useHelp();
  useEffect(() => {
    const handleKey = (e: KeyboardEvent) => {
      const tag = (e.target as HTMLElement).tagName;
      const isEditing = tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT' || (e.target as HTMLElement).isContentEditable;
      if (e.key === 'Escape' && isOpen) {
        close();
      } else if (e.key === '?' && !isEditing && !isOpen) {
        e.preventDefault();
        open();
      }
    };
    document.addEventListener('keydown', handleKey);
    return () => document.removeEventListener('keydown', handleKey);
  }, [isOpen, close, open]);

  // Focus trap: focus drawer when opened
  useEffect(() => {
    if (isOpen) drawerRef.current?.focus();
  }, [isOpen]);

  if (!isOpen) return null;

  const Icon = selectedScreen.icon;

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/40 z-40 transition-opacity"
        onClick={close}
        aria-hidden="true"
      />

      {/* Drawer panel */}
      <div
        ref={drawerRef}
        role="dialog"
        aria-modal="true"
        aria-label={`Instruções de uso — ${selectedScreen.label}`}
        tabIndex={-1}
        className="fixed right-0 top-0 h-full w-full max-w-sm z-50 flex flex-col bg-white shadow-2xl outline-none"
      >
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200 bg-gray-50">
          <div className="flex items-center gap-2">
            <BookOpen className="w-4 h-4 text-blue-600" />
            <span className="text-sm font-semibold text-gray-800">
              Instruções de Uso
            </span>
          </div>
          <button
            onClick={close}
            className="p-1.5 rounded-md text-gray-500 hover:bg-gray-200 hover:text-gray-700 transition-colors"
            aria-label="Fechar painel de ajuda"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Body — two-column layout */}
        <div className="flex flex-1 overflow-hidden">
          {/* Left nav — screen list */}
          <nav
            aria-label="Selecionar tela"
            className="w-[120px] flex-shrink-0 bg-gray-50 border-r border-gray-200 overflow-y-auto custom-scrollbar"
          >
            {HELP_DATA.map((screen) => {
              const NavIcon = screen.icon;
              const isActive = screen.route === selectedScreen.route;
              return (
                <button
                  key={screen.route}
                  onClick={() => setSelectedScreen(screen)}
                  className={`
                    w-full flex flex-col items-center gap-1.5 py-3 px-2 text-center border-l-2 transition-colors
                    ${isActive
                      ? 'border-blue-500 bg-white text-blue-700'
                      : 'border-transparent text-gray-500 hover:bg-gray-100 hover:text-gray-700'}
                  `}
                  aria-current={isActive ? 'page' : undefined}
                >
                  <NavIcon className="w-4 h-4" />
                  <span className="text-[11px] font-medium leading-tight">
                    {screen.label}
                  </span>
                </button>
              );
            })}
          </nav>

          {/* Right content */}
          <main className="flex-1 overflow-y-auto custom-scrollbar p-4 space-y-5">
            {/* Screen title */}
            <div>
              <div className="flex items-center gap-2 mb-1">
                <Icon className="w-5 h-5 text-blue-600" />
                <h2 className="text-base font-semibold text-gray-900">
                  {selectedScreen.label}
                </h2>
                {selectedScreen.comingSoon && (
                  <span className="ml-auto flex items-center gap-1 text-[10px] font-medium text-amber-700 bg-amber-100 px-1.5 py-0.5 rounded-full">
                    <Construction className="w-3 h-3" />
                    Em breve
                  </span>
                )}
              </div>
              <p className="text-xs text-gray-500 leading-relaxed">
                {selectedScreen.description}
              </p>
            </div>

            {/* Actions */}
            <div>
              <h3 className="text-xs font-semibold text-gray-700 uppercase tracking-wider mb-2">
                Como fazer
              </h3>
              <div className="space-y-3">
                {selectedScreen.actions.map((action, ai) => (
                  <details
                    key={ai}
                    className="group rounded-lg border border-gray-200 overflow-hidden"
                    open={ai === 0}
                  >
                    <summary className="flex items-center justify-between px-3 py-2 bg-gray-50 hover:bg-gray-100 cursor-pointer list-none text-sm font-medium text-gray-800 select-none">
                      <span>{action.title}</span>
                      <ChevronRight className="w-3.5 h-3.5 text-gray-400 transition-transform group-open:rotate-90" />
                    </summary>
                    <ol className="px-3 py-2 space-y-1.5">
                      {action.steps.map((step, si) => (
                        <li key={si} className="flex gap-2 text-xs text-gray-600">
                          <span className="flex-shrink-0 w-4 h-4 rounded-full bg-blue-100 text-blue-700 text-[10px] font-bold flex items-center justify-center mt-0.5">
                            {si + 1}
                          </span>
                          <span className="leading-relaxed">{step}</span>
                        </li>
                      ))}
                    </ol>
                  </details>
                ))}
              </div>
            </div>

            {/* Tips */}
            {selectedScreen.tips.length > 0 && (
              <div>
                <h3 className="text-xs font-semibold text-gray-700 uppercase tracking-wider mb-2">
                  Dicas
                </h3>
                <ul className="space-y-1.5">
                  {selectedScreen.tips.map((tip, ti) => (
                    <li key={ti} className="flex gap-2 text-xs text-gray-600">
                      <Lightbulb className="w-3.5 h-3.5 text-amber-500 flex-shrink-0 mt-0.5" />
                      <span className="leading-relaxed">{tip}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Keyboard shortcuts */}
            {selectedScreen.shortcuts && selectedScreen.shortcuts.length > 0 && (
              <div>
                <h3 className="text-xs font-semibold text-gray-700 uppercase tracking-wider mb-2">
                  Atalhos
                </h3>
                <ul className="space-y-1.5">
                  {selectedScreen.shortcuts.map((shortcut, si) => (
                    <li key={si} className="flex gap-2 text-xs text-gray-600">
                      <CheckCircle2 className="w-3.5 h-3.5 text-green-500 flex-shrink-0 mt-0.5" />
                      <span className="font-mono leading-relaxed">{shortcut}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </main>
        </div>

        {/* Footer */}
        <div className="px-4 py-2 border-t border-gray-200 bg-gray-50 text-[11px] text-gray-400 text-center">
          Pressione <kbd className="mx-0.5 px-1 py-0.5 bg-white border border-gray-300 rounded text-[10px] font-mono">Esc</kbd> para fechar
        </div>
      </div>
    </>
  );
}
