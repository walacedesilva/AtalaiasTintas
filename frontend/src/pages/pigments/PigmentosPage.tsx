import React from 'react';

/**
 * Placeholder page for Pigmentos
 * TODO: Implement full pigments management functionality
 */
export default function PigmentosPage(): React.ReactElement {
  return (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h1 className="text-2xl font-bold text-gray-900 mb-4">
          Gestão de Pigmentos
        </h1>
        <p className="text-gray-600 mb-6">
          Gerenciamento completo dos pigmentos utilizados nas misturas de tinta.
        </p>
        
        {/* Placeholder content */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex">
            <div className="text-blue-400 mr-3">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
              </svg>
            </div>
            <div>
              <h3 className="text-blue-800 font-medium">Em Desenvolvimento</h3>
              <p className="text-blue-700 text-sm mt-1">
                Esta página está sendo desenvolvida. Em breve você poderá gerenciar todos os pigmentos do sistema.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}