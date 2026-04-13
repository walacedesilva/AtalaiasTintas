import React from 'react';
import type { Pigmento } from '@/types';

/**
 * PigmentCard component
 * Displays pigment information in a card format with actions
 */

interface PigmentCardProps {
  pigmento: Pigmento;
  onEdit?: (pigmento: Pigmento) => void;
  onDelete?: (pigmento: Pigmento) => void;
}

export function PigmentCard({ pigmento, onEdit, onDelete }: PigmentCardProps): React.ReactElement {
  const formatPrice = (price: string): string => {
    const numPrice = parseFloat(price);
    return `R$ ${numPrice.toFixed(2).replace('.', ',')}`;
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow duration-200">
      {/* Header with Name and Status */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <div className="flex items-center space-x-3 mb-2">
            <h3 className="text-lg font-semibold text-gray-900">{pigmento.nome}</h3>
            <span
              className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                pigmento.ativo
                  ? 'bg-green-100 text-green-800'
                  : 'bg-red-100 text-red-800'
              }`}
              aria-label={`Status: ${pigmento.ativo ? 'Ativo' : 'Inativo'}`}
            >
              {pigmento.ativo ? 'Ativo' : 'Inativo'}
            </span>
          </div>
          <p className="text-sm text-gray-600 font-mono">{pigmento.codigo}</p>
        </div>

        {/* Color Preview */}
        <div 
          className="w-12 h-12 rounded-lg border-2 border-gray-200 flex-shrink-0"
          style={{ backgroundColor: pigmento.cor_hex }}
          aria-label={`Cor ${pigmento.nome}`}
          title={`Cor ${pigmento.nome}: ${pigmento.cor_hex}`}
        />
      </div>

      {/* Properties */}
      <div className="space-y-3">
        <div className="flex justify-between items-center">
          <span className="text-sm text-gray-600">Densidade:</span>
          <span className="text-sm font-medium text-gray-900">{pigmento.densidade}</span>
        </div>

        <div className="flex justify-between items-center">
          <span className="text-sm text-gray-600">Preço por litro:</span>
          <span 
            className="text-sm font-semibold text-blue-600"
            aria-label={`Preço por litro: ${formatPrice(pigmento.preco_litro)}`}
          >
            {formatPrice(pigmento.preco_litro)}
          </span>
        </div>

        <div className="flex justify-between items-center">
          <span className="text-sm text-gray-600">Cor:</span>
          <span className="text-sm font-mono text-gray-900">{pigmento.cor_hex}</span>
        </div>

        {/* Observations */}
        {pigmento.observacoes && (
          <div className="pt-3 border-t border-gray-100">
            <p className="text-sm text-gray-600">
              <span className="font-medium">Observações:</span>
            </p>
            <p className="text-sm text-gray-700 mt-1">{pigmento.observacoes}</p>
          </div>
        )}
      </div>

      {/* Action Buttons */}
      {(onEdit || onDelete) && (
        <div className="flex justify-end space-x-2 mt-4 pt-4 border-t border-gray-100">
          {onEdit && (
            <button
              type="button"
              onClick={() => onEdit(pigmento)}
              className="px-3 py-2 text-sm font-medium text-blue-600 bg-blue-50 rounded-md hover:bg-blue-100 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors"
              aria-label={`Editar pigmento ${pigmento.nome}`}
            >
              Editar
            </button>
          )}
          {onDelete && (
            <button
              type="button"
              onClick={() => onDelete(pigmento)}
              className="px-3 py-2 text-sm font-medium text-red-600 bg-red-50 rounded-md hover:bg-red-100 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2 transition-colors"
              aria-label={`Excluir pigmento ${pigmento.nome}`}
            >
              Excluir
            </button>
          )}
        </div>
      )}
    </div>
  );
}