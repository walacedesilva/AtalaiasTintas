import { useQuery, useMutation, useQueryClient, useInfiniteQuery } from '@tanstack/react-query';
import { tintometryAPI } from '@/api';
import type {
  Pigmento,
  FormulaTintometrica,
  MisturaTinta,
  MisturaCalculationRequest,
  ColorAnalysisRequest,
  SearchFilters,
} from '@/types';

/**
 * Tintometry hooks using React Query
 * Provides reactive state management for all paint mixing operations
 */

// Query keys for React Query cache
export const tintometryKeys = {
  all: ['tintometry'] as const,
  dashboard: () => [...tintometryKeys.all, 'dashboard'] as const,
  pigmentos: () => [...tintometryKeys.all, 'pigmentos'] as const,
  pigmento: (id: number) => [...tintometryKeys.pigmentos(), id] as const,
  cores: () => [...tintometryKeys.all, 'cores'] as const,
  cor: (id: number) => [...tintometryKeys.cores(), id] as const,
  formulas: () => [...tintometryKeys.all, 'formulas'] as const,
  formula: (id: number) => [...tintometryKeys.formulas(), id] as const,
  misturas: () => [...tintometryKeys.all, 'misturas'] as const,
  mistura: (id: number) => [...tintometryKeys.misturas(), id] as const,
  estoque: () => [...tintometryKeys.all, 'estoque'] as const,
  etiquetas: () => [...tintometryKeys.all, 'etiquetas'] as const,
  etiqueta: (id: number) => [...tintometryKeys.etiquetas(), id] as const
};

// Dashboard hooks
export function useDashboardStats() {
  return useQuery({
    queryKey: tintometryKeys.dashboard(),
    queryFn: () => tintometryAPI.getDashboardStats(),
    staleTime: 2 * 60 * 1000, // 2 minutes
    refetchInterval: 5 * 60 * 1000 // Refetch every 5 minutes
  });
}

// Pigmentos hooks
export function usePigmentos(filters?: SearchFilters) {
  return useQuery({
    queryKey: [...tintometryKeys.pigmentos(), filters],
    queryFn: () => tintometryAPI.pigmentos.list(filters),
    staleTime: 5 * 60 * 1000
  });
}

export function usePigmento(id: number) {
  return useQuery({
    queryKey: tintometryKeys.pigmento(id),
    queryFn: () => tintometryAPI.pigmentos.get(id),
    enabled: id > 0
  });
}

export function useCreatePigmento() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (pigmento: Omit<Pigmento, 'id' | 'created_at' | 'updated_at'>) =>
      tintometryAPI.pigmentos.create(pigmento),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: tintometryKeys.pigmentos() });
      queryClient.invalidateQueries({ queryKey: tintometryKeys.estoque() });
    }
  });
}

export function useUpdatePigmento() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<Pigmento> }) =>
      tintometryAPI.pigmentos.update(id, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: tintometryKeys.pigmento(id) });
      queryClient.invalidateQueries({ queryKey: tintometryKeys.pigmentos() });
    }
  });
}

// Cores hooks
export function useCores(filters?: SearchFilters) {
  return useQuery({
    queryKey: [...tintometryKeys.cores(), filters],
    queryFn: () => tintometryAPI.cores.list(filters),
    staleTime: 5 * 60 * 1000
  });
}

export function usePopularCores(limit: number = 10) {
  return useQuery({
    queryKey: [...tintometryKeys.cores(), 'popular', limit],
    queryFn: () => tintometryAPI.cores.getPopular(limit),
    staleTime: 10 * 60 * 1000
  });
}

export function useCor(id: number) {
  return useQuery({
    queryKey: tintometryKeys.cor(id),
    queryFn: () => tintometryAPI.cores.get(id),
    enabled: id > 0
  });
}

export function useSearchCores() {
  return useMutation({
    mutationFn: (query: string) => tintometryAPI.cores.search(query)
  });
}

// Formulas hooks
export function useFormulas(filters?: SearchFilters) {
  return useQuery({
    queryKey: [...tintometryKeys.formulas(), filters],
    queryFn: () => tintometryAPI.formulas.list(filters),
    staleTime: 5 * 60 * 1000
  });
}

export function useFormula(id: number) {
  return useQuery({
    queryKey: tintometryKeys.formula(id),
    queryFn: () => tintometryAPI.formulas.get(id),
    enabled: id > 0
  });
}

export function useCreateFormula() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (formula: Omit<FormulaTintometrica, 'id' | 'created_at' | 'updated_at'>) =>
      tintometryAPI.formulas.create(formula),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: tintometryKeys.formulas() });
    }
  });
}

export function useCalculateMixture() {
  return useMutation({
    mutationFn: (request: MisturaCalculationRequest) =>
      tintometryAPI.formulas.calculate(request)
  });
}

// Misturas hooks
export function useMisturas(filters?: SearchFilters) {
  return useQuery({
    queryKey: [...tintometryKeys.misturas(), filters],
    queryFn: () => tintometryAPI.misturas.list(filters),
    staleTime: 2 * 60 * 1000 // Fresh data for active operations
  });
}

export function useInfiniteMisturas(filters?: SearchFilters) {
  return useInfiniteQuery({
    queryKey: [...tintometryKeys.misturas(), 'infinite', filters],
    queryFn: ({ pageParam = 1 }) => 
      tintometryAPI.misturas.list({ ...filters, page: pageParam }),
    getNextPageParam: (lastPage) => {
      const hasNext = lastPage.next !== null;
      const currentPage = filters?.page || 1;
      return hasNext ? currentPage + 1 : undefined;
    },
    initialPageParam: 1
  });
}

export function useMistura(id: number) {
  return useQuery({
    queryKey: tintometryKeys.mistura(id),
    queryFn: () => tintometryAPI.misturas.get(id),
    enabled: id > 0,
    refetchInterval: (query) => {
      // Auto-refresh if mixture is in progress
      return query.state.data?.status === 'em_preparacao' ? 10000 : false; // 10 seconds
    }
  });
}

export function useCreateMistura() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (mistura: Omit<MisturaTinta, 'id' | 'created_at' | 'updated_at' | 'operador'>) =>
      tintometryAPI.misturas.create(mistura),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: tintometryKeys.misturas() });
      queryClient.invalidateQueries({ queryKey: tintometryKeys.dashboard() });
    }
  });
}

export function useStartMistura() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => tintometryAPI.misturas.start(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: tintometryKeys.mistura(id) });
      queryClient.invalidateQueries({ queryKey: tintometryKeys.misturas() });
    }
  });
}

export function useCompleteMistura() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, observacoes }: { id: number; observacoes?: string }) =>
      tintometryAPI.misturas.complete(id, observacoes),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: tintometryKeys.mistura(id) });
      queryClient.invalidateQueries({ queryKey: tintometryKeys.misturas() });
      queryClient.invalidateQueries({ queryKey: tintometryKeys.dashboard() });
    }
  });
}

// Estoque hooks
export function useEstoque(filters?: SearchFilters) {
  return useQuery({
    queryKey: [...tintometryKeys.estoque(), filters],
    queryFn: () => tintometryAPI.estoque.list(filters),
    staleTime: 2 * 60 * 1000
  });
}

export function useLowStock() {
  return useQuery({
    queryKey: [...tintometryKeys.estoque(), 'low'],
    queryFn: () => tintometryAPI.estoque.getLowStock(),
    staleTime: 1 * 60 * 1000, // 1 minute - critical data
    refetchInterval: 2 * 60 * 1000 // Check every 2 minutes
  });
}

export function useAddStock() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ pigmentoId, quantidade, observacoes }: {
      pigmentoId: number;
      quantidade: string;
      observacoes?: string;
    }) => tintometryAPI.estoque.addStock(pigmentoId, quantidade, observacoes),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: tintometryKeys.estoque() });
      queryClient.invalidateQueries({ queryKey: tintometryKeys.dashboard() });
    }
  });
}

// Etiquetas hooks
export function useEtiquetas(filters?: SearchFilters) {
  return useQuery({
    queryKey: [...tintometryKeys.etiquetas(), filters],
    queryFn: () => tintometryAPI.etiquetas.list(filters),
    staleTime: 5 * 60 * 1000
  });
}

export function useGenerateEtiqueta() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ misturaId, templateId }: { misturaId: number; templateId?: string }) =>
      tintometryAPI.etiquetas.generate(misturaId, templateId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: tintometryKeys.etiquetas() });
      queryClient.invalidateQueries({ queryKey: tintometryKeys.dashboard() });
    }
  });
}

export function usePrintEtiqueta() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => tintometryAPI.etiquetas.print(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: tintometryKeys.etiqueta(id) });
      queryClient.invalidateQueries({ queryKey: tintometryKeys.etiquetas() });
    }
  });
}

export function useEtiquetaPreview() {
  return useMutation({
    mutationFn: ({ misturaId, templateId }: { misturaId: number; templateId?: string }) =>
      tintometryAPI.etiquetas.getPreview(misturaId, templateId)
  });
}

// Color analysis hooks
export function useAnalyzeColor() {
  return useMutation({
    mutationFn: (request: ColorAnalysisRequest) =>
      tintometryAPI.colors.analyze(request)
  });
}

export function useFindSimilarColors() {
  return useMutation({
    mutationFn: ({ corHex, tolerancia }: { corHex: string; tolerancia?: number }) =>
      tintometryAPI.colors.findSimilar(corHex, tolerancia)
  });
}