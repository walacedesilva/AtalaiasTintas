import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { inventoryAPI, type EstoqueFilters, type EntradaManualPayload } from '@/api/inventory';

export const inventoryKeys = {
  all: ['inventory'] as const,
  estoque: () => [...inventoryKeys.all, 'estoque'] as const,
  estoqueList: (filters?: EstoqueFilters) => [...inventoryKeys.estoque(), 'list', filters] as const,
  estoqueResumo: (loja_id?: number) => [...inventoryKeys.estoque(), 'resumo', loja_id] as const,
  lotes: () => [...inventoryKeys.all, 'lotes'] as const,
  lotesProximos: (loja_id: number, dias?: number) => [...inventoryKeys.lotes(), 'proximos', loja_id, dias] as const,
  entradas: () => [...inventoryKeys.all, 'entradas'] as const,
  entradasList: (loja_id?: number) => [...inventoryKeys.entradas(), 'list', loja_id] as const,
};

export function useEstoqueResumo(loja_id?: number) {
  return useQuery({
    queryKey: inventoryKeys.estoqueResumo(loja_id),
    queryFn: () => inventoryAPI.estoque.resumo(loja_id),
    staleTime: 60 * 1000,
  });
}

export function useEstoqueLoja(filters?: EstoqueFilters) {
  return useQuery({
    queryKey: inventoryKeys.estoqueList(filters),
    queryFn: () => inventoryAPI.estoque.list(filters),
    staleTime: 30 * 1000,
  });
}

export function useLotesProximosVencimento(loja_id: number, dias = 30) {
  return useQuery({
    queryKey: inventoryKeys.lotesProximos(loja_id, dias),
    queryFn: () => inventoryAPI.lotes.proximosVencimento(loja_id, dias),
    enabled: loja_id > 0,
    staleTime: 5 * 60 * 1000,
  });
}

export function useEntradas(loja_id?: number) {
  return useQuery({
    queryKey: inventoryKeys.entradasList(loja_id),
    queryFn: () => inventoryAPI.entradas.list(loja_id),
    staleTime: 30 * 1000,
  });
}

export function useImportarXmlNFe() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ loja_id, file }: { loja_id: number; file: File }) =>
      inventoryAPI.entradas.importarXml(loja_id, file),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: inventoryKeys.entradas() });
      queryClient.invalidateQueries({ queryKey: inventoryKeys.estoque() });
    },
  });
}

export function useConfirmarEntrada() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => inventoryAPI.entradas.confirmar(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: inventoryKeys.entradas() });
      queryClient.invalidateQueries({ queryKey: inventoryKeys.estoque() });
      queryClient.invalidateQueries({ queryKey: inventoryKeys.lotes() });
    },
  });
}

export function useCriarEntradaManual() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: EntradaManualPayload) => inventoryAPI.entradas.criarManual(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: inventoryKeys.entradas() });
    },
  });
}
