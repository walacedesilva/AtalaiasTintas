/**
 * T041 — ClienteQuickSearch: debounced client lookup with keyboard navigation.
 */
import { useState, useRef, useEffect, useCallback } from 'react';
import { Search, User } from 'lucide-react';
import { salesAPI } from '@/api/sales';
import type { Cliente } from '@/types';

interface ClienteQuickSearchProps {
  onSelect: (cliente: Cliente | null) => void;
  placeholder?: string;
  autoFocus?: boolean;
}

export default function ClienteQuickSearch({
  onSelect,
  placeholder = 'Buscar cliente por nome, CPF ou CNPJ…',
  autoFocus = false,
}: ClienteQuickSearchProps) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<Cliente[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const [activeIdx, setActiveIdx] = useState(-1);
  const [selectedLabel, setSelectedLabel] = useState('');

  const inputRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLUListElement>(null);
  const abortRef = useRef<AbortController | null>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const search = useCallback(async (q: string) => {
    if (q.length < 2) {
      setResults([]);
      setIsOpen(false);
      return;
    }

    // Cancel previous request
    abortRef.current?.abort();
    abortRef.current = new AbortController();

    try {
      const data = await salesAPI.clientes.list({ search: q, ativo: true, page_size: 8 });
      setResults(data.results);
      setIsOpen(true);
      setActiveIdx(-1);
    } catch {
      // Aborted or network error — ignore
    }
  }, []);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value;
    setQuery(val);
    setSelectedLabel('');

    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => search(val), 300);
  };

  const handleSelect = (cliente: Cliente) => {
    setSelectedLabel(cliente.nome_completo);
    setQuery('');
    setResults([]);
    setIsOpen(false);
    onSelect(cliente);
  };

  const handleClear = () => {
    setSelectedLabel('');
    setQuery('');
    setResults([]);
    setIsOpen(false);
    onSelect(null);
    inputRef.current?.focus();
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!isOpen) return;
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setActiveIdx((prev) => Math.min(prev + 1, results.length - 1));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setActiveIdx((prev) => Math.max(prev - 1, -1));
    } else if (e.key === 'Enter' && activeIdx >= 0) {
      e.preventDefault();
      handleSelect(results[activeIdx]);
    } else if (e.key === 'Escape') {
      setIsOpen(false);
    }
  };

  // Scroll active item into view (optional chaining guards jsdom environments)
  useEffect(() => {
    if (listRef.current && activeIdx >= 0) {
      const item = listRef.current.children[activeIdx] as HTMLElement;
      item?.scrollIntoView?.({ block: 'nearest' });
    }
  }, [activeIdx]);

  useEffect(() => {
    if (autoFocus) inputRef.current?.focus();
  }, [autoFocus]);

  const displayValue = selectedLabel || query;

  return (
    <div className="relative w-full" onBlur={(e) => {
      if (!e.currentTarget.contains(e.relatedTarget as Node)) setIsOpen(false);
    }}>
      <div className="relative flex items-center">
        <Search className="pointer-events-none absolute left-3 h-4 w-4 text-slate-400" aria-hidden="true" />
        <input
          ref={inputRef}
          type="text"
          value={displayValue}
          onChange={handleChange}
          onFocus={() => { if (results.length > 0) setIsOpen(true); }}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          className="form-input w-full pl-9 pr-8"
          role="combobox"
          aria-expanded={isOpen}
          aria-controls="cliente-search-results"
          aria-autocomplete="list"
          aria-activedescendant={activeIdx >= 0 ? `cliente-opt-${activeIdx}` : undefined}
        />
        {(displayValue) && (
          <button
            type="button"
            onClick={handleClear}
            className="absolute right-2 rounded p-1 text-slate-400 hover:text-slate-600"
            aria-label="Limpar seleção de cliente"
          >
            ×
          </button>
        )}
      </div>

      {isOpen && results.length > 0 && (
        <ul
          ref={listRef}
          id="cliente-search-results"
          role="listbox"
          className="absolute left-0 right-0 top-full z-50 mt-1 max-h-56 overflow-auto rounded-xl border border-slate-200 bg-white shadow-lg"
          aria-label="Resultados da busca de clientes"
        >
          {results.map((c, idx) => (
            <li
              key={c.id}
              id={`cliente-opt-${idx}`}
              role="option"
              aria-selected={idx === activeIdx}
              className={`flex cursor-pointer items-center gap-3 px-3 py-2.5 text-sm transition-colors ${
                idx === activeIdx ? 'bg-brand-50 text-brand-700' : 'text-slate-700 hover:bg-slate-50'
              }`}
              onMouseDown={(e) => { e.preventDefault(); handleSelect(c); }}
            >
              <User className="h-4 w-4 shrink-0 text-slate-400" aria-hidden="true" />
              <div>
                <div className="font-medium">{c.nome_completo}</div>
                <div className="text-[11px] text-slate-400">
                  {c.tipo_cliente} · {c.cpf ?? c.cnpj ?? '—'}
                </div>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
