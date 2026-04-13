import React from 'react';
import { Link } from 'react-router-dom';
import { Paintbrush, ArrowLeft } from 'lucide-react';

export default function NotFoundPage(): React.ReactElement {
  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 px-6">
      <div className="text-center max-w-md">
        <div className="flex h-20 w-20 items-center justify-center rounded-3xl bg-teal-50 mx-auto mb-6">
          <Paintbrush className="h-10 w-10 text-teal-600" aria-hidden="true" />
        </div>
        <h1 className="text-7xl font-black text-slate-200 leading-none">404</h1>
        <h2 className="text-xl font-bold text-slate-900 mt-2 mb-3">Página não encontrada</h2>
        <p className="text-sm text-slate-500 mb-8">
          A página que você procura não existe ou foi movida.
        </p>
        <Link to="/dashboard" className="btn-primary inline-flex">
          <ArrowLeft className="h-4 w-4" aria-hidden="true" />
          Voltar ao Painel
        </Link>
      </div>
    </div>
  );
}