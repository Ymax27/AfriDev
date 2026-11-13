import { useQuery } from "@tanstack/react-query";

import { countriesApi } from "@/services/api";

export function useCountries() {
  return useQuery({
    queryKey: ["countries"],
    queryFn: countriesApi.list,
    staleTime: 10 * 60_000,
  });
}
